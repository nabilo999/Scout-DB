"""Development fit: which players best fit a club's position?

Three machine-learning pieces score a player-club pair:

  blueprint  KNN match between the player's per-90 profile and the club's
             successful past players in that position (see blueprint.py).
  projected  Linear (ridge) regression: his predicted role score next season
             at that club, if he plays regularly. The shortlist is ranked by this.
  develop    Logistic regression: the chance he improves next season (higher
             role score and at least 900 minutes) at that club.

Both regressions are trained on every past player-season that was followed by
another Big Five season, and both take the blueprint match as an input. Club
features and blueprints only use what was known in the player's current season,
so nothing from the future leaks into training. Nearest historical lookalikes
(the same KNN method as nearest_neighbors.py) supply the evidence for each pick.
"""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, mean_absolute_error, r2_score, roc_auc_score
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .blueprint import Blueprints
from .teamfit import PLAYERS_FILE, ROLE_METRICS, STYLE_DIMS, TEAMS_FILE, club_stints, normalise

MIN_MINUTES_TRAIN = 900  # player-seasons used as training starting points
REGULAR_MINUTES = 900  # "regular minutes" next season
TEST_FROM_SEASON = "2022-23"  # transitions starting here or later are the test set

N_LOOKALIKES = 80
N_EVIDENCE = 20  # lookalikes whose next club was most like the target club

CLUB_COLS = [d + "_z" for d in STYLE_DIMS] + ["strength_z"]
ROLES = sorted(ROLE_METRICS)

PLAYER_FEATURES = ["age", "age_sq", "role_score", "minutes_k", "own_strength"] + ["role_" + r for r in ROLES]
CLUB_FEATURES = (["club_" + c for c in CLUB_COLS]
                 + ["gap_" + d for d in STYLE_DIMS]
                 + ["strength_gap", "changed_club",
                    "age_x_club_strength", "age_x_club_pressing", "score_x_strength_gap"])
BLUEPRINT_FEATURES = ["blueprint"]
FEATURES = PLAYER_FEATURES + CLUB_FEATURES + BLUEPRINT_FEATURES

# Building the training blueprints takes ~15 s, so the fitted model is cached
# and rebuilt whenever the data files or this package's code change.
CACHE_FILE = Path(__file__).resolve().parent / ".cache" / "development_model.pkl"
CACHE_INPUTS = [PLAYERS_FILE, TEAMS_FILE] + sorted(Path(__file__).resolve().parent.glob("*.py"))


def next_season(season):
    start = int(season[:4]) + 1
    return "%d-%02d" % (start, (start + 1) % 100)


# ---------------------------------------------------------------- tables

def player_seasons(players, teams):
    """One row per player per season: his biggest row that season, total
    minutes across leagues, his main club and that club's profile."""
    rows = players.sort_values("minutes").groupby(["understat_player_id", "season"]).tail(1).copy()
    totals = players.groupby(["understat_player_id", "season"])["minutes"].sum()
    rows["minutes_total"] = totals.reindex(pd.MultiIndex.from_frame(
        rows[["understat_player_id", "season"]])).to_numpy()
    # Mid-season movers: take the last club listed (where he finished the season).
    rows["club"] = rows["team"].str.split(",").str[-1].str.strip()
    rows["clubs_all"] = rows["team"].str.split(",").map(lambda ts: {t.strip() for t in ts})
    for metric in {m for metrics in ROLE_METRICS.values() for m in metrics}:
        rows[metric + "_p90"] = rows[metric] / (rows["minutes"].clip(lower=1) / 90)
    own = teams[["season", "team"] + CLUB_COLS].rename(
        columns={"team": "club", **{c: "own_" + c for c in CLUB_COLS}})
    return rows.merge(own, on=["season", "club"], how="left").reset_index(drop=True)


def transitions(seasons, teams):
    """Training examples: season t (the starting point) joined to season t+1."""
    start = seasons[(seasons["minutes_total"] >= MIN_MINUTES_TRAIN)
                    & seasons["role"].isin(ROLES) & seasons["role_score"].notna()].copy()
    start["next_season"] = start["season"].map(next_season)
    later = seasons[["understat_player_id", "season", "club", "minutes_total", "role_score"]].rename(
        columns={"season": "next_season", "club": "next_club",
                 "minutes_total": "next_minutes", "role_score": "next_role_score"})
    pairs = start.merge(later, on=["understat_player_id", "next_season"], how="inner")
    # The next club as it looked in season t; promoted clubs have no row and drop out.
    club_then = teams[["season", "team"] + CLUB_COLS].rename(columns={"team": "next_club"})
    pairs = pairs.merge(club_then, on=["season", "next_club"], how="inner")
    pairs = pairs.dropna(subset=["own_" + c for c in CLUB_COLS])
    pairs["improved"] = ((pairs["next_minutes"] >= REGULAR_MINUTES)
                         & (pairs["next_role_score"] > pairs["role_score"])).astype(int)
    pairs["changed_club"] = (pairs["next_club"] != pairs["club"]).astype(int)
    return pairs.reset_index(drop=True)


def features(pairs):
    """Feature matrix for player-club pairs. `pairs` needs the player's
    season-t columns, own_* club columns, the target club's CLUB_COLS,
    changed_club and blueprint."""
    X = pd.DataFrame(index=pairs.index)
    X["age"] = pairs["age_on_sep_1"].fillna(pairs["age_on_sep_1"].median())
    X["age_sq"] = X["age"] ** 2
    X["role_score"] = pairs["role_score"]
    X["minutes_k"] = pairs["minutes_total"] / 1000
    X["own_strength"] = pairs["own_strength_z"]
    for r in ROLES:
        X["role_" + r] = (pairs["role"] == r).astype(int)
    for c in CLUB_COLS:
        X["club_" + c] = pairs[c]
    for d in STYLE_DIMS:
        X["gap_" + d] = (pairs[d + "_z"] - pairs["own_" + d + "_z"]).abs()
    X["strength_gap"] = pairs["strength_z"] - pairs["own_strength_z"]
    X["changed_club"] = pairs["changed_club"]
    X["age_x_club_strength"] = X["age"] * pairs["strength_z"]
    X["age_x_club_pressing"] = X["age"] * pairs["pressing_z"]
    X["score_x_strength_gap"] = X["role_score"] * X["strength_gap"]
    X["blueprint"] = pairs["blueprint"].fillna(0)
    return X


def new_classifier():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))


def new_regressor():
    return make_pipeline(StandardScaler(), Ridge(alpha=1.0))


# ---------------------------------------------------------------- model

class DevelopmentModel:
    """Blueprint KNN, projected-score regression, development classifier,
    and a KNN lookalike index per role for evidence."""

    def __init__(self, players, teams):
        self.players = players
        self.teams = teams
        self.blueprints = Blueprints(players, teams)
        self.seasons = player_seasons(players, teams)
        self.pairs = transitions(self.seasons, teams)
        self.pairs["blueprint"] = self._training_blueprints()
        X = features(self.pairs)[FEATURES]
        self.classifier = new_classifier().fit(X, self.pairs["improved"])
        regular = self._regular()
        self.regressor = new_regressor().fit(X[regular], self.pairs.loc[regular, "next_role_score"])
        self._knn = {}

    @classmethod
    def cached(cls, players, teams):
        """Load the fitted model from disk if the data and code are unchanged."""
        key = [(str(f), f.stat().st_mtime, f.stat().st_size) for f in CACHE_INPUTS]
        try:
            with open(CACHE_FILE, "rb") as fh:
                saved_key, model = pickle.load(fh)
            if saved_key == key:
                return model
        except Exception:
            pass
        print("Training development model (first run, ~15 s)...", flush=True)
        model = cls(players, teams)
        try:
            CACHE_FILE.parent.mkdir(exist_ok=True)
            with open(CACHE_FILE, "wb") as fh:
                pickle.dump((key, model), fh)
        except OSError:
            pass
        return model

    def _regular(self):
        return (self.pairs["next_minutes"] >= REGULAR_MINUTES) & self.pairs["next_role_score"].notna()

    def _training_blueprints(self):
        """Match of each training player to his next club's blueprint, built
        from seasons up to his starting season only."""
        out = pd.Series(np.nan, index=self.pairs.index)
        for (club, role, season), group in self.pairs.groupby(["next_club", "role", "season"]):
            bp, _ = self.blueprints.build(club, role, season)
            out[group.index] = self.blueprints.match(group, bp, role)[0]
        return out

    # -- evaluation

    def evaluate(self):
        """Time-based check: train on early transitions, test on later ones.
        Each model is compared with smaller versions of itself (player only;
        player + club) to show what the club data and the blueprint add."""
        X, pairs = features(self.pairs), self.pairs
        train = pairs["season"] < TEST_FROM_SEASON
        test = ~train
        movers = test & (pairs["changed_club"] == 1)
        sets = {"player only": PLAYER_FEATURES,
                "player + club": PLAYER_FEATURES + CLUB_FEATURES,
                "player + club + blueprint": FEATURES}

        develop_rows = []
        y = pairs["improved"]
        fitted = {name: new_classifier().fit(X.loc[train, cols], y[train]) for name, cols in sets.items()}
        for subset, mask in [("all test transitions", test), ("club changers only", movers)]:
            for name, cols in sets.items():
                p = fitted[name].predict_proba(X.loc[mask, cols])[:, 1]
                develop_rows.append({"test set": subset, "features": name, "n": int(mask.sum()),
                                     "AUC": roc_auc_score(y[mask], p),
                                     "Brier": brier_score_loss(y[mask], p)})

        projected_rows = []
        regular = self._regular()
        y = pairs["next_role_score"]
        fitted = {name: new_regressor().fit(X.loc[train & regular, cols], y[train & regular])
                  for name, cols in sets.items()}
        for subset, mask in [("all test transitions", test & regular), ("club changers only", movers & regular)]:
            same = pairs.loc[mask, "role_score"]
            projected_rows.append({"test set": subset, "features": "same score as this season",
                                   "n": int(mask.sum()), "MAE": mean_absolute_error(y[mask], same),
                                   "R2": r2_score(y[mask], same)})
            for name, cols in sets.items():
                p = fitted[name].predict(X.loc[mask, cols])
                projected_rows.append({"test set": subset, "features": name, "n": int(mask.sum()),
                                       "MAE": mean_absolute_error(y[mask], p), "R2": r2_score(y[mask], p)})

        def coefs(model):
            s = pd.Series(model[-1].coef_.ravel(), index=FEATURES)
            return s.reindex(s.abs().sort_values(ascending=False).index)

        return {"n_train": int(train.sum()), "n_test": int(test.sum()),
                "develop": pd.DataFrame(develop_rows), "projected": pd.DataFrame(projected_rows),
                "develop_coefficients": coefs(self.classifier),
                "projected_coefficients": coefs(self.regressor)}

    # -- scoring

    def score(self, candidates, club_row, role):
        """Blueprint match, projected score and development chance of each
        candidate at club_row."""
        rows = candidates.copy()
        for c in CLUB_COLS:
            rows[c] = club_row[c]
        rows["changed_club"] = (~rows["clubs_all"].map(lambda cs: club_row["team"] in cs)).astype(int)
        bp, fallback = self.blueprints.build(club_row["team"], role, club_row["season"])
        rows["blueprint"], rows["plays_like"] = self.blueprints.match(rows, bp, role)
        X = features(rows)[FEATURES]
        rows["projected"] = self.regressor.predict(X)
        rows["develop"] = 100 * self.classifier.predict_proba(X)[:, 1]
        rows["blueprint"] = 100 * rows["blueprint"]
        return rows, self.blueprints.describe(bp, fallback, club_row["team"])

    # -- KNN evidence

    def _lookalike_index(self, role):
        if role not in self._knn:
            metrics = [m + "_p90" for m in ROLE_METRICS[role]] + ["age_on_sep_1", "minutes_total"]
            history = self.pairs[self.pairs["role"] == role].dropna(subset=metrics).reset_index(drop=True)
            scaler = StandardScaler().fit(history[metrics])
            knn = NearestNeighbors().fit(scaler.transform(history[metrics]))
            self._knn[role] = (metrics, history, scaler, knn)
        return self._knn[role]

    def lookalikes(self, candidate):
        """The closest historical transitions to this player-season, excluding
        his own seasons and anything that ends after his current season."""
        metrics, history, scaler, knn = self._lookalike_index(candidate["role"])
        if candidate[metrics].isna().any():
            return history.iloc[0:0]
        query = scaler.transform(candidate[metrics].to_frame().T.astype(float))
        k = min(len(history), N_LOOKALIKES * 3)
        _, idx = knn.kneighbors(query, n_neighbors=k)
        near = history.iloc[idx[0]]
        near = near[(near["understat_player_id"] != candidate["understat_player_id"])
                    & (near["next_season"] <= candidate["season"])]
        return near.head(N_LOOKALIKES)

    def evidence(self, near, club_row):
        """Of the lookalikes whose next club was most like this one, how many improved."""
        if near.empty:
            return "no lookalikes"
        target = np.array([club_row[c] for c in CLUB_COLS], dtype=float)
        dist = np.sqrt(((near[CLUB_COLS].to_numpy() - target) ** 2).sum(axis=1))
        similar = near.assign(club_distance=dist).nsmallest(N_EVIDENCE, "club_distance")
        improved = similar[similar["improved"] == 1]
        text = "%d of %d lookalikes at the most similar clubs improved" % (len(improved), len(similar))
        if not improved.empty:
            ex = improved.iloc[0]
            text += " (e.g. %s %s -> %s)" % (ex["player"], ex["season"], ex["next_club"])
        return text

    # -- the two directions

    def find_club(self, name, season):
        clubs = self.teams[self.teams["season"] == season]
        keys = clubs["team"].map(normalise)
        query = normalise(name)
        hits = clubs[keys == query]
        if hits.empty:
            hits = clubs[keys.str.contains(query, regex=False)]
        if hits.empty:
            raise ValueError("No club matches %r in %s" % (name, season))
        if len(hits) > 1:
            raise ValueError("Several clubs match %r, be more specific:\n%s"
                             % (name, "\n".join("  " + t for t in hits["team"])))
        return hits.iloc[0]

    def shortlist(self, club, role, season=None):
        """Players in `role` from other clubs, ranked by projected role score
        next season at `club`. Returns (club row, blueprint description, table)."""
        if role not in ROLE_METRICS:
            raise ValueError("No role score for %r; choose one of %s" % (role, ", ".join(ROLES)))
        season = season or self.teams["season"].max()
        club_row = self.find_club(club, season)
        candidates = self.seasons[(self.seasons["season"] == season) & (self.seasons["role"] == role)
                                  & (self.seasons["minutes_total"] >= MIN_MINUTES_TRAIN)
                                  & self.seasons["role_score"].notna()
                                  & self.seasons["own_strength_z"].notna()]
        candidates = candidates[~candidates["clubs_all"].map(lambda cs: club_row["team"] in cs)]
        scored, blueprint_text = self.score(candidates, club_row, role)
        scored["vs_current"] = scored["projected"] - self.best_current(club_row, role)
        scored = scored.sort_values("projected", ascending=False).reset_index(drop=True)
        scored["evidence"] = [self.evidence(self.lookalikes(c), club_row) for _, c in scored.iterrows()]
        out = scored.drop(columns="minutes").rename(
            columns={"team": "current_club", "age_on_sep_1": "age", "minutes_total": "minutes"})
        columns = ["player", "current_club", "league", "age", "minutes", "role_score",
                   "projected", "vs_current", "develop", "blueprint", "plays_like", "evidence"]
        return club_row, blueprint_text, out[columns]

    def best_current(self, club_row, role):
        """Highest role score among the club's regulars (900+ minutes) in this role."""
        season_players = self.players[(self.players["season"] == club_row["season"])
                                      & (self.players["role"] == role)]
        stints = club_stints(season_players)
        regulars = stints[(stints["team"] == club_row["team"]) & (stints["club_minutes"] >= REGULAR_MINUTES)]
        return regulars["role_score"].max() if not regulars.empty else np.nan

    def club_ranking(self, player_id, season=None):
        """Every club in the player's season, ranked by his projected score there."""
        rows = self.seasons[self.seasons["understat_player_id"] == player_id]
        if season is not None:
            rows = rows[rows["season"] <= season]
        if rows.empty:
            raise ValueError("Player has no seasons up to %s" % season)
        player = rows.sort_values("season").iloc[-1]
        if player["role"] not in ROLE_METRICS or pd.isna(player["role_score"]):
            raise ValueError("%s has no role score (%s), so there is nothing to predict"
                             % (player["player"], player["tm_sub_position"]))
        clubs = self.teams[self.teams["season"] == player["season"]]
        one = pd.DataFrame([player])
        near = self.lookalikes(player)
        out = []
        for _, club_row in clubs.iterrows():
            if club_row["team"] in player["clubs_all"]:
                continue
            scored, _ = self.score(one, club_row, player["role"])
            r = scored.iloc[0]
            out.append({"team": club_row["team"], "league": club_row["league"],
                        "projected": r["projected"], "develop": r["develop"],
                        "blueprint": r["blueprint"], "plays_like": r["plays_like"],
                        "evidence": self.evidence(near, club_row)})
        return pd.DataFrame(out).sort_values("projected", ascending=False).reset_index(drop=True)
