import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt

gro_place =  "Groningen, Netherlands"
tags = {'amenity': 'hospital'}

# fetch groningen geodata
geo_frame = ox.graph_from_place(gro_place, network_type='drive')
# transform geodata into geodataframe
nodes, edges = ox.graph_to_gdfs(geo_frame)
# fetch emergency care data
emergency_care_gdf = ox.geometries_from_place(gro_place, tags)
#filter out noise
emergency_care_gdf = emergency_care_gdf[['geometry', 'name']]

# plot
fig, ax = plt.subplots(figsize=(10, 10))
edges.plot(ax=ax, linewidth=0.5, edgecolor='black')
emergency_care_gdf.plot(ax=ax, color='red', marker='o', markersize=50, label='Emergency Care')
plt.legend()
plt.show()
