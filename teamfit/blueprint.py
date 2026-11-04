"""Club blueprints: what success in a position has looked like at a club.

A club's blueprint for a role is every season in which a player in that role
was successful there (1,500+ minutes at the club and a role score of +0.5 or
more). Seasons count more when they are recent, when the club played then
like it plays now, and when the player's role score was higher. If the club
has fewer than 5 such seasons, successful seasons from the clubs most similar
in style are added at half weight until there are enough.

A player's blueprint match is a KNN-style comparison of his per-90 profile
(the role metrics' z-scores) with every blueprint season.
"""

import numpy as np
import pandas as pd

from .teamfit import ROLE_METRICS, STYLE_DIMS, club_stints

SUCCESS_MINUTES = 1500
SUCCESS_SCORE = 0.5
MIN_BLUEPRINT_SEASONS = 5
FALLBACK_WEIGHT = 0.5
MAX_FALLBACK_CLUBS = 10
RECENCY = 0.8  # weight multiplier per season back

STYLE_COLS = [d + "_z" for d in STYLE_DIMS]
CLUB_COLS = STYLE_COLS + ["strength_z"]


class Blueprints:
    def __init__(self, players, teams):
        stints = club_stints(players[players["role"].isin(ROLE_METRICS)])
        success = stints[(stints["club_minutes"] >= SUCCESS_MINUTES)
                         & (stints["role_score"] >= SUCCESS_SCORE)]
        style_then = teams[["season", "team"] + STYLE_COLS]
        self.success = success.merge(style_then, on=["season", "team"], how="inner").reset_index(drop=True)
        self.by_club_role = {key: rows for key, rows in self.success.groupby(["team", "role"])}
        self.teams = teams
        self.club_profile = teams.set_index(["season", "team"])[CLUB_COLS]
        self._cache = {}

    def build(self, club, role, season):
        """Blueprint seasons for (club, role) using seasons up to `season`.
        Returns (rows with a `weight` column, list of fallback clubs used)."""
        key = (club, role, season)
        if key in self._cache:
            return self._cache[key]
        now = self.club_profile.loc[(season, club)]

        def successes(team):
            rows = self.by_club_role.get((team, role))
            return None if rows is None else rows[rows["season"] <= season]

        own = successes(club)
        parts = [] if own is None or own.empty else [own.assign(source_weight=1.0)]
        count = sum(len(p) for p in parts)
        fallback = []
        if count < MIN_BLUEPRINT_SEASONS:
            others = self.club_profile.loc[season].drop(index=club)
            dist = np.sqrt(((others - now) ** 2).sum(axis=1)).sort_values()
            for team in dist.index[:MAX_FALLBACK_CLUBS]:
                rows = successes(team)
                if rows is None or rows.empty:
                    continue
                parts.append(rows.assign(source_weight=FALLBACK_WEIGHT))
                fallback.append(team)
                count += len(rows)
                if count >= MIN_BLUEPRINT_SEASONS:
                    break
        if not parts:
            result = (self.success.iloc[0:0].assign(weight=[]), fallback)
            self._cache[key] = result
            return result

        bp = pd.concat(parts, ignore_index=True)
        years_back = int(season[:4]) - bp["season_start"]
        style_gap = np.sqrt(((bp[STYLE_COLS].to_numpy() - now[STYLE_COLS].to_numpy()) ** 2).sum(axis=1))
        bp["weight"] = (bp["source_weight"] * RECENCY ** years_back
                        * np.exp(-style_gap ** 2 / 4) * bp["role_score"])
        self._cache[key] = (bp, fallback)
        return bp, fallback

    @staticmethod
    def match(candidates, bp, role):
        """Blueprint match (0-1) and closest blueprint season for each candidate.
        A candidate's own seasons are never part of his blueprint."""
        n = len(candidates)
        if bp.empty:
            return np.full(n, np.nan), [None] * n
        cols = ["z_" + m for m in ROLE_METRICS[role]]
        C = candidates[cols].fillna(0).to_numpy(dtype=float)
        B = bp[cols].fillna(0).to_numpy(dtype=float)
        rms = np.sqrt(((C[:, None, :] - B[None, :, :]) ** 2).mean(axis=2))
        sim = np.exp(-rms ** 2 / 2)
        own = candidates["understat_player_id"].to_numpy()[:, None] == bp["understat_player_id"].to_numpy()[None, :]
        w = np.where(own, 0.0, bp["weight"].to_numpy()[None, :])
        total = w.sum(axis=1)
        score = np.where(total > 0, (w * sim).sum(axis=1) / np.where(total > 0, total, 1), np.nan)
        closest = np.where(own, -1, sim).argmax(axis=1)
        labels = ["%s %s (%s)" % (bp["player"].iat[i], bp["season"].iat[i], bp["team"].iat[i])
                  if total[r] > 0 else None for r, i in enumerate(closest)]
        return score, labels

    def describe(self, bp, fallback, club):
        if bp.empty:
            return "no successful seasons at %s or similar clubs" % club
        own = bp[bp["team"] == club]
        names = own["player"].value_counts()
        text = "%d successful season(s) at %s" % (len(own), club)
        if not names.empty:
            text += " (" + ", ".join("%s x%d" % (p, c) if c > 1 else p for p, c in names.head(5).items()) + ")"
        if fallback:
            text += " + %d from similar clubs: %s" % (len(bp) - len(own), ", ".join(fallback))
        return text
