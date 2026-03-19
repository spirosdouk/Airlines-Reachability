"""Centrality analysis and shortest path computation."""

import pandas as pd
import networkx as nx


def compute_centrality(G: nx.Graph) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute degree and closeness centrality. Returns (degree_df, closeness_df)."""
    degree_centrality = nx.degree_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    degree_df = pd.DataFrame(
        list(degree_centrality.items()),
        columns=["Country", "Degree_Centrality"],
    )
    closeness_df = pd.DataFrame(
        list(closeness_centrality.items()),
        columns=["Country", "Closeness_Centrality"],
    )
    return degree_df, closeness_df


def find_country_shortest_path(G: nx.Graph, source: str, target: str) -> list[str]:
    """Find shortest path between two countries. Returns path or empty list."""
    try:
        return nx.shortest_path(G, source=source, target=target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def find_airport_shortest_path(
    G: nx.Graph,
    airports: pd.DataFrame,
    source_country: str,
    target_country: str,
) -> list[str]:
    """Find shortest airport path between two countries. Returns best path or empty list."""
    source_airports = [
        ap
        for ap in airports[airports["Country"] == source_country]["IATA"].dropna().unique()
        if ap in G.nodes
    ]
    target_airports = [
        ap
        for ap in airports[airports["Country"] == target_country]["IATA"].dropna().unique()
        if ap in G.nodes
    ]
    if not source_airports or not target_airports:
        return []

    best_path = None
    best_length = float("inf")
    for s_ap in source_airports:
        for t_ap in target_airports:
            try:
                path = nx.shortest_path(G, source=s_ap, target=t_ap)
                if len(path) < best_length:
                    best_length = len(path)
                    best_path = path
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
    return best_path or []


def get_neighbors_within_hops(G: nx.Graph, source: str, hops: int) -> nx.Graph:
    """Return subgraph of nodes within hops of source."""
    paths = nx.single_source_shortest_path(G, source, cutoff=hops)
    edges = set()
    for path in paths.values():
        if len(path) >= 2:
            edges.update(zip(path, path[1:]))
    subgraph = nx.Graph()
    subgraph.add_edges_from(edges)
    return subgraph
