import osmnx as ox
import networkx as nx
import folium
import random

# Define place and tags for emergency care
place = "Groningen, The Netherlands"
tags = {'amenity': 'hospital'}

# Fetch the street network (projected to UTM)
G = ox.graph_from_place(place, network_type="drive")
G_proj = ox.project_graph(G)  # Automatically project graph to UTM

# Add edge lengths and speed estimates to the graph
G_proj = ox.speed.add_edge_speeds(G_proj)  # Add speed_kph to edges
G_proj = ox.speed.add_edge_travel_times(G_proj)  # Add travel time based on speed and length

# Fetch emergency care locations (hospitals)
emergency_care_gdf = ox.features_from_place(place, tags)

# Ensure the emergency care GeoDataFrame is in EPSG:4326 (folium requires lat/lon)
if emergency_care_gdf.crs is None:
    emergency_care_gdf.crs = 'EPSG:4326'
else:
    emergency_care_gdf = emergency_care_gdf.to_crs('EPSG:4326')

# Project the hospitals to the same CRS as the street network graph for accurate distance calculations
emergency_care_gdf_proj = emergency_care_gdf.to_crs(G_proj.graph['crs'])

# Convert hospital polygons to centroids (if any polygons are present)
if emergency_care_gdf_proj.geom_type.isin(['Polygon', 'MultiPolygon']).any():
    emergency_care_gdf_proj['geometry'] = emergency_care_gdf_proj.centroid

# Find the closest nodes in the road network for each hospital location
hospital_nodes = emergency_care_gdf_proj['geometry'].apply(lambda point: ox.nearest_nodes(G_proj, point.x, point.y))

# Convert the OSMnx graph to GeoDataFrames for the nodes and edges
gdf_nodes, gdf_edges = ox.graph_to_gdfs(G_proj, nodes=True, edges=True)

# Reproject the nodes and edges back to EPSG:4326 for folium mapping (latitude/longitude)
gdf_nodes = gdf_nodes.to_crs(epsg=4326)
gdf_edges = gdf_edges.to_crs(epsg=4326)

# The rest of the code (rendering the map, calculating distances, etc.) remains the same


# Limit the number of nodes (randomly sample a subset of nodes for faster rendering)
num_nodes_to_display = 100  # Set the number of nodes to display
gdf_nodes_sampled = gdf_nodes.sample(n=num_nodes_to_display, random_state=42)


# Function to calculate the driving distance and travel time
# Function to calculate the driving distance and travel time
def calculate_driving_distance_and_time(node_id):
    min_distance = float('inf')
    min_time = float('inf')
    nearest_hospital_node = None

    # Iterate through hospital nodes and calculate shortest path to each hospital
    for hospital_node in hospital_nodes:
        # Skip if the hospital node is the same as the node being checked
        if node_id == hospital_node:
            continue

        try:
            # Calculate the shortest path by driving distance (length)
            distance = nx.shortest_path_length(G_proj, node_id, hospital_node, weight='length')

            # Calculate the shortest path by travel time
            time = nx.shortest_path_length(G_proj, node_id, hospital_node, weight='travel_time')

            if distance < min_distance:
                min_distance = distance
                min_time = time
                nearest_hospital_node = hospital_node
        except nx.NetworkXNoPath:
            continue

    # Return the minimum distance and time
    if min_distance == float('inf') or min_time == float('inf'):
        print(f"No valid path found for node {node_id}")
        return 0, 0
    else:
        print(
            f"Node {node_id}: Nearest hospital at node {nearest_hospital_node} - Distance: {min_distance} meters, Time: {min_time} hours")

    return min_distance, min_time


# Initialize the folium map centered on the average node location
m = folium.Map(location=[gdf_nodes.geometry.y.mean(), gdf_nodes.geometry.x.mean()], zoom_start=13)

# Add street network edges to the map
for _, row in gdf_edges.iterrows():
    folium.PolyLine(
        locations=[(point[1], point[0]) for point in row['geometry'].coords],  # Lat, Lon order
        color='grey',
        weight=2
    ).add_to(m)

# Convert hospital polygons to centroids (if any polygons are present)
if emergency_care_gdf.geom_type.isin(['Polygon', 'MultiPolygon']).any():
    emergency_care_gdf['geometry'] = emergency_care_gdf.centroid

# Add hospitals to the map as red markers
for _, row in emergency_care_gdf.iterrows():
    folium.CircleMarker(
        location=(row.geometry.y, row.geometry.x),
        radius=8,
        color='red',
        fill=True,
        fill_opacity=0.9,
        tooltip=row['name'] if 'name' in row else "Hospital"
    ).add_to(m)


# Function to handle node clicks and show driving distance and time to the nearest hospital
def on_node_click(lat, lon):
    # Find the nearest node in the road network
    node_id = ox.nearest_nodes(G_proj, lon, lat)

    # Calculate driving distance and travel time to the nearest hospital
    distance, time = calculate_driving_distance_and_time(node_id)

    # Convert time to minutes
    time_in_minutes = time * 60

    # Return the driving distance and travel time in a formatted string
    return f"Driving distance: {distance:.2f} meters\nTravel time: {time_in_minutes:.2f} minutes"


# Add clickable nodes to the map with popup showing driving distance and travel time
for _, row in gdf_nodes_sampled.iterrows():
    lat = row.geometry.y
    lon = row.geometry.x

    # Add each node with a click event that shows the driving distance and travel time
    folium.Marker(
        location=(lat, lon),
        icon=folium.Icon(color='blue', icon='info-sign'),
        popup=folium.Popup(on_node_click(lat, lon), max_width=250)
    ).add_to(m)

# Save the interactive map to an HTML file
m.save("interactive_map_with_limited_nodes_and_debugging.html")
