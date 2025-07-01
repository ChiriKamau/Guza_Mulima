import json
import folium
from geopy.distance import geodesic
from branca.colormap import LinearColormap
import re

def load_data(filename):
    """Load JSON data that contains multiple separate objects"""
    data = []
    with open(filename, 'r') as f:
        # Read the entire file content
        content = f.read()
        
        # Clean the content by removing trailing commas and whitespace
        content = content.strip().rstrip(',')
        
        # Use regex to find all JSON objects
        # This pattern matches everything between { and }, including nested braces
        json_objects = re.findall(r'\{[^{}]*\}', content)
        
        for obj in json_objects:
            try:
                # Clean up the object string
                obj = obj.strip()
                if not obj.startswith('{'):
                    continue
                if not obj.endswith('}'):
                    obj += '}'
                
                # Parse the JSON object
                data.append(json.loads(obj))
            except json.JSONDecodeError as e:
                print(f"Skipping malformed object: {obj[:100]}...\nError: {e}")
    
    # Filter out points with invalid coordinates (0,0)
    valid_data = [point for point in data if point.get('lat', 1) != 0 or point.get('lng', 1) != 0]
    
    return valid_data

def calculate_distances(points):
    """Calculate cumulative distance in kilometers"""
    distances = [0]
    for i in range(1, len(points)):
        prev = (points[i-1]['lat'], points[i-1]['lng'])
        curr = (points[i]['lat'], points[i]['lng'])
        distances.append(distances[-1] + geodesic(prev, curr).km)
    return distances

# Load and prepare data
hike_data = load_data('152025.json')

if not hike_data:
    print("No valid data points found!")
    exit()

distances = calculate_distances(hike_data)
altitudes = [p.get('altitude', 0) for p in hike_data]

# Create colormap for elevation (red=high, blue=low)
colormap = LinearColormap(
    colors=['blue', 'green', 'yellow', 'red'],
    vmin=min(altitudes), 
    vmax=max(altitudes)
)

# Create the map
m = folium.Map(
    location=[hike_data[0]['lat'], hike_data[0]['lng']], 
    zoom_start=14,
    tiles='https://{s}.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png',
    attr='Thunderforest Outdoors'
)

# Add elevation-colored path
folium.PolyLine(
    locations=[(p['lat'], p['lng']) for p in hike_data],
    weight=6,
    opacity=0.8,
    color=[colormap(alt) for alt in altitudes],
    line_cap='round',
    line_join='round'
).add_to(m)

# Add start/finish markers
folium.Marker(
    [hike_data[0]['lat'], hike_data[0]['lng']],
    popup=f"START\n{hike_data[0].get('timestamp', '')}",
    icon=folium.Icon(color='green', icon='flag')
).add_to(m)

folium.Marker(
    [hike_data[-1]['lat'], hike_data[-1]['lng']],
    popup=f"FINISH\n{hike_data[-1].get('timestamp', '')}",
    icon=folium.Icon(color='red', icon='flag-checkered')
).add_to(m)

# Add colormap legend
colormap.caption = 'Elevation (m)'
colormap.add_to(m)

# Save the map
m.save('hike_map.html')
print(f"Map saved to hike_map.html with {len(hike_data)} points")