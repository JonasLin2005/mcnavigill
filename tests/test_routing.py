"""Dijkstra and the Pareto search, checked against exhaustive path enumeration."""

import itertools

import pytest

from mcnavigill import CampusGraph, NoRoute, dijkstra, pareto_routes
from mcnavigill.graph import Edge, Node

G = CampusGraph.load()
ENTRANCES = sorted(n.id for n in G.entrances())
PAIRS = list(itertools.permutations(ENTRANCES, 2))


def all_simple_paths(graph, source, target):
    """Every simple path as (length_cm, outdoor_cm, nodes)."""
    out = []

    def walk(u, seen, nodes, length, outdoor):
        if u == target:
            out.append((length, outdoor, tuple(nodes)))
            return
        for e in graph.neighbours(u):
            v = e.other(u)
            if v not in seen:
                seen.add(v)
                nodes.append(v)
                walk(v, seen, nodes, length + e.length_cm, outdoor + e.outdoor_cm)
                nodes.pop()
                seen.remove(v)

    walk(source, {source}, [source], 0, 0)
    return out


BRUTE = {pair: all_simple_paths(G, *pair) for pair in PAIRS}


def is_valid(route, source, target):
    assert route.nodes[0] == source and route.nodes[-1] == target
    assert len(route.edges) == len(route.nodes) - 1
    for a, b, e in zip(route.nodes, route.nodes[1:], route.edges):
        assert {a, b} == {e.u, e.v}
    assert len(set(route.nodes)) == len(route.nodes)


def test_graph_loads_and_is_connected():
    assert len(G.entrances()) == 8
    reached, stack = {"1"}, ["1"]
    while stack:
        u = stack.pop()
        for e in G.neighbours(u):
            v = e.other(u)
            if v not in reached:
                reached.add(v)
                stack.append(v)
    assert reached == set(G.nodes)


@pytest.mark.parametrize("source,target", PAIRS)
def test_shortest_matches_brute_force(source, target):
    route = dijkstra(G, source, target, "shortest")
    is_valid(route, source, target)
    best = min((l, o) for l, o, _ in BRUTE[(source, target)])
    assert (route.length_cm, route.outdoor_cm) == best


@pytest.mark.parametrize("source,target", PAIRS)
def test_warmest_matches_brute_force(source, target):
    route = dijkstra(G, source, target, "warmest")
    is_valid(route, source, target)
    best = min((o, l) for l, o, _ in BRUTE[(source, target)])
    assert (route.outdoor_cm, route.length_cm) == best


@pytest.mark.parametrize("source,target", PAIRS)
def test_pareto_front_matches_brute_force(source, target):
    costs = {(l, o) for l, o, _ in BRUTE[(source, target)]}
    front = sorted(c for c in costs
                   if not any(d != c and d[0] <= c[0] and d[1] <= c[1] for d in costs))
    routes = pareto_routes(G, source, target)
    for r in routes:
        is_valid(r, source, target)
    assert [(r.length_cm, r.outdoor_cm) for r in routes] == front
    # the single-objective optima are the two ends of the front
    assert (routes[0].length_cm, routes[0].outdoor_cm) == \
        (dijkstra(G, source, target, "shortest").length_cm,
         dijkstra(G, source, target, "shortest").outdoor_cm)
    assert routes[-1].outdoor_cm == dijkstra(G, source, target, "warmest").outdoor_cm


def test_routes_are_symmetric():
    for a, b in PAIRS:
        for obj in ("shortest", "warmest"):
            assert dijkstra(G, a, b, obj).length_cm == dijkstra(G, b, a, obj).length_cm


def test_warmest_trades_distance_for_shelter():
    """At least one pair where staying indoors costs extra distance."""
    gaps = [dijkstra(G, a, b, "warmest").length_cm - dijkstra(G, a, b, "shortest").length_cm
            for a, b in PAIRS]
    assert max(gaps) > 0 and min(gaps) == 0


def test_scale_calibration():
    """Adams (5) to Burnside Hall (12) indoors is the 200 m the scale was set from."""
    route = dijkstra(G, "5", "12", "warmest")
    assert route.outdoor_cm == 0
    assert route.length_m == pytest.approx(200, abs=1)


def test_same_node_and_errors():
    r = dijkstra(G, "3", "3")
    assert r.nodes == ("3",) and r.length_cm == 0
    with pytest.raises(KeyError):
        dijkstra(G, "3", "99")
    with pytest.raises(ValueError):
        dijkstra(G, "3", "17", "fastest")


def test_disconnected_graph_raises():
    nodes = [Node(i, "entrance", "", float(k), 0.0) for k, i in enumerate("abc")]
    edges = [Edge("a", "b", "indoor", ((0.0, 0.0), (1.0, 0.0)), 100)]
    g = CampusGraph(nodes, edges)
    with pytest.raises(NoRoute):
        dijkstra(g, "a", "c")
    assert pareto_routes(g, "a", "c") == []


def test_bad_graph_rejected():
    n = [Node("a", "entrance", "", 0.0, 0.0), Node("b", "entrance", "", 1.0, 0.0)]
    with pytest.raises(ValueError):
        CampusGraph(n, [Edge("a", "b", "skyway", ((0, 0), (1, 0)), 100)])
    with pytest.raises(ValueError):
        CampusGraph(n, [Edge("a", "b", "indoor", ((0, 0), (1, 0)), 0)])


def test_resolve_building_names():
    assert G.resolve("burnside") == "12"
    assert G.resolve("7") == "7"
    with pytest.raises(KeyError):
        G.resolve("redpath")
