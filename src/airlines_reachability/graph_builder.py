import pandas as pd
import networkx as nx


def build_country_graph(routes: pd.DataFrame) -> nx.Graph:
    G = nx.Graph()
    for _, row in routes.iterrows():
        source_country = row["Country_source"]
        dest_country = row["Country_dest"]
        stops = row["Stops"]
        if pd.notna(source_country) and pd.notna(dest_country) and source_country != dest_country:
            G.add_edge(source_country, dest_country, stops=stops if pd.notna(stops) else 0)
    return G


def build_airport_graph(routes: pd.DataFrame) -> nx.Graph:
    G = nx.Graph()
    for _, row in routes.iterrows():
        source_ap = row["Source_airport"]
        dest_ap = row["Destination_airport"]
        stops = row["Stops"]
        if pd.notna(source_ap) and pd.notna(dest_ap):
            G.add_edge(source_ap, dest_ap, stops=stops if pd.notna(stops) else 0)
    return G
