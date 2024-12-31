import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
import sys
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import FancyArrowPatch
import csv 

def get_script_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()

script_dir = get_script_dir()
data_dir = script_dir 

routes_file = os.path.join(data_dir, 'routes.csv')
airlines_file = os.path.join(data_dir, 'airlines.dat')
airports_file = os.path.join(data_dir, 'airports.dat')

routes_columns = [
    'Airline', 'Airline_ID', 'Source_airport', 'Source_airport_ID',
    'Destination_airport', 'Destination_airport_ID', 'Codeshare',
    'Stops', 'Equipment'
]

airlines_columns = [
    'Airline_ID', 'Name', 'Alias', 'IATA', 'ICAO', 'Callsign',
    'Country', 'Active'
]

airports_columns = [
    'Airport_ID', 'Name', 'City', 'Country', 'IATA', 'ICAO',
    'Latitude', 'Longitude', 'Altitude', 'Timezone', 'DST',
    'Tz', 'Type', 'Source'
]

def read_data(file_path, columns, file_type='csv'):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        sys.exit(1)
    try:
        if file_type == 'csv':
            df = pd.read_csv(file_path, header=0, names=columns, encoding='latin1')
        elif file_type == 'dat':
            df = pd.read_csv(
                file_path,
                header=None,
                names=columns,
                encoding='latin1',
                delimiter=',',
                engine='python',
                quoting=csv.QUOTE_MINIMAL,
                quotechar='"',
                na_values=['\\N'],
                keep_default_na=False,
                dtype=str
            )
        else:
            raise ValueError("Unsupported file type.")
        print(f"Loaded {file_path} successfully.")
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit(1)

# Load Data
routes = read_data(routes_file, routes_columns, file_type='csv')
print("\nRoutes Data:")
print(routes.head())

airlines = read_data(airlines_file, airlines_columns, file_type='dat')
print("\nAirlines Data:")
print(airlines.head())

airports = read_data(airports_file, airports_columns, file_type='dat')
print("\nAirports Data:")
print(airports.head())

# Data Cleaning: Replace '\\N' with NaN for better handling
routes.replace('\\N', pd.NA, inplace=True)
airlines.replace('\\N', pd.NA, inplace=True)
airports.replace('\\N', pd.NA, inplace=True)

routes['Stops'] = pd.to_numeric(routes['Stops'], errors='coerce')
routes['Airline'] = routes['Airline'].astype(str)
airlines['IATA'] = airlines['IATA'].astype(str)
routes['Source_airport'] = routes['Source_airport'].astype(str)
routes['Destination_airport'] = routes['Destination_airport'].astype(str)

airports['Latitude'] = pd.to_numeric(airports['Latitude'], errors='coerce')
airports['Longitude'] = pd.to_numeric(airports['Longitude'], errors='coerce')

# Merge routes with airlines on IATA codes
routes = routes.merge(
    airlines[['IATA', 'Name', 'Country']],
    left_on='Airline', right_on='IATA',
    how='left',
    suffixes=('', '_airline')
)

# Merge routes with airports for Source
routes = routes.merge(
    airports[['IATA', 'Country', 'Latitude', 'Longitude']],
    left_on='Source_airport', right_on='IATA',
    how='left',
    suffixes=('', '_source')
)

# Merge routes with airports for Destination
routes = routes.merge(
    airports[['IATA', 'Country', 'Latitude', 'Longitude']],
    left_on='Destination_airport', right_on='IATA',
    how='left',
    suffixes=('', '_dest')
)

print("\nMerged Routes Data:")
print(routes.head())

# Initialize an undirected graph
G = nx.Graph()

for index, row in routes.iterrows():
    source_country = row['Country_source']
    dest_country = row['Country_dest']
    stops = row['Stops']
    
    if pd.notna(source_country) and pd.notna(dest_country):
        # Avoid routes within the same country
        if source_country != dest_country:
            # Since it's an undirected graph, multiple routes between the same countries are treated as a single connection
            G.add_edge(source_country, dest_country, stops=stops if pd.notna(stops) else 0)

print("\nGraph Information:")
print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")

# Calculate Degree Centrality
degree_centrality = nx.degree_centrality(G)
degree_df = pd.DataFrame(list(degree_centrality.items()), columns=['Country', 'Degree_Centrality'])

# Calculate Closeness Centrality
closeness_centrality = nx.closeness_centrality(G)
closeness_df = pd.DataFrame(list(closeness_centrality.items()), columns=['Country', 'Closeness_Centrality'])

closeness_least_accessible = closeness_df.sort_values(by='Closeness_Centrality', ascending=True)
closeness_most_accessible = closeness_df.sort_values(by='Closeness_Centrality', ascending=False)

degree_least_accessible = degree_df.sort_values(by='Degree_Centrality', ascending=True)
degree_most_accessible = degree_df.sort_values(by='Degree_Centrality', ascending=False)

top_least_accessible_closeness = closeness_least_accessible.head(15)
top_most_accessible_closeness = closeness_most_accessible.head(15)

top_least_accessible_degree = degree_least_accessible.head(15)
top_most_accessible_degree = degree_most_accessible.head(15)

def plot_top_countries(data, country_col, centrality_col, title, color, top_n, figsize=(12, 8)):
    """
    Plots a bar chart for the top N countries based on a centrality measure.

    Parameters:
    - data (DataFrame): The data containing countries and their centrality measures.
    - country_col (str): The column name for countries.
    - centrality_col (str): The column name for centrality measures.
    - title (str): The title of the plot.
    - color (str): The color of the bars.
    - top_n (int): The number of top items to display.
    - figsize (tuple): The size of the figure.
    """
    top_data = data.head(top_n)
    
    plt.figure(figsize=figsize)
    bars = plt.bar(top_data[country_col], top_data[centrality_col], color=color)
    plt.xlabel('Country')
    plt.ylabel(centrality_col.replace('_', ' ').title())
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    
    # Add data labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.4f}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3),
                     textcoords="offset points",
                     ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.show()


plot_top_countries(
    data=top_least_accessible_closeness,
    country_col='Country',
    centrality_col='Closeness_Centrality',
    title='Top 15 Least Accessible Countries by Closeness Centrality',
    color='lightcoral',
    top_n=20
)

plot_top_countries(
    data=top_most_accessible_closeness,
    country_col='Country',
    centrality_col='Closeness_Centrality',
    title='Top 15 Most Accessible Countries by Closeness Centrality',
    color='steelblue',
    top_n=15
)

plot_top_countries(
    data=top_least_accessible_degree,
    country_col='Country',
    centrality_col='Degree_Centrality',
    title='Top 15 Least Accessible Countries by Degree Centrality',
    color='salmon',
    top_n=15
)

plot_top_countries(
    data=top_most_accessible_degree,
    country_col='Country',
    centrality_col='Degree_Centrality',
    title='Top 15 Most Accessible Countries by Degree Centrality',
    color='mediumseagreen',
    top_n=15
)

# ------------------------------------------------------------------------------------
# Find the shortest path from Greece to 'Cocos (Keeling) Islands'
source_country = 'Greece'
target_country = 'Cocos (Keeling) Islands'

try:
    shortest_path = nx.shortest_path(G, source=source_country, target=target_country)
    path_length = len(shortest_path) - 1
    print(f"\nShortest path from {source_country} to {target_country}: {' -> '.join(shortest_path)}")
    print(f"Number of hops: {path_length}")
except nx.NetworkXNoPath:
    print(f"\nNo available path from {source_country} to {target_country}.")
    shortest_path = []
except nx.NodeNotFound as e:
    print(f"\nError: {e}")
    shortest_path = []

if len(shortest_path) <= 1:
    print("No path to plot.")
else:
    # Compute country coordinates
    country_coords = airports.groupby('Country').agg({'Latitude': 'mean', 'Longitude': 'mean'}).reset_index()
    country_coords_dict = {}
    for _, row in country_coords.iterrows():
        country = row['Country']
        try:
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            country_coords_dict[country] = (lat, lon)
        except (ValueError, TypeError):
            continue
    
    path_edges = list(zip(shortest_path, shortest_path[1:]))
    
    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.set_global()
    
    # Plot nodes and add a number above them
    for i, country in enumerate(shortest_path):
        if country in country_coords_dict:
            lat, lon = country_coords_dict[country]
            plt.plot(lon, lat, marker='o', color='red', markersize=5, transform=ccrs.PlateCarree())
            plt.text(lon + 1, lat + 1, f"{country}\n({i})", transform=ccrs.PlateCarree(),
                     fontsize=8, ha='center', va='bottom')
    
    # Plot directed edges 
    for u, v in path_edges:
        if u in country_coords_dict and v in country_coords_dict:
            lat_u, lon_u = country_coords_dict[u]
            lat_v, lon_v = country_coords_dict[v]
            
            arrow = FancyArrowPatch((lon_u, lat_u), (lon_v, lat_v),
                                    transform=ccrs.PlateCarree(),
                                    arrowstyle='->', color='blue', mutation_scale=15, linewidth=1)
            ax.add_patch(arrow)
    
    plt.title(f"Shortest Path from {source_country} to {target_country}")
    plt.show()

# --------------------------------------------------------------------------
# 3) AIRPORT-TO-AIRPORT GRAPH
G_airports = nx.Graph()

# Build the airport graph from "routes"
for _, row in routes.iterrows():
    source_ap = row['Source_airport']
    dest_ap   = row['Destination_airport']
    stops     = row['Stops']
    if pd.notna(source_ap) and pd.notna(dest_ap):
        G_airports.add_edge(
            source_ap, 
            dest_ap, 
            stops=stops if pd.notna(stops) else 0
        )

print("\nAirport Graph Information:")
print(f"Number of airport nodes: {G_airports.number_of_nodes()}")
print(f"Number of airport edges: {G_airports.number_of_edges()}")

source_country = "Greece"
target_country = "Cocos (Keeling) Islands"
 
# Gather all IATA codes 
# filter so we only keep those that are actually in the G_airports graph.
source_country_airports = [
    ap for ap in airports[airports['Country'] == source_country]['IATA'].dropna().unique()
    if ap in G_airports.nodes
]
target_country_airports = [
    ap for ap in airports[airports['Country'] == target_country]['IATA'].dropna().unique()
    if ap in G_airports.nodes
]

print(f"\nValid airports in '{source_country}': {source_country_airports}")
print(f"Valid airports in '{target_country}': {target_country_airports}")

# If no valid airports found, skip
if len(source_country_airports) == 0 or len(target_country_airports) == 0:
    print(f"No valid airports found for {source_country} or {target_country} in the graph.")
    best_path = []
else:
    best_path = None
    best_length = float('inf')

    for s_ap in source_country_airports:
        for t_ap in target_country_airports:
            try:
                path = nx.shortest_path(G_airports, source=s_ap, target=t_ap)
                if len(path) < best_length:
                    best_length = len(path)
                    best_path = path
            except nx.NetworkXNoPath:
                continue
            except nx.NodeNotFound:
                continue

    if best_path is None:
        print(f"No connecting route found between airports of {source_country} and {target_country}.")
        best_path = []
    else:
        # best minimal-hop path
        path_length = len(best_path) - 1
        print(f"\nBest (shortest) airport-to-airport path from {source_country} to {target_country}:")
        print(" -> ".join(best_path))
        print(f"Number of hops: {path_length}")

if len(best_path) <= 1:
    print("No path to plot (or only a single node).")
else:
    airport_coords_dict = {}
    for _, row in airports.iterrows():
        iata = row['IATA']
        lat  = row['Latitude']
        lon  = row['Longitude']
        if pd.notna(iata) and pd.notna(lat) and pd.notna(lon):
            airport_coords_dict[iata] = (lat, lon)

    path_edges = list(zip(best_path, best_path[1:]))

    plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.set_global()

    # Plot each airport in the path
    for i, ap in enumerate(best_path):
        if ap in airport_coords_dict:
            lat, lon = airport_coords_dict[ap]
            plt.plot(
                lon, lat, 
                marker='o', color='red', markersize=5, 
                transform=ccrs.PlateCarree()
            )
            plt.text(
                lon + 1, lat + 1, f"{ap}\n({i})",
                transform=ccrs.PlateCarree(),
                fontsize=8, ha='center', va='bottom'
            )

    # Plot edges as arrows
    for u, v in path_edges:
        if u in airport_coords_dict and v in airport_coords_dict:
            lat_u, lon_u = airport_coords_dict[u]
            lat_v, lon_v = airport_coords_dict[v]
            arrow = FancyArrowPatch(
                (lon_u, lat_u), (lon_v, lat_v),
                transform=ccrs.PlateCarree(),
                arrowstyle='->', color='blue',
                mutation_scale=15, linewidth=1
            )
            ax.add_patch(arrow)

    plt.title(f"Shortest Airport-to-Airport Path: {source_country} -> {target_country}")
    plt.show()



# -----------------------------------------------------------------------------
# 4) NEIGHBORS OF A SELECTED COUNTRY (HERE BASED ON DEGREE CENTRALITY)
degree_df_sorted_asc = degree_df.sort_values(by='Degree_Centrality', ascending=True)

most_unpopular_country = degree_df_sorted_asc.iloc[1]['Country']
print(f"\nMost Unpopular Country: {most_unpopular_country}")

hops = 2
neighbors_within_hops = nx.single_source_shortest_path(G, most_unpopular_country, cutoff=hops)

edges_in_shortest_paths = set()
for target, path in neighbors_within_hops.items():
    if len(path) >= 2:
        edges_in_path = list(zip(path, path[1:]))
        edges_in_shortest_paths.update(edges_in_path)

simplified_subgraph = nx.Graph()
simplified_subgraph.add_edges_from(edges_in_shortest_paths)

country_coords = airports.groupby('Country').agg({'Latitude': 'mean', 'Longitude': 'mean'}).reset_index()
country_coords_dict = {}
for _, row in country_coords.iterrows():
    country = row['Country']
    try:
        lat = float(row['Latitude'])
        lon = float(row['Longitude'])
        country_coords_dict[country] = (lat, lon)
    except (ValueError, TypeError):
        continue

plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.set_global()

# Plot each country on the map if we have coordinates
for country in simplified_subgraph.nodes():
    if country in country_coords_dict:
        lat, lon = country_coords_dict[country]
        plt.plot(lon, lat, marker='o', color='red', markersize=5, transform=ccrs.PlateCarree())
        plt.text(lon + 1, lat + 1, country, transform=ccrs.PlateCarree(), fontsize=8)

for u, v in simplified_subgraph.edges():
    if u in country_coords_dict and v in country_coords_dict:
        lat_u, lon_u = country_coords_dict[u]
        lat_v, lon_v = country_coords_dict[v]
        plt.plot([lon_u, lon_v], [lat_u, lat_v], color='blue', linewidth=1, transform=ccrs.PlateCarree())

plt.title(f"Neighbors within {hops} hop(s) of {most_unpopular_country} on a World Map")
plt.show()
