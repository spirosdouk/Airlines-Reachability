"""Main entry point: load data, build graphs, analyze, visualize."""

from .analysis import (
    compute_centrality,
    find_airport_shortest_path,
    find_country_shortest_path,
    get_neighbors_within_hops,
)
from .data_loader import load_and_merge_data
from .graph_builder import build_airport_graph, build_country_graph
from .visualization import (
    _get_airport_coords,
    _get_country_coords,
    plot_neighbors_on_map,
    plot_path_on_map,
    plot_top_countries,
)


def main() -> None:
    routes, airlines, airports = load_and_merge_data()
    print("\nMerged Routes Data:")
    print(routes.head())

    # 1) Country graph
    G = build_country_graph(routes)
    print("\nGraph Information:")
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")

    # 2) Centrality
    degree_df, closeness_df = compute_centrality(G)
    closeness_least = closeness_df.sort_values("Closeness_Centrality", ascending=True).head(15)
    closeness_most = closeness_df.sort_values("Closeness_Centrality", ascending=False).head(15)
    degree_least = degree_df.sort_values("Degree_Centrality", ascending=True).head(15)
    degree_most = degree_df.sort_values("Degree_Centrality", ascending=False).head(15)

    plot_top_countries(
        closeness_least, "Country", "Closeness_Centrality",
        "Top 15 Least Accessible Countries by Closeness Centrality",
        "lightcoral", 20,
    )
    plot_top_countries(
        closeness_most, "Country", "Closeness_Centrality",
        "Top 15 Most Accessible Countries by Closeness Centrality",
        "steelblue", 15,
    )
    plot_top_countries(
        degree_least, "Country", "Degree_Centrality",
        "Top 15 Least Accessible Countries by Degree Centrality",
        "salmon", 15,
    )
    plot_top_countries(
        degree_most, "Country", "Degree_Centrality",
        "Top 15 Most Accessible Countries by Degree Centrality",
        "mediumseagreen", 15,
    )

    # 3) Shortest path (country level)
    source_country = "Greece"
    target_country = "Cocos (Keeling) Islands"
    shortest_path = find_country_shortest_path(G, source_country, target_country)

    if shortest_path:
        print(f"\nShortest path from {source_country} to {target_country}: {' -> '.join(shortest_path)}")
        print(f"Number of hops: {len(shortest_path) - 1}")
        country_coords = _get_country_coords(airports)
        plot_path_on_map(
            shortest_path, country_coords,
            f"Shortest Path from {source_country} to {target_country}",
            is_country=True,
        )
    else:
        print(f"\nNo available path from {source_country} to {target_country}.")

    # 4) Airport graph
    G_airports = build_airport_graph(routes)
    print("\nAirport Graph Information:")
    print(f"Number of airport nodes: {G_airports.number_of_nodes()}")
    print(f"Number of airport edges: {G_airports.number_of_edges()}")

    best_path = find_airport_shortest_path(G_airports, airports, source_country, target_country)
    if best_path:
        print(f"\nBest airport path from {source_country} to {target_country}:")
        print(" -> ".join(best_path))
        print(f"Number of hops: {len(best_path) - 1}")
        airport_coords = _get_airport_coords(airports)
        plot_path_on_map(
            best_path, airport_coords,
            f"Shortest Airport-to-Airport Path: {source_country} -> {target_country}",
            is_country=False,
        )
    else:
        print(f"No connecting route between airports of {source_country} and {target_country}.")

    # 5) Neighbors of least accessible country
    degree_sorted = degree_df.sort_values("Degree_Centrality", ascending=True)
    most_unpopular = degree_sorted.iloc[1]["Country"]
    print(f"\nMost Unpopular Country: {most_unpopular}")

    hops = 2
    subgraph = get_neighbors_within_hops(G, most_unpopular, hops)
    country_coords = _get_country_coords(airports)
    plot_neighbors_on_map(
        subgraph, country_coords,
        f"Neighbors within {hops} hop(s) of {most_unpopular} on a World Map",
    )


if __name__ == "__main__":
    main()
