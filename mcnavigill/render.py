"""Interactive route maps with folium.

The graph lives in a local metric frame rather than latitude/longitude, so the map uses
Leaflet's flat ``Simple`` CRS with no tile layer: one map unit is one metre. Corridors and
tunnels are drawn solid, outdoor paths dashed, and the route on top.
"""

from __future__ import annotations

from collections.abc import Iterable

import folium

from .graph import CampusGraph
from .routing import Route

INDOOR = "#1f4e79"
OUTDOOR = "#2e7d32"
ROUTE_COLOURS = ("#d1495b", "#00798c", "#edae49", "#6a4c93")


def _latlng(p: tuple[float, float]) -> tuple[float, float]:
    x, y = p
    return (y, x)  # Leaflet expects [lat, lng] = [y, x]


def route_map(graph: CampusGraph, routes: Iterable[Route] = (), labels: Iterable[str] = (),
              title: str | None = None) -> folium.Map:
    routes, labels = list(routes), list(labels)
    xs = [n.x for n in graph.nodes.values()]
    ys = [n.y for n in graph.nodes.values()]
    pad = 15
    bounds = [[min(ys) - pad, min(xs) - pad], [max(ys) + pad, max(xs) + pad]]

    m = folium.Map(location=[(min(ys) + max(ys)) / 2, (min(xs) + max(xs)) / 2],
                   crs="Simple", tiles=None, zoom_start=1, min_zoom=-1, max_zoom=4,
                   control_scale=False)
    m.fit_bounds(bounds)
    m.get_root().header.add_child(folium.Element(
        "<style>.leaflet-container{background:#fafafa}</style>"))

    network = folium.FeatureGroup(name="Campus network")
    for e in graph.edges:
        folium.PolyLine(
            [_latlng(p) for p in e.points],
            color=INDOOR if e.kind == "indoor" else OUTDOOR,
            weight=4 if e.kind == "indoor" else 3,
            dash_array=None if e.kind == "indoor" else "6 6",
            opacity=0.55,
            tooltip=f"{e.u}–{e.v}: {e.length_cm / 100:.0f} m {e.kind}",
        ).add_to(network)
    for n in graph.nodes.values():
        if n.kind == "entrance":
            folium.CircleMarker(_latlng((n.x, n.y)), radius=5, color="#333", weight=1,
                                fill=True, fill_color="#fff", fill_opacity=1,
                                tooltip=n.label).add_to(network)
    network.add_to(m)

    for i, route in enumerate(routes):
        name = labels[i] if i < len(labels) else f"Route {i + 1}"
        colour = ROUTE_COLOURS[i % len(ROUTE_COLOURS)]
        layer = folium.FeatureGroup(name=name)
        folium.PolyLine([_latlng(p) for p in route.polyline()], color=colour, weight=7,
                        opacity=0.9,
                        tooltip=(f"{name}: {route.length_m:.0f} m, "
                                 f"{route.outdoor_m:.0f} m outdoors, "
                                 f"~{route.minutes:.0f} min")).add_to(layer)
        layer.add_to(m)

    if routes:
        src, dst = graph.nodes[routes[0].nodes[0]], graph.nodes[routes[0].nodes[-1]]
        folium.Marker(_latlng((src.x, src.y)), tooltip=f"From {src.label}",
                      icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker(_latlng((dst.x, dst.y)), tooltip=f"To {dst.label}",
                      icon=folium.Icon(color="red", icon="stop")).add_to(m)

    if title:
        m.get_root().html.add_child(folium.Element(
            f'<div style="position:fixed;top:10px;left:50px;z-index:9999;background:#fff;'
            f'padding:6px 10px;border-radius:4px;font:14px sans-serif;'
            f'box-shadow:0 1px 4px rgba(0,0,0,.3)">{title}</div>'))
    folium.LayerControl(collapsed=False).add_to(m)
    return m
