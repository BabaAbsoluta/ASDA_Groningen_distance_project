import osmnx as ox
import geopandas as gpd
import folium
import matplotlib.pyplot as plt

# Define place and tags for emergency care
place = "Groningen, The Netherlands"
tags = {'amenity': 'hospital'}

# Fetch and project the street network
print("Fetching the street network...")
G = ox.graph_from_place(place, network_type="drive")
print("Projecting the graph...")
G_proj = ox.project_graph(G)  # Project the graph to an appropriate CRS

# Fetch emergency care locations
print("Fetching emergency care locations...")
emergency_care_gdf = ox.features_from_place(place, tags)

# Ensure the emergency care GeoDataFrame has the correct CRS
print("Ensuring CRS for emergency care GeoDataFrame...")
emergency_care_gdf = gpd.GeoDataFrame(emergency_care_gdf, crs="EPSG:4326")

# Convert the network graph to GeoDataFrames
print("Converting network graph to GeoDataFrames...")
nodes, edges = ox.graph_to_gdfs(G_proj, nodes=True, edges=True)

# Check and set CRS for nodes and edges
print("Checking and setting CRS for nodes and edges GeoDataFrames...")
if nodes.crs is None:
    print("Nodes GeoDataFrame has no CRS. Setting CRS to EPSG:4326...")
    nodes.set_crs(epsg=4326, allow_override=True, inplace=True)
else:
    print(f"Nodes CRS: {nodes.crs}")
    print("Reprojecting nodes GeoDataFrame to EPSG:4326...")
    nodes = nodes.to_crs(epsg=4326)

if edges.crs is None:
    print("Edges GeoDataFrame has no CRS. Setting CRS to EPSG:4326...")
    edges.set_crs(epsg=4326, allow_override=True, inplace=True)
else:
    print(f"Edges CRS: {edges.crs}")
    print("Reprojecting edges GeoDataFrame to EPSG:4326...")
    edges = edges.to_crs(epsg=4326)

# Create a Folium map centered on Groningen
print("Creating Folium map...")
m = folium.Map(location=[53.2194, 6.5665], zoom_start=13)

# Add nodes to the map
print("Adding nodes to the map...")
for idx, row in nodes.iterrows():
    folium.Marker([row.geometry.y, row.geometry.x],
                   popup=f"Node {row.name}",
                   icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)

# Add edges to the map
print("Adding edges to the map...")
for idx, row in edges.iterrows():
    coords = list(row.geometry.coords)
    folium.PolyLine(coords, color="gray", weight=2.5, opacity=0.6).add_to(m)

# Add emergency care locations to the map
print("Adding emergency care locations to the map...")
for idx, row in emergency_care_gdf.iterrows():
    if row.geometry.geom_type == 'Point':
        folium.Marker([row.geometry.y, row.geometry.x],
                      popup=f"Hospital: {row['name']}",
                      icon=folium.Icon(color='red', icon='plus')).add_to(m)
    elif row.geometry.geom_type == 'Polygon':
        # Use the centroid of the polygon for display
        centroid = row.geometry.centroid
        folium.Marker([centroid.y, centroid.x],
                      popup=f"Hospital: {row['name']}",
                      icon=folium.Icon(color='red', icon='plus')).add_to(m)
    else:
        print(f"Unsupported geometry type: {row.geometry.geom_type}")

# Save the map to an HTML file
print("Saving the map to an HTML file...")
m.save("groningen_map.html")
print("Map saved as groningen_map.html")

# Optional: Display the map with matplotlib (not interactive)
print("Displaying the map with matplotlib...")
fig, ax = plt.subplots(figsize=(10, 10))
edges.plot(ax=ax, linewidth=1, edgecolor='gray')
nodes.plot(ax=ax, markersize=5, color='blue', label='Nodes')
emergency_care_gdf.plot(ax=ax, markersize=20, color='red', label='Hospitals')
plt.show()








