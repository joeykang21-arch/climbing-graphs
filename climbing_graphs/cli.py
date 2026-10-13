"""Command-line interface: ``python -m climbing_graphs <command> ...``

Run ``python -m climbing_graphs --help`` for the full list of commands.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from . import charts, theme
from .scoring import CATEGORIES, SCHEMES, describe_weights, score_climbers
from .sources import read_ascent_list, read_ifsc_wins

log = logging.getLogger("climbing_graphs")

DEFAULT_OUT = Path("output")
COMP_HIGHLIGHT = {"men": "Jakob Schubert", "women": "Janja Garnbret"}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    # Climber names and "·" separators can't always be encoded by Windows consoles.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    args.handler(args)
    return 0


# --- commands -----------------------------------------------------------------------


def cmd_best(args: argparse.Namespace) -> None:
    categories = list(CATEGORIES) if args.category == "all" else [args.category]
    schemes = list(SCHEMES) if args.scheme == "all" else [args.scheme]
    for category_key in categories:
        category = CATEGORIES[category_key]
        ascents = read_ascent_list(category.url, refresh=args.refresh)
        if args.as_of is not None:
            # Ascents with unknown dates are kept: there's no way to tell when they happened.
            ascents = ascents[~(ascents["date"] > args.as_of)]
        for scheme_key in schemes:
            scheme = SCHEMES[scheme_key]
            ranking = score_climbers(ascents, scheme, category.scale)
            weights = describe_weights(ranking.weights, category.scale)
            _print_ranking(f"{category.title} ({scheme.title}: {weights})", ranking.table)

            subtitle = f"{scheme.title.capitalize()}: {weights}"
            if args.as_of is not None:
                subtitle += f" · ascents up to {args.as_of:%d %b %Y}"
            fig = charts.strip_chart(
                ranking.table,
                title=category.title,
                subtitle=subtitle,
                score_label=category.score_label,
                highlight=args.highlight or category.highlight,
                top_labels=args.top,
                extra_labels=[*category.always_label, *args.label],
                log_axis=scheme.log_axis if args.log is None else args.log,
                background=args.background,
            )
            _save(fig, args, f"best_{category_key}_{scheme_key}")


def cmd_comp(args: argparse.Namespace) -> None:
    genders = ["men", "women"] if args.gender == "all" else [args.gender]
    for gender in genders:
        wins = read_ifsc_wins(gender, refresh=args.refresh)
        table = pd.DataFrame(
            {
                "climber": wins["climber"],
                "score": wins["lead"] + wins["boulder"] + wins["combined"],
                "detail": [
                    f"Lead: {r.lead:g}<br>Boulder: {r.boulder:g}<br>Combined: {r.combined:g}"
                    for r in wins.itertuples()
                ],
            }
        )
        table = table[table["score"] > 0].sort_values(["score", "climber"], ascending=[False, True])
        _print_ranking(f"IFSC wins, {gender}, no speed", table)
        fig = charts.strip_chart(
            table,
            title=f"Best Competition Climbers ({gender.capitalize()}, No Speed)",
            subtitle="Career IFSC World Cup series and World Championship wins in lead, boulder and combined",
            score_label="IFSC wins",
            highlight=args.highlight or COMP_HIGHLIGHT[gender],
            top_labels=args.top,
            extra_labels=args.label,
            background=args.background,
        )
        _save(fig, args, f"comp_{gender}")


def cmd_frontier(args: argparse.Namespace) -> None:
    keys = list(charts.COMPARISONS) if args.comparison == "all" else [args.comparison]
    for key in keys:
        comparison = charts.COMPARISONS[key]
        _save(charts.frontier_chart(comparison), args, f"frontier_{key}")
        _save(charts.gap_chart(comparison), args, f"gap_{key}")


def cmd_projection(args: argparse.Namespace) -> None:
    keys = list(charts.PROJECTIONS) if args.projection == "all" else [args.projection]
    for key in keys:
        _save(charts.projection_chart(charts.PROJECTIONS[key]), args, f"projection_{key}")


def cmd_timeline(args: argparse.Namespace) -> None:
    ascents = read_ascent_list(CATEGORIES["boulder"].url, refresh=args.refresh)
    _save(charts.timeline_chart(ascents), args, "timeline_hard_boulders")


def cmd_thumbnail(args: argparse.Namespace) -> None:
    _save(charts.thumbnail_chart(), args, "thumbnail")


def cmd_all(args: argparse.Namespace) -> None:
    for handler, extra in [
        (cmd_best, dict(category="all", scheme="all", as_of=None, log=None)),
        (cmd_comp, dict(gender="all")),
        (cmd_frontier, dict(comparison="all")),
        (cmd_projection, dict(projection="all")),
        (cmd_timeline, {}),
        (cmd_thumbnail, {}),
    ]:
        handler(argparse.Namespace(**{**vars(args), **extra}))


# --- helpers ------------------------------------------------------------------------


def _save(fig, args: argparse.Namespace, name: str) -> None:
    path = theme.save(fig, args.out / f"{name}.html", show=args.show)
    log.info("Saved %s", path)


def _print_ranking(heading: str, table: pd.DataFrame, n: int = 10) -> None:
    log.info("\n%s", heading)
    for rank, row in enumerate(table.head(n).itertuples(), start=1):
        log.info("  %2d. %-28s %8.4g", rank, row.climber, row.score)


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder (default: output/)")
    common.add_argument("--show", action="store_true", help="also open each chart in the browser")
    common.add_argument("--refresh", action="store_true", help="re-download source pages, ignoring the cache")
    common.add_argument("-v", "--verbose", action="store_true")

    strip = argparse.ArgumentParser(add_help=False)
    strip.add_argument("--highlight", help="climber to draw as a large diamond")
    strip.add_argument("--top", type=int, default=12, help="number of top climbers to label (default 12)")
    strip.add_argument("--label", action="append", default=[], metavar="NAME", help="always label this climber")
    strip.add_argument("--background", type=Path, help="image to stretch behind the plot")

    parser = argparse.ArgumentParser(prog="python -m climbing_graphs", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    best = commands.add_parser("best", parents=[common, strip], help="rank climbers by their hardest ascents")
    best.add_argument("category", choices=[*CATEGORIES, "all"])
    best.add_argument("--scheme", choices=[*SCHEMES, "all"], default="exponential",
                      help="scoring system (default: exponential = 18/5/1)")
    best.add_argument("--as-of", type=pd.Timestamp, metavar="YYYY-MM-DD",
                      help="only count ascents up to this date")
    log_flag = best.add_mutually_exclusive_group()
    log_flag.add_argument("--log", dest="log", action="store_true", default=None, help="force a log score axis")
    log_flag.add_argument("--linear", dest="log", action="store_false", help="force a linear score axis")
    best.set_defaults(handler=cmd_best)

    comp = commands.add_parser("comp", parents=[common, strip], help="rank competition climbers by IFSC wins")
    comp.add_argument("gender", choices=["men", "women", "all"])
    comp.set_defaults(handler=cmd_comp)

    frontier = commands.add_parser("frontier", parents=[common], help="hardest grade over time + gap charts")
    frontier.add_argument("comparison", choices=[*charts.COMPARISONS, "all"])
    frontier.set_defaults(handler=cmd_frontier)

    projection = commands.add_parser("projection", parents=[common], help="when will the next grade fall?")
    projection.add_argument("projection", choices=[*charts.PROJECTIONS, "all"])
    projection.set_defaults(handler=cmd_projection)

    commands.add_parser("timeline", parents=[common], help="animated hard-boulder ascents").set_defaults(
        handler=cmd_timeline
    )
    commands.add_parser("thumbnail", parents=[common], help="illustrative video thumbnail").set_defaults(
        handler=cmd_thumbnail
    )
    commands.add_parser("all", parents=[common, strip], help="generate every chart").set_defaults(handler=cmd_all)
    return parser
