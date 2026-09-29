"""McNavigill: winter routing across McGill's engineering quarter."""

from .graph import CampusGraph, Edge, Node
from .routing import NoRoute, Route, dijkstra, pareto_routes

__all__ = ["CampusGraph", "Edge", "Node", "NoRoute", "Route", "dijkstra", "pareto_routes"]
__version__ = "0.2.0"
