# Team fit

Two questions, both answered from `players/players_allYears.csv` and `teams/teams_allYears.csv`:

1. **Which players best fit this club?** A ranked shortlist for one club and position, ranked by a regression model's projected score at that club, with the club's blueprint of successful past players, a development chance and KNN lookalikes as evidence (see [Development model](#development-model)).
2. **Which clubs best fit this player?** Every Big Five club ranked by a rule-based style score (see [The fit score](#the-fit-score)), optionally with the machine-learning columns added.

```bash
python3 -m teamfit --club Arsenal --role W                         # shortlist of wingers for Arsenal
python3 -m teamfit --club "Como" --role ST --top 20 --csv como.csv
python3 -m teamfit "Bukayo Saka"                                   # clubs for a player, style fit
python3 -m teamfit "Bukayo Saka" --development                     # ... ranked by projected score
python3 -m teamfit "Florian Wirtz" --season 2024-25 --leagues EPL ESP --top 5
python3 -m teamfit --evaluate                                      # test the models
python3 -m teamfit --team-styles team_styles.csv --target-season 2025-26
```

Roles for `--club`: `CB FB DM CM AM W ST`. Needs Python 3.9+ with pandas, numpy and scikit-learn (`pip install -r requirements.txt`). If a name matches several players or clubs, the tool lists the options.

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


## Development model

`development.py` and `blueprint.py` score a **player–club pair** with three machine-learning pieces:

| Column | Question | Model |
|---|---|---|
| `blueprint`, `plays_like` | Does he play like players who succeeded at this club? | KNN-style match with the club's blueprint |
| `projected` | How good will he be there next season? | Ridge (linear) regression of next season's role score |
| `develop` | Will he develop there? | Logistic regression: chance his role score goes up and he plays 900+ minutes |

The shortlist is ranked by `projected`.

### Club blueprint

- **Successful season:** 1,500+ minutes at the club in that position, with a role score of +0.5 or more. For example, Tottenham's strikers are Harry Kane ×8 and Richarlison.
- **Weighting:** each season is multiplied by 0.8 per year back, by how closely the club's style then matches its style now, and by the player's role score.
- **Fallback:** if the club has fewer than 5 successful seasons in the position, successful seasons from the clubs most similar in style and strength are added at half weight until there are 5. The shortlist header says when this happened, for example "Como + 9 from similar clubs: Roma".
- **Match:** the candidate's per-90 profile (the z-scores behind his role score) is compared with every blueprint season. `blueprint` (0–100) is the weighted average similarity, and `plays_like` is the closest season. A player's own seasons are never part of his blueprint.

### Training

- **Data:** every player-season with 900+ minutes in a scored role that was followed by another Big Five season (about 13,000 *transitions*).
- **`projected`** is trained on the transitions where he played 900+ minutes next season. It predicts how good he will be *if he plays regularly*.
- **No look-ahead:** club features, and the blueprint of the club he played for next, use only what was known in his starting season. Players who left the Big Five are not included, because there is no club to learn from.
- **Features:** player (age, age², role score, minutes, role, current club strength); target club (pressing, pressure faced, territory, openness, strength); the style and strength gaps between the two; a new-club flag; a few combinations such as age × club strength; and the blueprint match.

### Evaluation (`--evaluate`)

Trained on transitions before 2022-23, tested on 2022-23 onwards. **MAE** is the average error in role-score points (lower is better), and **R²** is the share of variation explained (higher is better).

| Club changers only | MAE | R² | develop AUC |
|---|---|---|---|
| Same score as this season | 0.631 | 0.088 | |
| Player only | 0.593 | 0.211 | 0.625 |
| Player + club | 0.504 | 0.445 | 0.686 |
| Player + club + blueprint | 0.502 | 0.448 | 0.688 |

- **Club data matters a lot for players who change club.** It doubles the explained variation, from 0.211 to 0.445.
- **The blueprint adds very little on top**: +0.003 R² and +0.002 AUC. It correlates 0.62 with current role score, so most of what it says (he plays like a successful player) the model already knows. A style-only version, which compares the shape of the profile rather than its level, added nothing either. In this data, players like past successful ones are not better predicted to succeed at that club than the player and club numbers already suggest. The blueprint stays in as an explanation for scouts ("plays like Kane 2017-18"), not as a source of accuracy.
- **Projections shrink towards average.** An elite player's projected score is well below his current one (Kane 2.6 → 0.4 at Tottenham), because historically very high seasons tend not to repeat. Compare `projected` values with each other, not with current role scores.

### Shortlist (`--club X --role R`)

The shortlist covers every player in that role with 900+ minutes in the latest season, excluding the club's own players. Each player gets:

- `projected`, `develop`, `blueprint` and `plays_like`;
- `vs_current`: his projected score minus the best current role score among the club's regulars in that position;
- `evidence`: from the 80 historical player-seasons closest to his per-90 profile, age and minutes (the same KNN idea as `nearest_neighbors.py`), how many of the 20 whose next club was most like this one improved.

**Player → clubs** (`"Name" --development`) adds `projected`, `develop`, `blueprint`, `plays_like` and `evidence` to the club ranking and sorts by `projected`. The rule-based score is shown as `style_fit`.

The fitted model is cached in `teamfit/.cache/`. It is rebuilt automatically (about 15 s) when the data files or the code change.

## Limits

- The data has no tackles, passing accuracy or saves. Centre-back scores cover build-up only, and goalkeepers get no `need` score (its weight is shared out over the other components).
- A player who moved clubs mid-season has his minutes split evenly between both clubs.
- Positions come from Transfermarkt's single listed sub-position, not from where he actually played each match.
- The development model finds correlations, not causes. Players are not assigned to clubs at random: good players join good clubs. It shows which kinds of moves have tended to go well, not what a club will do for a player.
- An R² of about 0.45 and an AUC of about 0.69 are useful signals but far from certain. Treat the scores as ranking aids, not numbers to quote.
- Club blueprints rely on club history in the Big Five since 2014-15. Recently promoted clubs mostly use the fallback, and long-serving stars (Kane at Tottenham) dominate their club's blueprint.
- Some rows in the player files appear twice (same player, league and season, differing only in the `match_*` columns). `load_players()` keeps one of each.
- This is a compatibility screen for shortlisting, not a prediction that a player will succeed in a coach's system.
