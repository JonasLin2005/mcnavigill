# Hackathon prototype (January 2025)

The routing, geolocation and graph files from the McWICS hackathon (January 2025), kept for
reference. The package in `../mcnavigill/` replaces them.

| File | What it is |
|---|---|
| `campus-graph-sketch.pdf` | The engineering quarter traced from the campus map: corridors and tunnels in blue, outdoor paths in green, numbered entrances and junctions. The rebuilt graph in `../mcnavigill/data/` is digitized from its right-hand panel. |
| `optimal.py` | Dijkstra's algorithm on a hand-entered graph with distance weights (metres). |
| `warmest.py` | The same search with outdoor-exposure scores as weights. |
| `GPS.py` | IP geolocation through ipinfo.io and a folium map of the result. |

What changed in the rebuild:

- The two routing scripts became one graph whose edges carry both a length and an outdoor
  length, and one Dijkstra that takes the objective as a parameter. The list scan for the
  next node became a binary heap, and a Pareto search was added for everything between the
  two extremes.
- `GPS.py` read the coordinates from `data['location']`; ipinfo returns them under `loc`,
  so the script always ended in its `except` branch. Fixed in `../mcnavigill/locate.py`.
- The hackathon graph used hand-entered weights. The rebuild measures every edge along its
  drawn path.
