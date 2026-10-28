"""Team fit: which Big Five clubs suit a player's profile?

For a player and a target season, every club gets a fit score built from four
explainable components (each 0-100):

  style      How close the club's playing style is to the styles of the teams
             the player has recently played in (pressing, pressure faced,
             territory, openness).
  need       Share of the club's minutes in the player's role that went to
             players with a lower role score than him. High = he would be an
             upgrade on most of the incumbents.
  formation  Whether the club's usual formation has a natural slot for his
             position, and whether he has played in that back-line shape.
  level      How close the club's strength (xG share) is to the level he has
             been playing and producing at.

This is a statistical compatibility screen, not a prediction of success.
"""

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PLAYERS_FILE = ROOT / "players" / "players_allYears.csv"
TEAMS_FILE = ROOT / "teams" / "teams_allYears.csv"

WEIGHTS = {"style": 0.40, "need": 0.30, "formation": 0.15, "level": 0.15}

# Style dimensions, oriented so that higher = more of the named trait.
# Each is z-scored within its season so seasons can be compared.
STYLE_DIMS = {
    "pressing": "how hard the team presses (inverse PPDA)",
    "pressure_faced": "how hard opponents press them (inverse PPDA allowed)",
    "territory": "share of deep completions in their matches",
    "openness": "total xG in their matches (for + against)",
}

# How far back the player's style history goes, and how fast older seasons fade.
HISTORY_SEASONS = 3
SEASON_DECAY = 0.6

MIN_MINUTES_REFERENCE = 450  # minimum minutes to be part of a role's z-score reference
MIN_ROLE_MINUTES = 900  # below this a club "barely uses" the role and need is neutral

ROLE_OF_SUB_POSITION = {
    "Goalkeeper": "GK",
    "Centre-Back": "CB",
    "Left-Back": "FB",
    "Right-Back": "FB",
    "Defensive Midfield": "DM",
    "Central Midfield": "CM",
    "Attacking Midfield": "AM",
    "Left Winger": "W",
    "Right Winger": "W",
    "Left Midfield": "W",
    "Right Midfield": "W",
    "Centre-Forward": "ST",
    "Second Striker": "ST",
}

ROLE_NAMES = {
    "GK": "goalkeeper", "CB": "centre-back", "FB": "full-back", "DM": "defensive midfielder",
    "CM": "central midfielder", "AM": "attacking midfielder", "W": "winger", "ST": "striker",
}

# Per-90 metrics and weights that make up each role's score. The data has no
# tackles, passing accuracy or saves, so CB scores only cover build-up and GK
# has no score at all.
ROLE_METRICS = {
    "ST": {"npxg": 0.35, "non_penalty_goals": 0.15, "shots": 0.15, "xa": 0.15, "xg_chain": 0.20},
    "W": {"npxg": 0.25, "xa": 0.25, "key_passes": 0.20, "xg_chain": 0.20, "non_penalty_goals": 0.10},
    "AM": {"xa": 0.30, "key_passes": 0.25, "xg_chain": 0.25, "npxg": 0.20},
    "CM": {"xg_buildup": 0.35, "xg_chain": 0.25, "xa": 0.20, "key_passes": 0.20},
    "DM": {"xg_buildup": 0.60, "xg_chain": 0.20, "key_passes": 0.20},
    "FB": {"xa": 0.30, "xg_buildup": 0.30, "key_passes": 0.25, "xg_chain": 0.15},
    "CB": {"xg_buildup": 0.70, "xg_chain": 0.30},
}


# ---------------------------------------------------------------- loading

def load_teams(path=TEAMS_FILE):
    teams = pd.read_csv(path)
    teams["pressing"] = -teams["ppda"]
    teams["pressure_faced"] = -teams["ppda_allowed"]
    teams["territory"] = teams["deep_completion_share"]
    teams["openness"] = (teams["xg_for"] + teams["xg_against"]) / teams["matches"]
    teams["strength"] = teams["xg_share"]
    for col in list(STYLE_DIMS) + ["strength"]:
        by_season = teams.groupby("season")[col]
        teams[col + "_z"] = (teams[col] - by_season.transform("mean")) / by_season.transform("std")
    teams["back_line"] = teams["most_used_formation"].map(back_line)
    return teams


def load_players(path=PLAYERS_FILE):
    players = pd.read_csv(path)
    players["role"] = players["tm_sub_position"].map(ROLE_OF_SUB_POSITION)
    players["season_start"] = players["season"].str[:4].astype(int)
    players = add_role_scores(players)
    return players


def add_role_scores(players):
    """z-score each role metric per 90 within role and season, then combine."""
    players = players.copy()
    players["role_score"] = np.nan
    per90 = players["minutes"].clip(lower=1) / 90
    for role, metrics in ROLE_METRICS.items():
        in_role = players["role"] == role
        score = pd.Series(0.0, index=players.index[in_role])
        for metric, weight in metrics.items():
            rate = players.loc[in_role, metric] / per90[in_role]
            ref = rate[players.loc[in_role, "minutes"] >= MIN_MINUTES_REFERENCE]
            seasons = players.loc[in_role, "season"]
            mean = ref.groupby(seasons[ref.index]).mean().reindex(seasons).to_numpy()
            std = ref.groupby(seasons[ref.index]).std().reindex(seasons).to_numpy()
            score += weight * ((rate - mean) / std).clip(-3, 3)
        players.loc[in_role, "role_score"] = score
    return players


def club_stints(players):
    """One row per (player-season, club). Mid-season movers are split evenly
    between the clubs because the data only gives the season total."""
    stints = players.assign(team=players["team"].str.split(",")).explode("team")
    stints["team"] = stints["team"].str.strip()
    clubs_per_row = stints.groupby(level=0)["team"].transform("size")
    stints["club_minutes"] = stints["minutes"] / clubs_per_row
    return stints.reset_index(drop=True)


# ---------------------------------------------------------------- formations

def back_line(formation):
    if not isinstance(formation, str) or not formation[:1].isdigit():
        return np.nan
    return int(formation[0])


def strikers(formation):
    if not isinstance(formation, str):
        return np.nan
    if "Diamond" in formation:
        return 2
    lines = [int(c) for c in formation.split()[0].split("-")]
    return lines[-1]


def role_slot(role, sub_position, formation):
    """0-1: how naturally the formation accommodates this role."""
    if not isinstance(formation, str):
        return 0.5
    shape = formation.split()[0]
    back = back_line(formation)
    up_front = strikers(formation)
    has_wingers = shape in {"4-2-3-1", "4-3-3", "4-1-4-1", "3-4-3", "4-4-1-1", "4-4-2", "5-4-1"}
    has_ten = shape in {"4-2-3-1", "3-4-2-1", "4-3-1-2", "3-4-1-2", "4-3-2-1", "4-1-3-2", "4-4-1-1"} \
        or "Diamond" in formation

    if role == "W":
        if has_wingers:
            # 4-4-2 / 5-4-1 wide players are midfielders more than wingers
            return 0.8 if shape in {"4-4-2", "5-4-1", "4-4-1-1"} else 1.0
        return 0.4  # wing-back systems with two strikers or two tens
    if role == "FB":
        return 1.0 if back == 4 else 0.7  # becomes a wing-back
    if role == "AM":
        return 1.0 if has_ten else 0.6
    if role == "ST":
        if sub_position == "Second Striker":
            return 1.0 if up_front >= 2 or has_ten else 0.6
        return 1.0
    if role == "DM":
        return 0.8 if shape == "4-4-2" and "double 6" not in formation else 1.0
    return 1.0  # CB, CM, GK fit every shape


# ---------------------------------------------------------------- player context

def normalise(text):
    text = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def find_player(players, name=None, player_id=None):
    """Return the understat_player_id for a name search (or validate an id)."""
    if player_id is not None:
        if player_id not in set(players["understat_player_id"]):
            raise ValueError("No player with understat_player_id %s" % player_id)
        return player_id
    query = normalise(name)
    names = players[["understat_player_id", "player"]].drop_duplicates()
    names = names.assign(key=names["player"].map(normalise))
    exact = names[names["key"] == query]
    hits = exact if not exact.empty else names[names["key"].str.contains(query, regex=False)]
    ids = hits["understat_player_id"].unique()
    if len(ids) == 0:
        raise ValueError("No player matches %r" % name)
    if len(ids) > 1:
        options = (players[players["understat_player_id"].isin(ids)]
                   .sort_values("season").groupby("understat_player_id").last())
        listing = "\n".join("  --id %d  %s (%s, %s)" % (pid, r["player"], r["team"], r["season"])
                            for pid, r in options.iterrows())
        raise ValueError("Several players match %r, pick one:\n%s" % (name, listing))
    return int(ids[0])


def player_context(player_id, players, teams, season=None):
    """Summarise the player at a reference season: role, form and the
    minutes-weighted style of the clubs he has recently played for."""
    rows = players[players["understat_player_id"] == player_id]
    if season is not None:
        rows = rows[rows["season"] <= season]
    if rows.empty:
        raise ValueError("Player has no seasons up to %s" % season)
    ref_season = rows["season"].max()
    current = rows[rows["season"] == ref_season].sort_values("minutes").iloc[-1]
    known_roles = rows.dropna(subset=["role"]).sort_values("season")
    if known_roles.empty:
        raise ValueError("Player %s has no Transfermarkt position" % current["player"])
    latest_role = known_roles.iloc[-1]

    ref_start = int(ref_season[:4])
    history = club_stints(rows[rows["season_start"] > ref_start - HISTORY_SEASONS])
    history = history.merge(teams, on=["league", "season", "team"], how="inner")
    history["weight"] = history["club_minutes"] * SEASON_DECAY ** (ref_start - history["season_start"])
    if history["weight"].sum() == 0:
        history["weight"] = 1.0
    w = history["weight"] / history["weight"].sum()

    style = {dim: float((history[dim + "_z"] * w).sum()) for dim in STYLE_DIMS}
    back_lines = history.groupby("back_line")["weight"].sum() / history["weight"].sum()
    strength_played = float((history["strength_z"] * w).sum())

    seasons_with_score = rows[(rows["role"] == latest_role["role"]) & (rows["minutes"] >= MIN_MINUTES_REFERENCE)]
    role_score = (seasons_with_score.sort_values("season")["role_score"].iloc[-1]
                  if not seasons_with_score.empty else current["role_score"])

    return {
        "player_id": player_id,
        "player": current["player"],
        "season": ref_season,
        "clubs": sorted(set(club_stints(rows[rows["season"] == ref_season])["team"])),
        "league": current["league"],
        "age": current["age_on_sep_1"],
        "minutes": int(rows.loc[rows["season"] == ref_season, "minutes"].sum()),
        "role": latest_role["role"],
        "sub_position": latest_role["tm_sub_position"],
        "role_score": None if pd.isna(role_score) else float(role_score),
        "style": style,
        "back_line_share": back_lines.to_dict(),
        "strength_played": strength_played,
        "history": history[["season", "team", "club_minutes"]].drop_duplicates(),
    }


# ---------------------------------------------------------------- scoring

def style_scores(ctx, clubs):
    player = np.array([ctx["style"][d] for d in STYLE_DIMS])
    club = clubs[[d + "_z" for d in STYLE_DIMS]].to_numpy()
    dist = np.sqrt(((club - player) ** 2).sum(axis=1))
    return 100 * np.exp(-dist ** 2 / 8)  # dist 0 -> 100, 2 -> 61, 4 -> 14


def need_scores(ctx, clubs, players):
    """Share of each club's role minutes played by lower-scoring players.
    Clubs that barely use the role get a neutral 50; formation covers that."""
    if ctx["role"] not in ROLE_METRICS or ctx["role_score"] is None:
        return pd.Series(np.nan, index=clubs.index)
    season_players = players[(players["season"] == clubs["season"].iloc[0])
                             & (players["role"] == ctx["role"])
                             & (players["understat_player_id"] != ctx["player_id"])]
    stints = club_stints(season_players)
    stints["below"] = stints["role_score"] < ctx["role_score"]
    stints["below_minutes"] = stints["club_minutes"] * stints["below"]
    per_club = stints.groupby(["league", "team"])[["below_minutes", "club_minutes"]].sum()
    role_minutes = per_club["club_minutes"].where(per_club["club_minutes"] >= MIN_ROLE_MINUTES)
    share = per_club["below_minutes"] / role_minutes
    keys = pd.MultiIndex.from_frame(clubs[["league", "team"]])
    return pd.Series(100 * share.reindex(keys).fillna(0.5).to_numpy(), index=clubs.index)


def formation_scores(ctx, clubs):
    slot = clubs["most_used_formation"].map(lambda f: role_slot(ctx["role"], ctx["sub_position"], f))
    familiar = clubs["back_line"].map(lambda b: ctx["back_line_share"].get(b, 0.0))
    return 100 * (0.6 * slot + 0.4 * familiar)


def player_level(ctx):
    """Club strength (z) the player looks suited to: where he has played,
    nudged up or down by how well he produces for his role."""
    nudge = 0.0 if ctx["role_score"] is None else 0.5 * np.clip(ctx["role_score"], -2, 2)
    return ctx["strength_played"] + nudge


def level_scores(ctx, clubs):
    gap = clubs["strength_z"] - player_level(ctx)
    return 100 * np.exp(-gap ** 2 / 2), gap


def explain(row, ctx):
    notes = []
    gaps = {d: row[d + "_z"] - ctx["style"][d] for d in STYLE_DIMS}
    close = [d for d, g in gaps.items() if abs(g) < 0.5]
    far = max(gaps, key=lambda d: abs(gaps[d]))
    if close:
        notes.append("similar " + ", ".join(d.replace("_", " ") for d in close))
    if abs(gaps[far]) >= 1:
        notes.append("%s %s than he is used to" % (
            far.replace("_", " "), "much higher" if gaps[far] > 0 else "much lower"))
    if not pd.isna(row["need"]):
        notes.append("outscores players with %d%% of their %s minutes"
                     % (round(row["need"]), ROLE_NAMES[ctx["role"]]))
    gap = row["level_gap"]
    notes.append("step up" if gap > 0.75 else "step down" if gap < -0.75 else "similar level")
    return "; ".join(notes)


def rank_clubs(player_id, players, teams, season=None, target_season=None,
               leagues=None, include_current=False):
    ctx = player_context(player_id, players, teams, season)
    target_season = target_season or ctx["season"]
    clubs = teams[teams["season"] == target_season].copy()
    if clubs.empty:
        raise ValueError("No team data for season %s" % target_season)
    if leagues:
        clubs = clubs[clubs["league"].isin(leagues)]
    if not include_current:
        clubs = clubs[~clubs["team"].isin(ctx["clubs"])]

    clubs["style"] = style_scores(ctx, clubs)
    clubs["need"] = need_scores(ctx, clubs, players)
    clubs["formation"] = formation_scores(ctx, clubs)
    clubs["level"], clubs["level_gap"] = level_scores(ctx, clubs)

    # If need can't be measured (goalkeepers, unscored players) spread its weight.
    weights = dict(WEIGHTS)
    if clubs["need"].isna().all():
        weights.pop("need")
    total = sum(weights.values())
    clubs["fit"] = sum(clubs[c] * w for c, w in weights.items()) / total

    clubs["why"] = clubs.apply(lambda r: explain(r, ctx), axis=1)
    clubs = clubs.sort_values("fit", ascending=False)
    columns = ["team", "league", "fit", "style", "need", "formation", "level",
               "most_used_formation", "managers", "why"]
    return ctx, clubs[columns].reset_index(drop=True)


def team_styles(teams, season=None):
    """Readable style table for one season (or all), for export."""
    out = teams if season is None else teams[teams["season"] == season]
    cols = ["league", "season", "team", "ppda", "ppda_allowed", "deep_completion_share",
            "xg_share", "most_used_formation"] + [d + "_z" for d in STYLE_DIMS] + ["strength_z"]
    return out[cols].round(3)
