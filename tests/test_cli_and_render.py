from unittest import mock

import requests

from mcnavigill import CampusGraph, dijkstra
from mcnavigill.cli import main
from mcnavigill.locate import LocateError, locate
from mcnavigill.render import route_map


def test_route_map_writes_html(tmp_path):
    g = CampusGraph.load()
    routes = [dijkstra(g, "3", "17", o) for o in ("shortest", "warmest")]
    out = tmp_path / "map.html"
    route_map(g, routes, ["Shortest", "Warmest"], title="test").save(str(out))
    html = out.read_text(encoding="utf-8")
    assert "L.CRS.Simple" in html and "Warmest" in html


def test_cli_route(tmp_path, capsys):
    out = tmp_path / "r.html"
    assert main(["route", "macdonald eng", "17", "--out", str(out)]) == 0
    text = capsys.readouterr().out
    assert "Shortest:" in text and "Warmest:" in text and out.exists()


def test_cli_pareto_and_nodes(capsys):
    assert main(["pareto", "3", "17"]) == 0
    assert "Pareto 1:" in capsys.readouterr().out
    assert main(["nodes"]) == 0
    assert "Burnside Hall" in capsys.readouterr().out


def test_cli_unknown_building(capsys):
    assert main(["route", "redpath", "17"]) == 2


def _response(payload):
    r = mock.Mock()
    r.json.return_value = payload
    r.raise_for_status.return_value = None
    return r


def test_locate_parses_loc():
    s = mock.Mock()
    s.get.return_value = _response({"loc": "45.5017,-73.5673", "city": "Montreal",
                                    "region": "Quebec"})
    loc = locate(session=s)
    assert (loc.lat, loc.lon, loc.city) == (45.5017, -73.5673, "Montreal")


def test_locate_errors():
    s = mock.Mock()
    s.get.return_value = _response({"city": "Montreal"})  # no "loc"
    try:
        locate(session=s)
    except LocateError:
        pass
    else:
        raise AssertionError("expected LocateError")
    s.get.side_effect = requests.ConnectionError("offline")
    try:
        locate(session=s)
    except LocateError:
        pass
    else:
        raise AssertionError("expected LocateError")
