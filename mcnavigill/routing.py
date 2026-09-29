"""Route search over the campus graph.

Two objectives, both solved with Dijkstra's algorithm on a binary heap:

* ``shortest`` minimises total walking distance, ties broken by outdoor distance;
* ``warmest``  minimises distance walked outdoors, ties broken by total distance.

Each objective is a lexicographic pair of non-negative integer costs, so Dijkstra's
greedy step stays valid and tie-breaking is exact.

``pareto_routes`` returns every route that is not beaten on both criteria at once, using a
bicriteria label-setting search (Martins, 1984). The two single-objective routes are the
two ends of that front.
"""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass, field

from .graph import CampusGraph, Edge

WALKING_SPEED_M_PER_MIN = 80.0  # about 1.33 m/s

OBJECTIVES = {
    "shortest": lambda e: (e.length_cm, e.outdoor_cm),
    "warmest": lambda e: (e.outdoor_cm, e.length_cm),
}


class NoRoute(Exception):
    pass


@dataclass(frozen=True)
class Route:
    nodes: tuple[str, ...]
    edges: tuple[Edge, ...] = field(repr=False)

    @property
    def length_cm(self) -> int:
        return sum(e.length_cm for e in self.edges)

    @property
    def outdoor_cm(self) -> int:
        return sum(e.outdoor_cm for e in self.edges)

    @property
    def length_m(self) -> float:
        return self.length_cm / 100

    @property
    def outdoor_m(self) -> float:
        return self.outdoor_cm / 100

    @property
    def minutes(self) -> float:
        return self.length_m / WALKING_SPEED_M_PER_MIN

    def polyline(self) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for start, e in zip(self.nodes, self.edges):
            seg = e.oriented(start)
            pts.extend(seg if not pts else seg[1:])
        return pts


def _check(graph: CampusGraph, *nodes: str) -> None:
    for n in nodes:
        if n not in graph.nodes:
            raise KeyError(f"unknown node {n!r}")


def dijkstra(graph: CampusGraph, source: str, target: str, objective: str = "shortest") -> Route:
    """Optimal route from ``source`` to ``target`` under one objective."""
    if objective not in OBJECTIVES:
        raise ValueError(f"objective must be one of {sorted(OBJECTIVES)}")
    _check(graph, source, target)
    weight = OBJECTIVES[objective]

    best: dict[str, tuple[int, int]] = {source: (0, 0)}
    parent: dict[str, tuple[str, Edge]] = {}
    settled: set[str] = set()
    heap: list[tuple[tuple[int, int], str]] = [((0, 0), source)]

    while heap:
        cost, u = heapq.heappop(heap)
        if u in settled:
            continue  # stale heap entry
        settled.add(u)
        if u == target:
            break
        for e in graph.neighbours(u):
            v = e.other(u)
            if v in settled:
                continue
            w = weight(e)
            cand = (cost[0] + w[0], cost[1] + w[1])
            if v not in best or cand < best[v]:
                best[v] = cand
                parent[v] = (u, e)
                heapq.heappush(heap, (cand, v))

    if target not in settled:
        raise NoRoute(f"{target!r} is not reachable from {source!r}")

    nodes, edges = [target], []
    while nodes[-1] != source:
        prev, e = parent[nodes[-1]]
        edges.append(e)
        nodes.append(prev)
    return Route(tuple(reversed(nodes)), tuple(reversed(edges)))


def pareto_routes(graph: CampusGraph, source: str, target: str) -> list[Route]:
    """All Pareto-optimal routes on (total distance, outdoor distance), shortest first.

    Labels are popped in lexicographic order of (distance, outdoor). A popped label is
    kept only if its outdoor cost is strictly below every label already kept at that node,
    which is exactly the non-dominance test in this order. Labels that the target's front
    already dominates are pruned. Every edge has positive length, so no cycle survives.
    """
    _check(graph, source, target)
    counter = itertools.count()  # heap tie-breaker; labels themselves are not comparable
    # label: (length, outdoor, seq, node, parent_label, edge)
    heap = [(0, 0, next(counter), source, None, None)]
    best_outdoor: dict[str, int] = {}  # lowest outdoor cost among kept labels, per node
    found = []

    while heap:
        label = heapq.heappop(heap)
        length, outdoor, _, u, _, _ = label
        if outdoor >= best_outdoor.get(u, float("inf")):
            continue  # dominated at u
        if outdoor >= best_outdoor.get(target, float("inf")):
            continue  # cannot improve the target's front
        best_outdoor[u] = outdoor
        if u == target:
            found.append(label)
            continue
        for e in graph.neighbours(u):
            v = e.other(u)
            heapq.heappush(heap, (length + e.length_cm, outdoor + e.outdoor_cm,
                                  next(counter), v, label, e))

    routes = []
    for label in found:
        nodes, edges = [], []
        while label is not None:
            nodes.append(label[3])
            if label[5] is not None:
                edges.append(label[5])
            label = label[4]
        routes.append(Route(tuple(reversed(nodes)), tuple(reversed(edges))))
    return routes
