# Frontend attribute data audit

Based on the CSV headers in this checkout. The current backend uses `players/players_attack.csv` and `players/players_midfield.csv`; their underlying season files and `players_allYears.csv` have the same 43 base columns. The scored variants add model features, not additional observations of player skills. Existing frontend ratings are illustrative fixtures.

Goalkeeping attributes have been removed from all three frontend player fixtures. The remaining groups are Physical, Mental and Technical (28 attributes). This does not remove goalkeeper player records from the source datasets.

## 1. Have directly in the current data: none

None of the 28 displayed attributes has a direct measurement column in the active player files. We do have inputs for some performance proxies below.

## 2. Can derive useful performance proxies: 3

These are candidates for future scores, not implemented ratings or direct observations of the named skills.

| Group | Attribute | Available inputs and possible score |
|---|---|---|
| Technical | Finishing | `non_penalty_goals`, `npxg`, `minutes`: non-penalty goals above expected per 90. Require enough minutes and shots; small samples are noisy. |
| Mental | Attack Position | `npxg`, `shots`, `minutes`: non-penalty xG per 90 as a chance-getting proxy, with shot volume as context. Measures attacking opportunities, not tracked positioning or movement. |
| Mental | Vision | `xa`, `key_passes`, `minutes`: expected assists and key passes per 90 as a chance-creation proxy. Measures observed creation, not a player's ability to see every available pass. |

Exact formulas and any weighting still need to be chosen. For shot conversion or xG per shot, the active data has all shots but no non-penalty shot count; do not silently mix non-penalty goals/xG with an all-shots denominator.

## 3. Do not have enough evidence to score as named: 25

| Group | Missing attributes |
|---|---|
| Physical (8) | Acceleration; Sprint Speed; Agility; Balance; Jumping; Stamina; Strength; Reactions. |
| Mental (2) | Aggression; Interceptions. |
| Technical (15) | Ball Control; Crossing; Dribbling; FK Acc.; Heading Acc.; Long Passing; Short Passing; Marking; Shot Power; Long Shots; Stand Tackle; Sliding Tackle; Volleys; Curve; Penalties. |

- Stamina: minutes and games can describe workload/usage, not endurance. Height does not establish jumping or strength.
- Aggression: `yellow_cards` and `red_cards` can describe discipline, not establish aggression or pressing intensity.
- Penalties: `goals - non_penalty_goals` gives penalty goals scored. There is no penalty-attempt or miss column, so conversion accuracy cannot be calculated. Zero penalty goals does not mean poor penalty ability.
- Heading accuracy and dribbling: no supporting columns in either the active player files or the archived player-performance files.

## Archived data: additional options, not connected to the current backend

`Old data (not needed, dont remove)/big5_player_performance/big5_player_stats_<year>_<year>.csv` contains these columns across the archived 2015-16 through 2024-25 files:

| Attribute | Archived columns | Limit |
|---|---|---|
| Interceptions | `interceptions` | Direct event count; can derive per-90 output. |
| Short Passing | `passes_completed_short`, `passes_short`, `passes_pct_short` | Completion accuracy and volume; pass difficulty is not controlled for. |
| Long Passing | `passes_completed_long`, `passes_long`, `passes_pct_long` | Completion accuracy and volume; pass difficulty is not controlled for. |
| Penalties | `pens_made`, `pens_att` | Conversion rate where attempts are nonzero, with sample size shown. |
| General tackling | `tackles`, `tackles_won`, `challenge_tackles_pct` | Could support a general tackling score, but cannot split standing and sliding tackles. |
| Crossing activity | `crosses_into_penalty_area` | Completed crosses into the box only; not total crossing attempts or crossing accuracy. |

Using these requires a separate join with player identities, clubs and seasons reconciled and row-level coverage checked. The archived files have not been modified or connected.

When scoring is implemented: calculate supported raw scores first, then percentiles within an appropriate position/season comparison group. Handle low samples and missing data explicitly. A percentile cannot supply evidence for an unmeasured attribute.
