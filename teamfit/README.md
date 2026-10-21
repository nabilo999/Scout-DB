# Team fit

Ranks every Big Five club by how well it suits one player, and says why. It uses only `players/players_allYears.csv` and `teams/teams_allYears.csv`.

```bash
python3 -m teamfit "Bukayo Saka"                                  # latest season, all clubs
python3 -m teamfit "Florian Wirtz" --season 2024-25 --leagues EPL ESP --top 5
python3 -m teamfit --id 833 --csv vvd_fit.csv                     # full ranking to CSV
python3 -m teamfit --team-styles team_styles.csv --target-season 2025-26
```

Needs Python 3.9+ with pandas and numpy. If a name matches several players, the tool lists their `--id` values.

## The fit score

`fit` is a weighted average of four 0–100 components. The weights are in `WEIGHTS` in `teamfit.py`.

| Component | Weight | Question | How |
|---|---|---|---|
| `style` | 0.40 | Does the club play like the teams he has recently played in? | Club style vector compared with the minutes-weighted style of his clubs over the last 3 seasons (older seasons × 0.6 per year). Distance d gives `100·exp(−d²/8)`. |
| `need` | 0.30 | Would he improve their options in his role? | Share of the club's minutes in his role that went to players with a lower role score. Clubs with under 900 minutes in the role get a neutral 50. |
| `formation` | 0.15 | Is there a natural slot for him? | 60% slot fit (for example, a winger in a 3-5-2 scores 0.4) and 40% his experience with that back-line shape (3, 4 or 5 at the back). |
| `level` | 0.15 | Is the club roughly his level? | Club strength (xG share, z) compared with the strength of the clubs he has played for, adjusted by ±0.5·role score. The `why` column labels it *step up*, *similar level* or *step down*. |

**Style dimensions** are z-scored within each season, so a 2018 club and a 2025 club can be compared:

- `pressing`: −PPDA (higher = presses harder)
- `pressure_faced`: −PPDA allowed (higher = opponents press them harder)
- `territory`: deep-completion share
- `openness`: xG for + xG against per match

Dominance (xG share) is left out of style. It correlates 0.9 with territory and measures quality more than style, so it is used for `level` instead.

**Role score** is a weighted sum of per-90 z-scores within the player's role and season, using players with 450+ minutes as the reference. The metrics for each role are in `ROLE_METRICS`.

## Limits

- The data has no tackles, passing accuracy or saves. Centre-back scores cover build-up only, and goalkeepers get no `need` score (its weight is shared out over the other components).
- A player who moved clubs mid-season has his minutes split evenly between both clubs.
- Positions come from Transfermarkt's single listed sub-position, not from where he actually played each match.
- This is a compatibility screen for shortlisting, not a prediction that a player will succeed in a coach's system.
