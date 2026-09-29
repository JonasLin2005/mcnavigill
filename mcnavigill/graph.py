"""Campus graph for the McGill engineering quarter.

Nodes and edges are read from ``data/nodes.csv`` and ``data/edges.csv``. Geometry was
digitized in pixels from the team's annotated campus map and is converted here to metres
in a local frame (x to the east along Sherbrooke, y to the north). Each edge stores its
full polyline, and its length is measured along that polyline, so bends count.

Lengths are kept as integer centimetres. Route costs are sums of integers, which keeps
tie-breaking exact.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

#: Absolute scale of the digitized map. Calibrated so that the hackathon estimate of
#: 200 m for Adams -> Burnside Hall (node 5 -> node 12, indoor route) holds.
METRES_PER_PIXEL = 0.38

EDGE_KINDS = ("indoor", "outdoor")


@dataclass(frozen=True)
class Node:
    id: str
    kind: str  # "entrance", "junction" or "waypoint"
    building: str
    x: float  # metres, local frame
    y: float

    @property
    def label(self) -> str:
        return f"{self.id} ({self.building})" if self.building else self.id


@dataclass(frozen=True)
class Edge:
    u: str
    v: str
    kind: str  # "indoor" (corridor or tunnel) or "outdoor"
    points: tuple[tuple[float, float], ...]  # polyline from u to v, metres
    length_cm: int

    @property
    def outdoor_cm(self) -> int:
        return self.length_cm if self.kind == "outdoor" else 0

    def other(self, node: str) -> str:
        return self.v if node == self.u else self.u

    def oriented(self, start: str) -> tuple[tuple[float, float], ...]:
        """Polyline read from ``start`` to the other end."""
        return self.points if start == self.u else tuple(reversed(self.points))


class CampusGraph:
    """Undirected weighted graph with adjacency lists."""

    def __init__(self, nodes: list[Node], edges: list[Edge]):
        self.nodes: dict[str, Node] = {}
        for n in nodes:
            if n.id in self.nodes:
                raise ValueError(f"duplicate node id {n.id!r}")
            self.nodes[n.id] = n
        self.edges = list(edges)
        self.adj: dict[str, list[Edge]] = {n: [] for n in self.nodes}
        seen: set[frozenset[str]] = set()
        for e in self.edges:
            for end in (e.u, e.v):
                if end not in self.nodes:
                    raise ValueError(f"edge {e.u}-{e.v} refers to unknown node {end!r}")
            if e.u == e.v:
                raise ValueError(f"self-loop at {e.u!r}")
            if e.kind not in EDGE_KINDS:
                raise ValueError(f"edge {e.u}-{e.v} has unknown kind {e.kind!r}")
            if e.length_cm <= 0:
                raise ValueError(f"edge {e.u}-{e.v} has non-positive length")
            key = frozenset((e.u, e.v))
            if key in seen:
                raise ValueError(f"parallel edge {e.u}-{e.v}")
            seen.add(key)
            self.adj[e.u].append(e)
            self.adj[e.v].append(e)

    # ------------------------------------------------------------------ loading
    @classmethod
    def from_csv(cls, nodes_csv: Path, edges_csv: Path,
                 metres_per_pixel: float = METRES_PER_PIXEL) -> "CampusGraph":
        def to_m(x: float, y: float) -> tuple[float, float]:
            # image y grows downward; flip so north is up
            return (x * metres_per_pixel, -y * metres_per_pixel)

        nodes = []
        pixel = {}
        with open(nodes_csv, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                px = (float(row["x_px"]), float(row["y_px"]))
                pixel[row["id"]] = px
                x, y = to_m(*px)
                nodes.append(Node(row["id"], row["kind"], row["building"], x, y))

        edges = []
        with open(edges_csv, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                u, v = row["u"], row["v"]
                via = [tuple(map(float, p.split())) for p in row["via"].split(";") if p.strip()]
                try:
                    pts = [pixel[u], *via, pixel[v]]
                except KeyError as err:
                    raise ValueError(f"edge {u}-{v} refers to unknown node {err}") from None
                pts_m = tuple(to_m(*p) for p in pts)
                length = sum(math.dist(a, b) for a, b in zip(pts_m, pts_m[1:]))
                edges.append(Edge(u, v, row["kind"], pts_m, round(length * 100)))
        return cls(nodes, edges)

    @classmethod
    def load(cls) -> "CampusGraph":
        """The bundled engineering-quarter graph."""
        data = resources.files("mcnavigill") / "data"
        with resources.as_file(data / "nodes.csv") as n, resources.as_file(data / "edges.csv") as e:
            return cls.from_csv(n, e)

    # ------------------------------------------------------------------ queries
    def neighbours(self, node: str) -> list[Edge]:
        return self.adj[node]

    def entrances(self) -> list[Node]:
        return [n for n in self.nodes.values() if n.kind == "entrance"]

    def resolve(self, name: str) -> str:
        """Accept a node id ("12") or a building name ("burnside") and return a node id."""
        if name in self.nodes:
            return name
        key = name.strip().lower()
        hits = sorted({n.id for n in self.entrances() if key and key in n.building.lower()},
                      key=_natural)
        if not hits:
            raise KeyError(f"no node or building matches {name!r}")
        return hits[0]


def _natural(node_id: str) -> tuple[int, str]:
    return (int(node_id), "") if node_id.isdigit() else (10**6, node_id)
