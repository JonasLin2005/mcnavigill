"""Approximate user location from the public IP address, via ipinfo.io.

IP geolocation resolves to a city, not a building, so the router does not snap to it; the
``where`` command shows it on an OpenStreetMap map. This is the hackathon GPS script with
two fixes: ipinfo returns the coordinates under ``loc`` (the original read ``location`` and
always fell into its error branch), and errors are raised instead of calling ``exit()``.
"""

from __future__ import annotations

from dataclasses import dataclass

import folium
import requests

IPINFO_URL = "https://ipinfo.io/json"


@dataclass(frozen=True)
class Location:
    lat: float
    lon: float
    city: str
    region: str


class LocateError(RuntimeError):
    pass


def locate(timeout: float = 5.0, session: requests.Session | None = None) -> Location:
    http = session or requests
    try:
        resp = http.get(IPINFO_URL, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        lat, lon = (float(v) for v in data["loc"].split(","))
    except (requests.RequestException, KeyError, ValueError) as err:
        raise LocateError(f"could not geolocate this connection: {err}") from err
    return Location(lat, lon, data.get("city", "unknown"), data.get("region", "unknown"))


def location_map(loc: Location, zoom: int = 12) -> folium.Map:
    m = folium.Map(location=[loc.lat, loc.lon], zoom_start=zoom)
    folium.Marker([loc.lat, loc.lon], tooltip=f"Approximate location: {loc.city}, {loc.region}"
                  ).add_to(m)
    return m
