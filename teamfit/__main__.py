"""Rank Big Five clubs by fit for one player.

    python3 -m teamfit "Bukayo Saka"
    python3 -m teamfit "Florian Wirtz" --season 2024-25 --leagues EPL ESP --top 5
    python3 -m teamfit --id 8260 --csv saka_fit.csv
    python3 -m teamfit --team-styles team_styles_2025-26.csv --target-season 2025-26
"""

import argparse
import sys

import pandas as pd

from . import teamfit


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m teamfit", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("player", nargs="?", help="player name (accents and case ignored)")
    parser.add_argument("--id", type=int, help="understat_player_id, if the name is ambiguous")
    parser.add_argument("--season", help="player's reference season, e.g. 2024-25 (default: his latest)")
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
    if not args.player and args.id is None:
        parser.error("give a player name or --id")

    players = teamfit.load_players()
    try:
        player_id = teamfit.find_player(players, args.player, args.id)
        ctx, ranking = teamfit.rank_clubs(player_id, players, teams, args.season,
                                          args.target_season, args.leagues, args.include_current)
    except ValueError as err:
        print(err, file=sys.stderr)
        return 1

    score = "n/a" if ctx["role_score"] is None else "%+.2f" % ctx["role_score"]
    print("%s | %s %s | %s (%s) | %d min | role score %s"
          % (ctx["player"], ctx["season"], ", ".join(ctx["clubs"]), ctx["sub_position"],
             ctx["role"], ctx["minutes"], score))
    print("Style of recent clubs (z): " + ", ".join(
        "%s %+.2f" % (d, v) for d, v in ctx["style"].items()))
    print()
    with pd.option_context("display.max_colwidth", 90, "display.width", 200):
        shown = ranking.head(args.top).drop(columns=["managers"]).round(0)
        print(shown.to_string(index=False))

    if args.csv:
        ranking.round(2).to_csv(args.csv, index=False)
        print("\nWrote %s" % args.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
