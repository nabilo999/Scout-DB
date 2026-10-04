# Scout DB

ScoutIQ is a football scouting decision-support prototype. It helps a recruitment team answer three related questions about a player:

1. **Current ability:** What does the player contribute now, relative to players in the same role?
2. **Potential:** Which past players had similar profiles at a similar age, and how did those players develop afterward?
3. **Team fit:** How closely does the player's profile match the style and needs of a selected team?

The project turns season statistics into explainable comparisons and shortlists. It is intended to support scouts and analysts, not to make transfer decisions on their behalf. Scores should show the evidence and assumptions behind them.

## Product idea

A user selects or searches for a player. ScoutIQ presents a position-aware view of the player's recent production, usage and areas of strength. The user can then see historical player comparisons and select a club to review the player's fit with that club's profile.

The three parts share one player-performance foundation, but answer different questions:

| Part | Question | Main inputs | Intended output |
|---|---|---|---|
| Current ability | How strong is the player's recent on-field contribution? | Latest completed season's minutes, production, passing, creation, defending and role | A transparent, position-aware profile and baseline score |
| Historical similarity and potential | What happened to comparable players after a similar season? | Earlier player-seasons, age, position, minutes and performance features, followed by later seasons | Comparable historical players, their subsequent development and an evidence-based potential estimate |
| Team fit | Which clubs' playing profiles appear compatible with this player? | Big Five player-season data aggregated by club, plus 2024–25 match results and available match statistics | Team-style profiles, fit comparisons and a shortlist of clubs to investigate |

The shared sequence is:

```text
Season source data
       |
       v
Validated player-season records and features
       |----------------------|
       v                      v
Current ability       Historical similarity
                              |
                              v
                         Potential

Validated 2024–25 team inputs --> Team profiles --> Team fit
                                             player profile --^
```

## How the three parts work

### Current ability

The current-ability view describes performance in the latest completed season available in this data snapshot, 2024–25. It uses playing time and role-relevant measures such as goals, assists, expected goals, chance creation, passing, ball progression, tackles, interceptions, blocks and clearances.

Raw totals reward players who play more minutes, so the feature pipeline will include per-90 rates and playing-time context. Comparisons should be made within useful role groups and, when appropriate, within league-season groups. The first score will be a documented baseline with visible components, minimum-minute handling and missing-data rules. It will not be presented as an objective or universal measure of talent.

### Historical similarity and potential

Historical similarity starts from a player's season profile, age and position. It finds comparable player-seasons in the earlier seasons, then follows those players into later seasons to measure what happened after the comparison point.

Potential is a forward-looking estimate built from those historical outcomes. The team must define the outcome before training or scoring—for example, change in a role-specific per-90 profile, sustained playing time, or both. The model must only use information available at the historical comparison date. Later seasons must never leak into the similarity inputs for that comparison.

The 2024–25 players can be compared to earlier historical cases, but the current files do not contain their 2025–26 outcomes. Those outcomes cannot be claimed as observed evidence in this version.

### Team fit

Team fit builds a profile for each club in the five leagues using the completed 2024–25 season. Player-season statistics can be grouped by club to describe passing, chance creation, progression and defensive activity. Match records add wins, draws, losses, goals, shots and other available match statistics.

The team profile is compared with a player's role-specific profile. The result should explain which available dimensions match and where they differ. This is a statistical compatibility screen, not proof that a player will succeed in a coach's system. The current sources do not contain a consistent pressure count or verified possession percentage, so ScoutIQ must not label tackles as pressing or infer possession from touches.

## Current data sources

The second version of ScoutIQ's data: 12 consistent seasons, **2014-15 through 2025-26**, for the Big Five leagues (EPL, La Liga, Bundesliga, Serie A, Ligue 1). 

## Column dictionary

### `merged/players/players_<season>.csv` (43 columns)

One row per player per league per season. Understat columns first, then Transfermarkt (`tm_` and biometric columns), then merge diagnostics.

| Column | Source | Meaning |
| --- | --- | --- |
| `understat_player_id` | Understat | Understat player id. Stable across seasons and clubs. |
| `player` | Understat | Player name as Understat spells it. |
| `league` | Understat | `EPL`, `ESP`, `GER`, `ITA` or `FRA`. |
| `season` | Understat | Season label, e.g. `2024-25`. |
| `team` | Understat | Club; two clubs comma-separated if the player moved within the league mid-season. |
| `position_understat` | Understat | Every position the player was used in this season: `GK`, `D` (defender), `M` (midfielder), `F` (forward), `S` (appeared as substitute). E.g. `F M S`. |
| `games` | Understat | League appearances. |
| `minutes` | Understat | League minutes played (includes added time). |
| `goals` | Understat | League goals, penalties included. |
| `non_penalty_goals` | Understat | Goals excluding penalties. |
| `assists` | Understat | Assists. |
| `shots` | Understat | Shots attempted. |
| `key_passes` | Understat | Passes that led directly to a shot. |
| `xg` | Understat | Expected goals: summed probability that the player's shots become goals. |
| `npxg` | Understat | Expected goals excluding penalties. |
| `xa` | Understat | Expected assists: xG of the shots the player's passes created. |
| `xg_chain` | Understat | Total xG of every possession that ended in a shot and that the player was involved in. Measures overall attacking involvement. |
| `xg_buildup` | Understat | `xg_chain` excluding the possessions where the player took the shot or made the key pass. Measures build-up involvement; useful for deep midfielders and defenders. |
| `yellow_cards` | Understat | Yellow cards. |
| `red_cards` | Understat | Red cards. |
| `tm_player_id` | Transfermarkt | Transfermarkt player id. Stable; joins to `player_league_history.csv` and the raw Transfermarkt tables. Blank if unlinked. |
| `tm_name` | Transfermarkt | Player name as Transfermarkt spells it. |
| `date_of_birth` | Transfermarkt | Full date of birth (`YYYY-MM-DD`). |
| `age_on_sep_1` | Derived | Age in years on 1 September of the season's first year, to two decimals. |
| `height_cm` | Transfermarkt | Height in centimetres (current listing, not per season). |
| `foot` | Transfermarkt | Preferred foot: `right`, `left` or `both`. |
| `tm_position` | Transfermarkt | Broad position: `Goalkeeper`, `Defender`, `Midfield`, `Attack`. |
| `tm_sub_position` | Transfermarkt | Detailed position, e.g. `Centre-Back`, `Left-Back`, `Defensive Midfield`, `Right Winger`, `Centre-Forward`. |
| `citizenship` | Transfermarkt | Country of citizenship. |
| `country_of_birth` | Transfermarkt | Country of birth. |
| `tm_league_games` | Transfermarkt | League matches with at least one minute played, this league and season. Blank where Transfermarkt's appearance rows are missing. |
| `tm_league_minutes` | Transfermarkt | League minutes (each match capped at 90). |
| `tm_league_goals` | Transfermarkt | League goals; a cross-check on `goals`. |
| `tm_league_assists` | Transfermarkt | League assists by Transfermarkt's definition, which is looser than Understat's: equal in 86% of rows, higher in 12%. |
| `tm_club_ids` | Transfermarkt | Transfermarkt club id(s) the player played for in this league-season. |
| `tm_club_names` | Transfermarkt | The matching club names. |
| `tm_all_competition_minutes` | Transfermarkt | Minutes across every competition Transfermarkt tracks that season: league, domestic cups, Champions League, Europa League, Conference League and qualifiers. Workload context. |
| `market_value_start_eur` | Transfermarkt | Latest market value on or before 1 September of the season (euros). |
| `market_value_end_eur` | Transfermarkt | Latest market value on or before 1 July after the season (euros). |
| `match_score` | Merge | Combined name/minutes/goals score for the link (0–1). Blank for fallback links. |
| `match_name_similarity` | Merge | Name similarity between the two spellings (0–1). |
| `match_minutes_similarity` | Merge | 1 minus the relative minutes difference (0–1). |
| `match_method` | Merge | How the link was made: `same_club` (normal), `league_wide`, `understat_id_carryover`, `valuation_club_name` or `manual`. |

### `merged/teams/teams_<season>.csv` (41 columns)

One row per club per season, built from Understat's per-match records. Ratios are recomputed from season totals, not averaged across matches.

| Column | Meaning |
| --- | --- |
| `league`, `season` | League code and season label. |
| `understat_team_id` | Understat club id. |
| `team` | Club name as Understat spells it (matches `team` in the player files). |
| `tm_club_id` | Transfermarkt club id. |
| `matches` | League matches played. |
| `wins`, `draws`, `losses`, `points` | Season record. |
| `goals_for`, `goals_against` | Goals scored and conceded. |
| `xg_for`, `xg_against` | Expected goals created and conceded. |
| `npxg_for`, `npxg_against` | The same without penalties. |
| `expected_points` | Points the team "should" have earned given its xG and xGA in each match. |
| `deep_completions_for` | Passes completed within an estimated 20 yards of the opponent's goal, excluding crosses. Measures territorial pressure. |
| `deep_completions_against` | Deep completions allowed. |
| `ppda_passes` | Passes the opponents made in their own build-up area (the numerator of PPDA). |
| `ppda_def_actions` | Defensive actions (tackles, interceptions, challenges, fouls) the team made in the opponents' half (the denominator). |
| `ppda` | **Passes allowed per defensive action**: `ppda_passes / ppda_def_actions`. Lower = more intense pressing. 2024-25 range: about 6.5 (Barcelona) to 17 (St. Pauli). |
| `ppda_allowed_passes`, `ppda_allowed_def_actions`, `ppda_allowed` | The same measured on opponents pressing this team. Low = this team gets pressed hard, often because it builds up from the back. |
| `*_per_match` | Points, goals, xG, npxG, deep completions and expected points divided by `matches`. |
| `xg_share` | `xg_for / (xg_for + xg_against)`: share of the chance quality in the team's matches. A dominance measure. |
| `deep_completion_share` | Share of deep completions in the team's matches. A territory measure. |
| `most_used_formation` | Formation Transfermarkt recorded most often, e.g. `4-2-3-1`, `3-4-3`. |
| `most_used_formation_share` | Share of matches played in that formation (0–1). |
| `managers` | Manager(s) during the season, in order, separated by `|`. |
| `manager_count` | Number of managers that season. |
