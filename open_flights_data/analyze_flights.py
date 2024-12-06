import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import FancyArrowPatch

script_dir = os.path.dirname(os.path.abspath(__file__))
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

# Load Data

try:
    routes = pd.read_csv(routes_file, header=0, names=routes_columns, encoding='latin1')
    print("Routes Data:")
    print(routes.head())
except FileNotFoundError:
    print(f"Error: {routes_file} not found.")
    exit()

try:
    airlines = pd.read_csv(airlines_file, header=None, names=airlines_columns, encoding='latin1')
    print("\nAirlines Data:")
    print(airlines.head())
except FileNotFoundError:
    print(f"Error: {airlines_file} not found.")
    exit()

try:
    airports = pd.read_csv(airports_file, header=None, names=airports_columns, encoding='latin1')
    print("\nAirports Data:")
    print(airports.head())
except FileNotFoundError:
    print(f"Error: {airports_file} not found.")
    exit()

# Data Cleaning: Replace '\\N' with NaN for better handling
routes.replace('\\N', pd.NA, inplace=True)
airlines.replace('\\N', pd.NA, inplace=True)
airports.replace('\\N', pd.NA, inplace=True)
routes['Stops'] = pd.to_numeric(routes['Stops'], errors='coerce')

routes['Airline'] = routes['Airline'].astype(str)
airlines['IATA'] = airlines['IATA'].astype(str)
routes['Source_airport'] = routes['Source_airport'].astype(str)
routes['Destination_airport'] = routes['Destination_airport'].astype(str)

# Merge routes with airlines on IATA codes
routes = routes.merge(
    airlines[['IATA', 'Name', 'Country']],
    left_on='Airline', right_on='IATA',
    how='left',
    suffixes=('', '_airline')
)

routes = routes.merge(
    airports[['IATA', 'Country', 'Latitude', 'Longitude']],
    left_on='Source_airport', right_on='IATA',
    how='left',
    suffixes=('', '_source')
)

routes = routes.merge(
    airports[['IATA', 'Country', 'Latitude', 'Longitude']],
    left_on='Destination_airport', right_on='IATA',
    how='left',
    suffixes=('', '_dest')
)
print("\nMerged Routes Data:")
print(routes.head())

G = nx.DiGraph()

for index, row in routes.iterrows():
    source_country = row['Country_source']
    dest_country = row['Country_dest']
    stops = row['Stops']
    
    # Ensure both source and destination countries are not missing
    if pd.notna(source_country) and pd.notna(dest_country):
        # Avoid routes within the same country
        if source_country != dest_country:
            # Add an edge from source_country to dest_country with 'stops' as weight
            if G.has_edge(source_country, dest_country):
                G[source_country][dest_country]['stops'] += stops
            else:
                G.add_edge(source_country, dest_country, stops=stops)

print("\nGraph Information:")
print("Number of nodes:", G.number_of_nodes())
print("Number of edges:", G.number_of_edges())

# ------------------------------------------------------------------------------------
degree_centrality = nx.degree_centrality(G)
degree_df = pd.DataFrame(list(degree_centrality.items()), columns=['Country', 'Degree_Centrality'])

# Sort by Degree Centrality in ascending order to find least connected countries
degree_df_sorted = degree_df.sort_values(by='Degree_Centrality', ascending=True)

print("\nTop 10 Most Antisocial Countries (Least Connected):")
print(degree_df_sorted.head(10))

closeness_centrality = nx.closeness_centrality(G)
closeness_df = pd.DataFrame(list(closeness_centrality.items()), columns=['Country', 'Closeness_Centrality'])

# Sort by Closeness Centrality in descending order to find most accessible countries
closeness_df_sorted = closeness_df.sort_values(by='Closeness_Centrality', ascending=False)
from matplotlib.patches import FancyArrowPatch

print("\nTop 10 Most Accessible Countries:")
print(closeness_df_sorted.head(10))

# ------------------------------------------------------------------------------------
source_country = 'United States'
target_country = 'North Korea'

try:
    shortest_path = nx.shortest_path(G, source=source_country, target=target_country, weight='stops')
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
    exit()

# Compute country coordinates
country_coords = airports.groupby('Country').agg({'Latitude': 'mean', 'Longitude': 'mean'}).reset_index()
country_coords_dict = {row['Country']: (row['Latitude'], row['Longitude']) for _, row in country_coords.iterrows()}

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
        plt.text(lon+1, lat+1, f"{country}\n({i})", transform=ccrs.PlateCarree(), fontsize=8, ha='center', va='bottom')

# Plot directed edges 
for u, v in path_edges:
    if u in country_coords_dict and v in country_coords_dict:
        lat_u, lon_u = country_coords_dict[u]
        lat_v, lon_v = country_coords_dict[v]
        
        arrow = FancyArrowPatch((lon_u, lat_u), (lon_v, lat_v),
                                transform=ccrs.PlateCarree(),
                                arrowstyle='->', color='blue', mutation_scale=15, linewidth=1)
        ax.add_patch(arrow)

plt.title(f"Directed Shortest Path from {source_country} to {target_country}")
plt.show()

top_antisocial = degree_df_sorted.head(30)

plt.figure(figsize=(10, 6))
plt.bar(top_antisocial['Country'], top_antisocial['Degree_Centrality'], color='salmon')
plt.xlabel('Country')
plt.ylabel('Degree Centrality')
plt.title('Top 10 Most Antisocial Countries by Direct Airline Connections')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

top_accessible = closeness_df_sorted.head(30)

plt.figure(figsize=(10, 6))
plt.bar(top_accessible['Country'], top_accessible['Closeness_Centrality'], color='skyblue')
plt.xlabel('Country')
plt.ylabel('Closeness Centrality')
plt.title('Top 10 Most Accessible Countries by Closeness Centrality')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# ------------------------------------------------------------------------------------
most_unpopular_country = degree_df_sorted.iloc[23]['Country']
most_unpopular_country = degree_df_sorted.iloc[1]['Country']

print(f"\nMost Unpopular Country: {most_unpopular_country}")

## Find all countries within 2 hops from the most unpopular country
hops = 2
neighbors_within_2_hops = nx.single_source_shortest_path(G, most_unpopular_country, cutoff=hops)

# Extract edges that are part of the shortest paths
edges_in_shortest_paths = set()
for target in neighbors_within_2_hops:
    path = neighbors_within_2_hops[target]
    edges_in_path = list(zip(path, path[1:]))
    edges_in_shortest_paths.update(edges_in_path)

# Create the subgraph using only the edges
simplified_subgraph = nx.DiGraph()
simplified_subgraph.add_edges_from(edges_in_shortest_paths)


# ------------------------------------------------------------------------------------
# latitude and longitude of all airports in that country for the mapping.
country_coords = airports.groupby('Country').agg({'Latitude': 'mean', 'Longitude': 'mean'}).reset_index()
country_coords_dict = {row['Country']: (row['Latitude'], row['Longitude']) for _, row in country_coords.iterrows()}

plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.set_global()

# Plot each node (country) on the map if we have coordinates
for country in simplified_subgraph.nodes():
    if country in country_coords_dict:
        lat, lon = country_coords_dict[country]
        plt.plot(lon, lat, marker='o', color='red', markersize=5, transform=ccrs.PlateCarree())
        plt.text(lon+1, lat+1, country, transform=ccrs.PlateCarree(), fontsize=8)

# Plot edges
for u, v in simplified_subgraph.edges():
    if u in country_coords_dict and v in country_coords_dict:
        lat_u, lon_u = country_coords_dict[u]
        lat_v, lon_v = country_coords_dict[v]
        plt.plot([lon_u, lon_v], [lat_u, lat_v], color='blue', linewidth=1, transform=ccrs.PlateCarree())

plt.title(f"Neighbors within {hops} hops of {most_unpopular_country} on a World Map")
plt.show()