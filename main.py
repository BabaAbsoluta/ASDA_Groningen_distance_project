import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt

# Define place and tags for emergency care
place = "Groningen, The Netherlands"
tags = {'amenity': 'hospital'}

# Fetch and project the street network
G = ox.graph_from_place(place, network_type="drive")
G_proj = ox.project_graph(G)  # Project the graph to an appropriate CRS

# Fetch emergency care locations
emergency_care_gdf = ox.features_from_place(place, tags)

# Ensure the emergency care GeoDataFrame is in EPSG:4326
if emergency_care_gdf.crs is None:
    emergency_care_gdf.crs = 'EPSG:4326'
else:
    emergency_care_gdf = emergency_care_gdf.to_crs('EPSG:4326')

# Reproject emergency care locations to match the graph's CRS
emergency_care_gdf_proj = emergency_care_gdf.to_crs(G_proj.graph['crs'])

# Convert polygons to points by taking the centroid of each polygon
emergency_care_gdf_proj['geometry'] = emergency_care_gdf_proj.geometry.centroid

# Consolidate intersections
Gc = ox.consolidate_intersections(G_proj, dead_ends=True)

# Find the closest nodes in the graph for each emergency care location (now points)
closest_nodes = emergency_care_gdf_proj.geometry.apply(
    lambda point: ox.nearest_nodes(Gc, point.x, point.y)
)

# Convert the graph to GeoDataFrames for exploration
gdf_nodes, gdf_edges = ox.graph_to_gdfs(Gc, nodes=True, edges=True)

# Create an interactive map using GeoPandas' explore
# Use a built-in tile layer that does not require additional attribution
m = gdf_edges.explore(color='grey', tooltip=True, legend=True, tiles="OpenStreetMap")
gdf_nodes.explore(ax=m, color='blue', tooltip=True, legend=True)
emergency_care_gdf_proj.explore(ax=m, color='red', marker_kwds={'radius': 100})

# Save the interactive map to an HTML file
m.save("interactive_map.html")



