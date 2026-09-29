"""Command line: ``mcnavigill nodes | route | pareto | where``."""

from __future__ import annotations

import argparse
import sys

from .graph import CampusGraph
from .routing import NoRoute, Route, dijkstra, pareto_routes


def _summary(route: Route, graph: CampusGraph) -> str:
    path = " -> ".join(route.nodes)
    return (f"{path}\n  {route.length_m:.0f} m total, {route.outdoor_m:.0f} m outdoors, "
            f"about {route.minutes:.0f} min "
            f"({graph.nodes[route.nodes[0]].building or route.nodes[0]} to "
            f"{graph.nodes[route.nodes[-1]].building or route.nodes[-1]})")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mcnavigill",
                                description="Winter routing across McGill's engineering quarter.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("nodes", help="list building entrances")

    r = sub.add_parser("route", help="best route under one objective")
    r.add_argument("source", help="node id or building name, e.g. 3 or 'macdonald eng'")
    r.add_argument("target")
    r.add_argument("--objective", choices=["shortest", "warmest", "both"], default="both")
    r.add_argument("--out", help="write an interactive HTML map here")

    pr = sub.add_parser("pareto", help="every route not beaten on both distance and exposure")
    pr.add_argument("source")
    pr.add_argument("target")
    pr.add_argument("--out", help="write an interactive HTML map here")

    w = sub.add_parser("where", help="approximate location from your IP address")
    w.add_argument("--out", help="write an HTML map here")

    args = p.parse_args(argv)

    if args.cmd == "where":
        from .locate import LocateError, locate, location_map
        try:
            loc = locate()
        except LocateError as err:
            print(err, file=sys.stderr)
            return 1
        print(f"{loc.city}, {loc.region}: {loc.lat:.4f}, {loc.lon:.4f}")
        if args.out:
            location_map(loc).save(args.out)
            print(f"map written to {args.out}")
        return 0

    graph = CampusGraph.load()

    if args.cmd == "nodes":
        for n in sorted(graph.entrances(), key=lambda n: int(n.id)):
            print(f"{n.id:>3}  {n.building}")
        return 0

    try:
        src, dst = graph.resolve(args.source), graph.resolve(args.target)
    except KeyError as err:
        print(err.args[0], file=sys.stderr)
        return 2

    try:
        if args.cmd == "route":
            objectives = ["shortest", "warmest"] if args.objective == "both" else [args.objective]
            routes = [dijkstra(graph, src, dst, o) for o in objectives]
            labels = [o.capitalize() for o in objectives]
        else:
            routes = pareto_routes(graph, src, dst)
            labels = [f"Pareto {i + 1}" for i in range(len(routes))]
    except NoRoute as err:
        print(err, file=sys.stderr)
        return 1

    for label, route in zip(labels, routes):
        print(f"{label}: {_summary(route, graph)}")

    if args.out:
        from .render import route_map
        title = f"{graph.nodes[src].label} → {graph.nodes[dst].label}"
        route_map(graph, routes, labels, title=title).save(args.out)
        print(f"map written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
