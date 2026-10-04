# ScoutIQ features, in plain language

A short version of `FEATURES.md`. Each feature has a name, what it tells a scout, and the columns it comes from. Column meanings are in `README.md`.

**One rule for everything:** compare players fairly by using **per 90 minutes**. A striker with 10 goals in 900 minutes is better than one with 10 goals in 3,000 minutes. Per 90 = `stat ÷ minutes × 90`.

**Only compare like with like:** forwards with forwards and defenders with defenders. Use the `tm_sub_position` column to group players.

---

## 1. Current ability: how good is he right now?

Uses the latest season's player file.

| Feature | What it tells you | Columns |
|---|---|---|
| Goals per 90 | How often he scores | `goals`, `minutes` |
| Expected goals (xG) per 90 | How many good chances he gets, whether or not he scores them | `npxg`, `minutes` |
| Shots per 90 | How often he shoots | `shots`, `minutes` |
| Shot quality | Does he take good shots or hopeful ones? (xG ÷ shots) | `npxg`, `shots` |
| Assists per 90 | How often he sets up goals | `assists`, `minutes` |
| Expected assists (xA) per 90 | How good the chances he creates are | `xa`, `minutes` |
| Key passes per 90 | How often his pass leads to a shot | `key_passes`, `minutes` |
| Attacking involvement | How often he is part of a move that ends in a shot | `xg_chain`, `minutes` |
| Build-up involvement | Same, but only the earlier passes in the move. Good for midfielders and defenders | `xg_buildup`, `minutes` |
| Availability | How much of the season he actually played | `minutes`, team `matches` |

**Gap to know about:** this data has no tackles, passing accuracy or goalkeeper saves. The ratings work well for attackers but are weak for centre-backs and keepers. The team still has to decide how to handle that.

---

## 2. Potential: where will he be in a season or two?

Uses all 12 seasons. We look at players who were like him in the past and see what happened to them next.

**What we know about him now:**

| Feature | What it tells you | Columns |
|---|---|---|
| Age | Young players usually improve; players past about 30 usually decline | `age_on_sep_1` |
| Height, preferred foot | Physical profile | `height_cm`, `foot` |
| Position | Players in different roles develop differently | `tm_sub_position` |
| League | Some leagues are harder than others | `league` |
| Team strength | Being good in a top team differs from being good in a weak one | team `points_per_match` |
| Recent form trend | Is his output going up or down compared with last season? | last season's file vs this season's |
| Playing-time trend | Is he playing more or less than last season? | `minutes` in both seasons |
| Market value trend | Does the market rate him higher or lower than a year ago? | `market_value_start_eur`, `market_value_end_eur` |
| Experience | How many seasons he has already played at this level | count of past player files he appears in |

**What we want to predict (the answer):**

1. **Does he stay at this level?** Is he still a regular in the Big Five next season, or has he dropped down a level, moved abroad or retired?
2. **Does he get better or worse?** Compare his per-90 numbers next season with this season's.

---

## 3. Team fit: does he suit this club?

Uses the team files.

**What each club looks like:**

| Feature | What it tells you | Columns |
|---|---|---|
| Pressing intensity | How hard the team presses to win the ball back. Lower PPDA = more pressing | `ppda` |
| Pressure faced | How hard opponents press this team | `ppda_allowed` |
| Territory | How much of the game is played near the opponent's goal | `deep_completion_share` |
| Dominance | Who creates the better chances in this team's games | `xg_share` |
| Attacking output | How many good chances they create | `xg_for_per_match` |
| Defensive solidity | How few good chances they allow | `xg_against_per_match` |
| Formation | Back three or back four, one striker or two | `most_used_formation` |

**What the player brings:**

| Feature | What it tells you | Columns |
|---|---|---|
| His share of the team's output | Is he the main threat in his team, or a supporting player? | his `xg_chain` vs team `xg_for` |
| Styles of his past teams | Has he already played in a pressing team, or a team that keeps the ball? | his `team` each season → that team's row |

**The fit idea:** a player whose past teams played like the target club should find it easier to settle in. The fit score shows how close those styles are, and whether he would be the main threat or a supporting player at the new club.

---

## How the three parts come together

```
Current ability ─┐
Potential ───────┼──► Recommendation: should this club go for this player?
Team fit ────────┘
```
