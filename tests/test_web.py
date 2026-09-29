"""The web front end's data file matches the package and is up to date."""

import json
from pathlib import Path

from mcnavigill import CampusGraph, dijkstra
from mcnavigill.web import build_data, render_data_js

ROOT = Path(__file__).resolve().parent.parent
G = CampusGraph.load()


def test_data_js_is_current():
    committed = (ROOT / "web" / "data.js").read_text(encoding="utf-8")
    assert committed == render_data_js(build_data()), "run: python scripts/build_web.py"


def test_exported_fronts_match_dijkstra():
    data = build_data(G)
    ids = [e["id"] for e in data["entrances"]]
    assert len(data["routes"]) == len(ids) * (len(ids) - 1)
    for pair, front in data["routes"].items():
        a, b = pair.split("|")
        s, w = dijkstra(G, a, b, "shortest"), dijkstra(G, a, b, "warmest")
        assert front[0]["L"] == round(s.length_m, 1) and front[0]["O"] == round(s.outdoor_m, 1)
        assert front[-1]["O"] == round(w.outdoor_m, 1) and front[-1]["L"] == round(w.length_m, 1)
        for r in front:
            assert r["n"][0] == a and r["n"][-1] == b


def test_page_references_data():
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    assert '<script src="data.js"></script>' in html
    body = (ROOT / "web" / "data.js").read_text(encoding="utf-8")
    json.loads(body.split("window.MCNAV = ", 1)[1].rstrip().rstrip(";"))
