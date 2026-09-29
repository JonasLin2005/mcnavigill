"""Static figure for the README: the network with the shortest and warmest routes.

    python scripts/draw_figure.py 3 17 docs/routes.png
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcnavigill import CampusGraph, dijkstra  # noqa: E402
from mcnavigill.render import INDOOR, OUTDOOR  # noqa: E402


def main(source="3", target="17", out="docs/routes.png"):
    g = CampusGraph.load()
    fig, ax = plt.subplots(figsize=(5.2, 7.2), dpi=150)
    for e in g.edges:
        xs, ys = zip(*e.points)
        ax.plot(xs, ys, color=INDOOR if e.kind == "indoor" else OUTDOOR,
                lw=2.2 if e.kind == "indoor" else 1.6,
                ls="-" if e.kind == "indoor" else (0, (4, 3)), alpha=0.45, zorder=1)
    styles = {"shortest": ("#d1495b", 5.5), "warmest": ("#00798c", 3.5)}
    for obj, (colour, lw) in styles.items():
        r = dijkstra(g, source, target, obj)
        xs, ys = zip(*r.polyline())
        ax.plot(xs, ys, color=colour, lw=lw, alpha=0.9, zorder=2, solid_capstyle="round",
                label=f"{obj}: {r.length_m:.0f} m, {r.outdoor_m:.0f} m outdoors")
    for n in g.entrances():
        ax.scatter(n.x, n.y, s=28, c="white", edgecolors="#333", zorder=3)
        ax.annotate(n.building, (n.x, n.y), xytext=(5, 3), textcoords="offset points",
                    fontsize=6.5, color="#333", zorder=4)
    ax.plot([], [], color=INDOOR, lw=2.2, alpha=0.6, label="corridor / tunnel")
    ax.plot([], [], color=OUTDOOR, lw=1.6, ls=(0, (4, 3)), alpha=0.6, label="outdoor path")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc="lower left", bbox_to_anchor=(0, -0.13), fontsize=7, frameon=False, ncol=1)
    src, dst = g.nodes[source].building, g.nodes[target].building
    ax.set_title(f"{src} → {dst}", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")


if __name__ == "__main__":
    main(*sys.argv[1:])
