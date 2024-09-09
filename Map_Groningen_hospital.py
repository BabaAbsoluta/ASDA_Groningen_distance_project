import osmnx as ox
import folium
from shapely.geometry import Point
from geopy.distance import geodesic

# Define place and tags for emergency care
place = "Groningen, The Netherlands"
tags = {'amenity': 'hospital'}

# Fetch and project the street network
G = ox.graph_from_place(place, network_type="drive")
G = ox.project_graph(G)  # Automatically project graph to UTM

# Fetch emergency care locations (hospitals)
emergency_care_gdf = ox.features_from_place(place, tags)

# Ensure the emergency care GeoDataFrame is in EPSG:4326 (folium requires lat/lon)
if emergency_care_gdf.crs is None:
    emergency_care_gdf.crs = 'EPSG:4326'
else:
    emergency_care_gdf = emergency_care_gdf.to_crs('EPSG:4326')

# Convert the OSMnx graph to GeoDataFrames for the nodes and edges
gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)

# Reproject the nodes and edges back to EPSG:4326 for folium mapping
gdf_nodes = gdf_nodes.to_crs(epsg=4326)
gdf_edges = gdf_edges.to_crs(epsg=4326)

# Convert hospital polygons to centroids (if any polygons are present)
if emergency_care_gdf.geom_type.isin(['Polygon', 'MultiPolygon']).any():
    emergency_care_gdf['geometry'] = emergency_care_gdf.centroid


# Function to calculate the distance between two points (in meters)
def calculate_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).meters


# Initialize the folium map centered on the average node location
m = folium.Map(location=[gdf_nodes.geometry.y.mean(), gdf_nodes.geometry.x.mean()], zoom_start=13)

# Add street network edges to the map
for _, row in gdf_edges.iterrows():
    folium.PolyLine(
        locations=[(point[1], point[0]) for point in row['geometry'].coords],  # Lat, Lon order
        color='grey',
        weight=2
    ).add_to(m)

# Add hospitals to the map
for _, row in emergency_care_gdf.iterrows():
    folium.CircleMarker(
        location=(row.geometry.y, row.geometry.x),
        radius=8,
        color='red',
        fill=True,
        fill_opacity=0.9,
        tooltip=row['name'] if 'name' in row else "Hospital"
    ).add_to(m)


# Function to handle node clicks and calculate distance to the nearest hospital
def on_node_click(lat, lon):
    # Calculate distances from the clicked point to all hospitals
    distances = emergency_care_gdf.geometry.apply(lambda hospital: calculate_distance(lat, lon, hospital.y, hospital.x))

    # Find the nearest hospital and the distance to it
    nearest_hospital_idx = distances.idxmin()
    nearest_hospital_distance = distances.min()

    # Return the distance in a formatted string
    return f"Distance to nearest hospital: {nearest_hospital_distance:.2f} meters"


# Add clickable nodes to the map with popup showing distance to nearest hospital
for _, row in gdf_nodes.iterrows():
    lat = row.geometry.y
    lon = row.geometry.x

    # Add each node with a click event that shows the distance to the nearest hospital
    folium.Marker(
        location=(lat, lon),
        icon=folium.Icon(color='blue', icon='info-sign'),
        popup=folium.Popup(on_node_click(lat, lon), max_width=250)
    ).add_to(m)

# Save the interactive map to an HTML file
m.save("interactive_map_with_clickable_nodes.html")
