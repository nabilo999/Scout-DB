"""Find historical players with profiles similar to a named player."""

from pathlib import Path
import html
import json
import unicodedata

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


DATA_DIR = Path(__file__).parent / "players"

ATTACK_FEATURES = [
    "age_on_sep_1",
    "minutes",
    "height_cm",
    "goalsPer90",
    "xgPer90",
    "shotsPer90",
    "shot_quality",
    "finishing_expected",
    "attacking_involvement",
    "non_penalty_goals_per90",
    "share_team_attack",
    "assistsPer90",
    "xAPer90",
    "key_passes_Per90",
]

# Height is left out for midfielders: the data has no aerial or physical stats for
# them, so it matched players by build rather than by how they play. A backtest on
# 2022-23 to 2024-25 (with 20 neighbours) gave the lowest next-season error without
# it. Minutes stays: matching on playing time helps predict next season's minutes.
MIDFIELD_FEATURES = [
    "age_on_sep_1",
    "minutes",
    "buildup_involvement",
    "key_passes_Per90",
    "xAPer90",
    "share_team_buildup",
    "chance_quality",
    "shotsPer90",
    "xgPer90",
    "attacking_involvement",
]

# Always part of the next-season outlook, even when not used for similarity.
OUTCOME_EXTRA = ["minutes"]


def plain_name(name):
    """Lower-case name without accents or HTML codes (e.g. "O&#039;Neil" -> "o'neil")."""
    name = unicodedata.normalize("NFKD", html.unescape(str(name)))
    return "".join(c for c in name if not unicodedata.combining(c)).casefold().strip()


def load_player_tables():
    attack = pd.read_csv(DATA_DIR / "players_attack.csv")
    midfield = pd.read_csv(DATA_DIR / "players_midfield.csv")
    # Players who switched league mid-season appear twice per league in the files; keep one.
    key = ["understat_player_id", "season", "league"]
    return attack.drop_duplicates(key), midfield.drop_duplicates(key)


def find_player_rows(attack, midfield, player_name=None, player_id=None):
    """All rows for one player, matched by exact name.

    The Understat spelling is tried first ("Kylian Mbappe-Lottin"), then the
    Transfermarkt spelling ("Kylian Mbappé"), then either spelling ignoring
    accents and case ("kylian mbappe"). Partial names are not matched. If the
    name belongs to more than one player, the options are listed so the
    caller can pass player_id instead.
    """
    rows = pd.concat([attack, midfield], ignore_index=True)
    if player_id is not None:
        found = rows[rows["understat_player_id"] == player_id]
    else:
        name = str(player_name).strip().casefold()
        if not name:
            raise ValueError("Give a player name (it can't be blank)")
        found = rows[rows["player"].str.casefold() == name]
        if found.empty:
            found = rows[rows["tm_name"].fillna("").str.casefold() == name]
        if found.empty:
            plain = plain_name(player_name)
            found = rows[(rows["player"].map(plain_name) == plain)
                         | (rows["tm_name"].fillna("").map(plain_name) == plain)]
    if found.empty:
        raise ValueError(f"Player not found: {player_name if player_id is None else player_id}")

    ids = found["understat_player_id"].unique()
    if len(ids) > 1:
        latest = found.sort_values("season").groupby("understat_player_id").last()
        options = "; ".join(
            f"player_id={pid}: {row['player']} ({row['team']}, {row['season']})"
            for pid, row in latest.iterrows()
        )
        raise ValueError(f"Several players are called {player_name}, pick one: {options}")
    return found.sort_values("season")


def check_latest_season(matches, min_minutes=450):
    """(latest season, its minutes, latest season with min_minutes+ or None, its minutes)."""
    minutes = matches.drop_duplicates(["season", "league"]).groupby("season")["minutes"].sum()
    enough = minutes[minutes >= min_minutes]
    return (
        minutes.index[-1], int(minutes.iloc[-1]),
        enough.index[-1] if not enough.empty else None,
        int(enough.iloc[-1]) if not enough.empty else None,
    )


def find_similar_players(
    player_name, n_neighbors=20, min_minutes=450, show_graph=True, return_report=False,
    use_regular_season=False, player_id=None, n_shown=5,
):
    """Print and return the closest earlier player-seasons and their average outlook.

    The latest season found for the player is used as the current profile.
    If it has fewer than min_minutes, a warning is printed (and returned in
    the report); use_regular_season=True uses his latest season with enough
    minutes instead. Candidates must be from the same detailed position and
    an earlier season.

    The next-season outlook averages the n_neighbors closest players (20: a
    backtest showed 5 was too noisy, worse than assuming no change for
    midfielders). Tables, the graph and the report show the closest n_shown.

    Examples:
        find_similar_players("Erling Haaland")  # attacker data
        find_similar_players("David Silva")     # midfielder data
        find_similar_players("Sergio Agüero", use_regular_season=True)
    """
    attack, midfield = load_player_tables()
    matches = find_player_rows(attack, midfield, player_name, player_id)

    # Small samples make per-90 numbers unreliable: warn, or switch season if asked.
    latest, latest_minutes, regular, regular_minutes = check_latest_season(matches, min_minutes)
    query_season, warning = latest, None
    if latest_minutes < min_minutes:
        who = matches.iloc[-1]["player"]
        small = f"{who} played only {latest_minutes} minutes in {latest} (under {min_minutes})"
        if regular is None:
            warning = f"{small} and has no season with {min_minutes}+ minutes, so these matches are unreliable."
        elif use_regular_season:
            query_season = regular
            warning = (f"Using {regular} ({regular_minutes} min), his latest season with "
                       f"{min_minutes}+ minutes, because {small}.")
        else:
            warning = (f"{small}, so these matches are unreliable. His latest season with "
                       f"{min_minutes}+ minutes is {regular} ({regular_minutes} min); "
                       f"use use_regular_season=True to compare that season instead.")
        print(f"\nWARNING: {warning}")

    current = matches[matches["season"] == query_season].sort_values("minutes").iloc[-1]
    source = attack if current["tm_position"] == "Attack" else midfield
    features = ATTACK_FEATURES if current["tm_position"] == "Attack" else MIDFIELD_FEATURES

    # Use the most recent row in the proper position table as the query profile.
    current_rows = source[
        (source["understat_player_id"] == current["understat_player_id"])
        & (source["season"] == current["season"])
    ]
    if current_rows.empty:
        current_rows = pd.DataFrame([current])
    current = current_rows.sort_values("season").iloc[-1]

    candidates = source[
        (source["tm_sub_position"] == current["tm_sub_position"])
        & (source["season"] < current["season"])
        & (source["minutes"] >= min_minutes)
    ].copy()

    if candidates.empty:
        raise ValueError("No earlier players found for this position and minute limit.")

    # Exclude the selected player's own earlier seasons when an ID is available.
    if pd.notna(current["tm_player_id"]):
        candidates = candidates[
            candidates["tm_player_id"] != current["tm_player_id"]
        ]
    if pd.notna(current["understat_player_id"]):
        candidates = candidates[
            candidates["understat_player_id"] != current["understat_player_id"]
        ]

    # Keep an ID for each player so repeat seasons can be removed after ranking.
    candidates["player_key"] = candidates["tm_player_id"].fillna(
        candidates["understat_player_id"].astype(str)
    )
    candidates["player_key"] = candidates["player_key"].astype(str)
    if candidates.empty:
        raise ValueError("No other players found for this position and minute limit.")

    # Impute missing values and scale features so large units do not dominate distance.
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    history = imputer.fit_transform(candidates[features])
    history = scaler.fit_transform(history)
    query = scaler.transform(imputer.transform(current[features].to_frame().T))

    model = NearestNeighbors(n_neighbors=len(candidates))
    model.fit(history)
    distances, indexes = model.kneighbors(query)

    ranked = candidates.iloc[indexes[0]].copy()
    ranked["distance"] = distances[0]
    ranked = ranked.sort_values("distance").drop_duplicates("player_key").reset_index(drop=True)
    results = ranked.head(n_neighbors).copy()  # used for the next-season outlook
    closest = ranked.head(n_shown).copy()  # shown in tables, the graph and the report
    columns = list(dict.fromkeys(
        ["player", "season", "team", "tm_sub_position", "minutes", *features, "distance"]
    ))
    results_table = closest[columns].reset_index(drop=True)

    print(f"\nClosest historical matches for {current['player']} ({current['season']}):")
    print(results_table.to_string(index=False))

    # Show the five closest players in red and the next ten in yellow.
    shown = ranked.head(n_shown + 10).copy()
    shown["label"] = shown["player"] + " (" + shown["season"] + ")"
    shown = shown.iloc[::-1]
    colors = ["red" if rank < n_shown else "gold"
              for rank in range(len(shown) - 1, -1, -1)]

    figure, axis = plt.subplots(figsize=(10, max(5, len(shown) * 0.38)))
    bars = axis.barh(shown["label"], shown["distance"], color=colors, edgecolor="black")
    axis.axvline(0, color="green", linestyle="--", linewidth=1.5,
                 label=f"{current['player']} reference (distance 0)")
    axis.set_title(f"Historical neighbors of {current['player']} ({current['season']})")
    axis.set_xlabel("KNN distance from selected player's profile (lower is closer)")
    axis.set_ylabel("Historical player-season")
    axis.grid(axis="x", alpha=0.25)
    axis.bar_label(bars, fmt="%.2f", padding=4, fontsize=8)
    axis.legend(handles=[
        Patch(facecolor="red", edgecolor="black", label=f"Closest {min(n_shown, len(shown))}"),
        Patch(facecolor="gold", edgecolor="black", label="Next 10"),
        Line2D([0], [0], color="green", linestyle="--",
               label=f"{current['player']} reference (distance 0)"),
    ], loc="upper left", bbox_to_anchor=(1.02, 1))
    figure.tight_layout(rect=(0, 0, 0.76, 1))
    graph_path = Path(__file__).parent / "player_similarity.png"
    figure.savefig(graph_path, dpi=160)
    print(f"\nSaved similarity graph to: {graph_path}")

    # Follow each comparable player into the next season and average observed stats.
    outcome_features = OUTCOME_EXTRA + [
        feature for feature in features
        if feature not in ("age_on_sep_1", "height_cm", *OUTCOME_EXTRA)
    ]
    outcomes = []
    for _, neighbor in results.iterrows():
        start_year = int(neighbor["season"][:4])
        next_season = f"{start_year + 1}-{(start_year + 2) % 100:02d}"
        next_rows = source[source["season"] == next_season]

        if pd.notna(neighbor["tm_player_id"]):
            next_rows = next_rows[next_rows["tm_player_id"] == neighbor["tm_player_id"]]
        if next_rows.empty and pd.notna(neighbor["understat_player_id"]):
            next_rows = next_rows[
                next_rows["understat_player_id"] == neighbor["understat_player_id"]
            ]

        if not next_rows.empty:
            # If a player has multiple league rows, use the row with the most minutes.
            next_row = next_rows.sort_values("minutes", ascending=False).iloc[0]
            outcomes.append(
                {
                    "player": neighbor["player"],
                    "from_season": neighbor["season"],
                    "next_season": next_season,
                    **{feature: next_row[feature] for feature in outcome_features},
                }
            )

    average = None
    outcome_table = pd.DataFrame()
    if outcomes:
        outcome_table = pd.DataFrame(outcomes)
        print(f"\nObserved next-season outcomes ({len(outcomes)} of {len(results)} matches):")
        print(outcome_table.to_string(index=False))
        average = outcome_table[outcome_features].mean().rename("average_prediction")
        print("\nSimple average prediction from observed follow-ups:")
        print(average.to_frame().round(3).to_string())
    else:
        print("\nNo matched players had an observed next-season row in these files.")

    if show_graph:
        plt.show()
    else:
        plt.close(figure)

    if return_report:
        prediction = None
        if average is not None:
            prediction = json.loads(average.to_frame().T.to_json(orient="records"))[0]
        current_stats = {
            field: current[field]
            for field in outcome_features
            if pd.notna(current[field])
        }
        current_stats = json.loads(pd.Series(current_stats).to_json())
        return {
            "player": current["player"],
            "season": current["season"],
            "position": current["tm_sub_position"],
            "current_stats": current_stats,
            "matches": json.loads(results_table.to_json(orient="records")),
            "outcomes": json.loads(outcome_table.to_json(orient="records")),
            "prediction": prediction,
            "prediction_coverage": f"{len(outcome_table)} of {len(results)}",
            "warning": warning,
        }
    return results_table



if __name__ == "__main__":
    name = input("Player name: ")
    attack, midfield = load_player_tables()
    rows = find_player_rows(attack, midfield, name)
    latest, minutes, regular, regular_minutes = check_latest_season(rows)
    switch = False
    if minutes < 450 and regular is not None:
        print(f"{rows.iloc[-1]['player']}'s latest season ({latest}) has only {minutes} minutes, which is too few to rely on.")
        answer = input(f"Use {regular} ({regular_minutes} min) instead? [y/N] ")
        switch = answer.strip().lower().startswith("y")
    find_similar_players(name, use_regular_season=switch)
