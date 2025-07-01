import json
import folium
import math
from branca.colormap import LinearColormap
import webbrowser

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat/2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dLon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def time_to_seconds(t):
    """Convert hh:mm:ss or mm:ss string to total seconds"""
    parts = t.strip().split(":")
    parts = [int(p) for p in parts]
    while len(parts) < 3:
        parts.insert(0, 0)  # handle mm:ss
    hours, minutes, seconds = parts
    return hours * 3600 + minutes * 60 + seconds

def load_data(filename):
    """Load your custom JSON format"""
    data = []
    with open(filename, 'r') as f:
        text = f.read().strip()

        # Remove trailing comma if present
        if text.endswith(","):
            text = text[:-1]

        # Wrap in []
        text = f"[{text}]"

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print("JSON error:", e)
            return []

    # Filter invalid points
    return [
        p for p in data
        if isinstance(p, dict)
        and 'lat' in p and 'lng' in p
        and (p['lat'] != 0 or p['lng'] != 0)
    ]

# Load data
hike_data = load_data('152025.json')

if not hike_data:
    print("No valid data points found!")
    exit()

# Calculate distances and speeds
distances = [0]
speeds = [0]

for i in range(1, len(hike_data)):
    prev = hike_data[i-1]
    curr = hike_data[i]

    dist = haversine(
        prev['lng'], prev['lat'],
        curr['lng'], curr['lat']
    )
    distances.append(distances[-1] + dist)

    dt = time_to_seconds(curr['timestamp']) - time_to_seconds(prev['timestamp'])
    dt = max(dt, 1)  # avoid divide by zero
    speed = (dist / dt) * 3600  # km/h
    speeds.append(speed)

altitudes = [p.get('altitude', 0) for p in hike_data]

# Create map
m = folium.Map(
    location=[hike_data[0]['lat'], hike_data[0]['lng']],
    zoom_start=14,
    tiles='https://{s}.tile.thunderforest.com/outdoors/{z}/{x}/{y}.png',
    attr='Thunderforest Outdoors'
)

# Add colored path by altitude
colormap = LinearColormap(['blue', 'green', 'yellow', 'red'],
                          vmin=min(altitudes),
                          vmax=max(altitudes))

folium.PolyLine(
    locations=[(p['lat'], p['lng']) for p in hike_data],
    weight=6,
    color=[colormap(alt) for alt in altitudes]
).add_to(m)

# Add a circle marker for each point
for i, p in enumerate(hike_data):
    popup_text = (
        f"<b>Time:</b> {p.get('timestamp', '')}<br>"
        f"<b>Altitude:</b> {p.get('altitude', '')} m<br>"
        f"<b>Speed:</b> {speeds[i]:.2f} km/h"
    )
    folium.CircleMarker(
        location=[p['lat'], p['lng']],
        radius=3,
        color='black',
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

# Add start and end markers
folium.Marker(
    [hike_data[0]['lat'], hike_data[0]['lng']],
    popup=f"Start: {hike_data[0].get('timestamp', '')}",
    icon=folium.Icon(color='green')
).add_to(m)

folium.Marker(
    [hike_data[-1]['lat'], hike_data[-1]['lng']],
    popup=f"End: {hike_data[-1].get('timestamp', '')}",
    icon=folium.Icon(color='red')
).add_to(m)

# Add legend
colormap.caption = 'Altitude (m)'
colormap.add_to(m)

# Save
map_file = 'hike_map.html'
m.save(map_file)
print(f"Success! Map saved with {len(hike_data)} points.")

# Auto-open in browser
webbrowser.open(map_file)
