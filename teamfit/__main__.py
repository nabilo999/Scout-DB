"""Team fit: which players best fit a club, and which clubs best fit a player.

    python3 -m teamfit --club Arsenal --role W                  # shortlist for a club
    python3 -m teamfit --club "Como" --role ST --top 20 --csv como_st.csv
    python3 -m teamfit "Bukayo Saka"                            # clubs for a player (style fit)
    python3 -m teamfit "Bukayo Saka" --development              # ... ML view: upgrade clubs first, by projected score
    python3 -m teamfit "Florian Wirtz" --season 2024-25 --leagues EPL ESP --top 5
    python3 -m teamfit "Sergio Aguero" --regular-season       # skip a latest season under 900 min
    python3 -m teamfit --evaluate                               # test the development model
    python3 -m teamfit --team-styles team_styles_2025-26.csv --target-season 2025-26

Roles for --club: CB FB DM CM AM W ST (goalkeepers have no role score).
"""

import argparse
import sys

import pandas as pd

from . import teamfit
from .development import DevelopmentModel, upgrade_order


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m teamfit", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("player", nargs="?", help="player name (accents and case ignored)")
    parser.add_argument("--id", type=int, help="understat_player_id, if the name is ambiguous")
    parser.add_argument("--club", help="club to build a player shortlist for (needs --role)")
    parser.add_argument("--role", choices=sorted(teamfit.ROLE_METRICS), help="position for --club")
    parser.add_argument("--development", action="store_true", help="add the ML columns (projected, develop, blueprint) to a player's club ranking")
    parser.add_argument("--evaluate", action="store_true", help="test the development model and exit")
    parser.add_argument("--season", help="player's reference season, e.g. 2024-25 (default: his latest); "
                                         "with --club, the season of the shortlist (default: latest)")
    parser.add_argument("--regular-season", action="store_true",
                        help="if the player's latest season has under 900 minutes, use his latest season "
                             "with 900+ minutes instead")
    parser.add_argument("--target-season", help="season of club profiles to compare against (default: reference season)")
    parser.add_argument("--leagues", nargs="+", choices=["EPL", "ESP", "GER", "ITA", "FRA"])
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--include-current", action="store_true", help="keep the player's own club(s) in the ranking")
    parser.add_argument("--csv", help="write the full ranking to this file")
    parser.add_argument("--team-styles", metavar="CSV", help="export club style profiles and exit")
    args = parser.parse_args(argv)

    teams = teamfit.load_teams()
    if args.team_styles:
        teamfit.team_styles(teams, args.target_season).to_csv(args.team_styles, index=False)
        print("Wrote %s" % args.team_styles)
        return 0
    if args.club and not args.role:
        parser.error("--club needs --role")
    if not (args.player or args.id is not None or args.club or args.evaluate):
        parser.error("give a player name, --id, --club or --evaluate")

    players = teamfit.load_players()
    try:
        if args.evaluate:
            return evaluate(DevelopmentModel.cached(players, teams))
        if args.club:
            return club_shortlist(DevelopmentModel.cached(players, teams), args)
        return player_clubs(players, teams, args)
    except ValueError as err:
        print(err, file=sys.stderr)
        return 1


def evaluate(model):
    result = model.evaluate()
    print("Trained on %d transitions before 2022-23, tested on %d from 2022-23 on."
          % (result["n_train"], result["n_test"]))
    print("\nprojected: ridge regression of next season's role score (players with 900+ minutes next season)")
    print("MAE = average error in role-score points (lower is better); R2 = share of variation explained\n")
    print(result["projected"].round(3).to_string(index=False))
    print("\ndevelop: logistic regression, label = role score up next season and 900+ minutes\n")
    print(result["develop"].round(3).to_string(index=False))
    for name in ["projected", "develop"]:
        print("\nLargest %s coefficients (standardised features, trained on all transitions):" % name)
        print(result[name + "_coefficients"].head(10).round(3).to_string())
    return 0


def club_shortlist(model, args):
    club, blueprint, ranking = model.shortlist(args.club, args.role, args.season)
    if args.leagues:
        ranking = ranking[ranking["league"].isin(args.leagues)]
    role = teamfit.ROLE_NAMES[args.role]
    print("%s (%s, %s) | %s | shortlist: %s"
          % (club["team"], club["league"], club["season"], club["most_used_formation"], role))
    print("Blueprint: " + blueprint)
    print("projected = predicted role score next season at %s | vs_current = projected minus their best "
          "current %s | develop = chance (%%) he improves there | blueprint = match (0-100) with "
          "their successful past %ss\n" % (club["team"], role, role))
    show(ranking, args)
    return 0


def player_clubs(players, teams, args):
    player_id = teamfit.find_player(players, args.player, args.id)
    season = minutes_check(players, player_id, args)
    ctx, ranking = teamfit.rank_clubs(player_id, players, teams, season,
                                      args.target_season, args.leagues, args.include_current)
    if args.development:
        dev = DevelopmentModel.cached(players, teams).club_ranking(player_id, ctx["season"], args.target_season)
        ranking = (ranking.drop(columns="why").rename(columns={"fit": "style_fit"})
                   .merge(dev, on=["team", "league"], how="inner"))
        ranking = upgrade_order(ranking)
        print("Clubs where he would be an upgrade (vs_current > 0: his projected score beats their best current "
              "%s) come first, ranked by projected score; then the rest, ranked by vs_current. "
              "Blank vs_current = the club has no regular in that role.\n"
              % teamfit.ROLE_NAMES.get(ctx["role"], "player"))

    score = "n/a" if ctx["role_score"] is None else "%+.2f" % ctx["role_score"]
    print("%s | %s %s | %s (%s) | %d min | role score %s"
          % (ctx["player"], ctx["season"], ", ".join(ctx["clubs"]), ctx["sub_position"],
             ctx["role"], ctx["minutes"], score))
    print("Style of recent clubs (z): " + ", ".join(
        "%s %+.2f" % (d, v) for d, v in ctx["style"].items()))
    print()
    show(ranking.drop(columns=["managers"]), args)
    return 0


def minutes_check(players, player_id, args):
    """Warn when the reference season is too small to rely on and, with
    --regular-season, switch to the latest season with enough minutes.
    Returns the season to use."""
    season, minutes, regular, regular_minutes = teamfit.check_minutes(players, player_id, args.season)
    if minutes >= teamfit.REGULAR_SEASON_MINUTES:
        return season
    name = players.loc[players["understat_player_id"] == player_id, "player"].iloc[-1]
    small = "%s played only %d minutes in %s (under %d)" % (name, minutes, season, teamfit.REGULAR_SEASON_MINUTES)
    if regular is None:
        print("WARNING: %s and has no season with %d+ minutes, so these results are unreliable.\n"
              % (small, teamfit.REGULAR_SEASON_MINUTES))
        return season
    if args.regular_season:
        print("Using %s (%d min), his latest season with %d+ minutes, because %s.\n"
              % (regular, regular_minutes, teamfit.REGULAR_SEASON_MINUTES, small))
        return regular
    print("WARNING: %s, so his numbers there are unreliable.\n"
          "         His latest season with %d+ minutes is %s (%d min). "
          "Add --regular-season to use it instead.\n"
          % (small, teamfit.REGULAR_SEASON_MINUTES, regular, regular_minutes))
    return season


def show(ranking, args):
    with pd.option_context("display.max_colwidth", 95, "display.width", 250):
        print(ranking.head(args.top).round(1).to_string(index=False))
    if args.csv:
        ranking.round(2).to_csv(args.csv, index=False)
        print("\nWrote %s" % args.csv)


if __name__ == "__main__":
    sys.exit(main())
