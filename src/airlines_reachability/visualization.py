import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import FancyArrowPatch
import pandas as pd
import networkx as nx


def plot_top_countries(
    data: pd.DataFrame,
    country_col: str,
    centrality_col: str,
    title: str,
    color: str,
    top_n: int = 15,
    figsize: tuple = (12, 8),
) -> None:
    top_data = data.head(top_n)
    plt.figure(figsize=figsize)
    bars = plt.bar(top_data[country_col], top_data[centrality_col], color=color)
    plt.xlabel("Country")
    plt.ylabel(centrality_col.replace("_", " ").title())
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    for bar in bars:
        height = bar.get_height()
        plt.annotate(
            f"{height:.4f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    plt.tight_layout()
    plt.show()


def _get_country_coords(airports: pd.DataFrame) -> dict[str, tuple[float, float]]:
    coords = airports.groupby("Country").agg({"Latitude": "mean", "Longitude": "mean"}).reset_index()
    result = {}
    for _, row in coords.iterrows():
        try:
            lat, lon = float(row["Latitude"]), float(row["Longitude"])
            result[row["Country"]] = (lat, lon)
        except (ValueError, TypeError):
            continue
    return result


def _get_airport_coords(airports: pd.DataFrame) -> dict[str, tuple[float, float]]:
    result = {}
    for _, row in airports.iterrows():
        if pd.notna(row["IATA"]) and pd.notna(row["Latitude"]) and pd.notna(row["Longitude"]):
            result[str(row["IATA"])] = (float(row["Latitude"]), float(row["Longitude"]))
    return result


def plot_path_on_map(
    path: list[str],
    coords: dict[str, tuple[float, float]],
    title: str,
    is_country: bool = True,
) -> None:
    if len(path) <= 1:
        return
    path_edges = list(zip(path, path[1:]))
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.set_global()

    for i, node in enumerate(path):
        if node in coords:
            lat, lon = coords[node]
            plt.plot(lon, lat, marker="o", color="red", markersize=5, transform=ccrs.PlateCarree())
            plt.text(
                lon + 1, lat + 1, f"{node}\n({i})",
                transform=ccrs.PlateCarree(),
                fontsize=8, ha="center", va="bottom",
            )

    for u, v in path_edges:
        if u in coords and v in coords:
            lat_u, lon_u = coords[u]
            lat_v, lon_v = coords[v]
            arrow = FancyArrowPatch(
                (lon_u, lat_u), (lon_v, lat_v),
                transform=ccrs.PlateCarree(),
                arrowstyle="->", color="blue", mutation_scale=15, linewidth=1,
            )
            ax.add_patch(arrow)

    plt.title(title)
    plt.show()


def plot_neighbors_on_map(
    G: nx.Graph,
    coords: dict[str, tuple[float, float]],
    title: str,
) -> None:
    """Plot a country subgraph on a world map."""
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.set_global()

    for node in G.nodes():
        if node in coords:
            lat, lon = coords[node]
            plt.plot(lon, lat, marker="o", color="red", markersize=5, transform=ccrs.PlateCarree())
            plt.text(lon + 1, lat + 1, node, transform=ccrs.PlateCarree(), fontsize=8)

    for u, v in G.edges():
        if u in coords and v in coords:
            lat_u, lon_u = coords[u]
            lat_v, lon_v = coords[v]
            plt.plot(
                [lon_u, lon_v], [lat_u, lat_v],
                color="blue", linewidth=1, transform=ccrs.PlateCarree(),
            )

    plt.title(title)
    plt.show()
