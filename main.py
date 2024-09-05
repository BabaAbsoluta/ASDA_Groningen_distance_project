import osmnx as ox
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
emergency_care_gdf_proj = emergency_care_gdf.to_crs(ox.project_graph(G).graph['crs'])

# Consolidate intersections
Gc = ox.consolidate_intersections(G_proj, dead_ends=True)

# Plot the graph
fig, ax = ox.plot_graph(
    Gc,
    figsize=(10, 10),
    edge_linewidth=1,
    edge_color="c",
    node_size=5,
    node_color="#222222",
    node_edgecolor="c",
    show=False,
    close=False
)

# Plot the emergency care locations with enhanced visibility
emergency_care_gdf_proj.plot(ax=ax, color='red', marker='o', markersize=50, label='Emergency Care')

# Add legend and show plot
plt.legend()
plt.show()

