import json
import folium
import matplotlib.pyplot as plt
from datetime import datetime
import re

def load_hike_data(filename):
    """Load JSON data that contains multiple separate objects with potential formatting issues"""
    data = []
    with open(filename, 'r') as f:
        # Read the entire file content
        content = f.read()
        
        # Remove any trailing commas and whitespace
        content = content.strip().rstrip(',')
        
        # Handle cases where objects might be separated improperly
        # This regex matches individual JSON objects
        json_objects = re.findall(r'\{.*?\}(?=\s*,\s*\{|$)', content, re.DOTALL)
        
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
    valid_data = [point for point in data if point['lat'] != 0 or point['lng'] != 0]
    
    return valid_data

# 1. Load the data
hike_data = load_hike_data('152025.json')

if not hike_data:
    print("No valid data points found!")
    exit()

# --- 2. Generate Interactive Map ---
coordinates = [(point["lat"], point["lng"]) for point in hike_data]
m = folium.Map(location=coordinates[0], zoom_start=15, tiles='OpenStreetMap')

# Add path with elevation-based color gradient
altitudes = [p["altitude"] for p in hike_data]
min_alt, max_alt = min(altitudes), max(altitudes)

def get_color(alt):
    """Return color based on altitude (green to red gradient)"""
    normalized = (alt - min_alt) / (max_alt - min_alt)
    return f"hsl({120 * (1 - normalized)}, 100%, 50%)"

# Draw path
folium.PolyLine(
    locations=coordinates,
    color='blue',
    weight=5,
    opacity=0.8,
    tooltip="Hike Path"
).add_to(m)

# Add markers for start and end
folium.Marker(
    coordinates[0],
    popup=f"Start<br>Time: {hike_data[0]['timestamp']}<br>Alt: {altitudes[0]:.1f}m",
    icon=folium.Icon(color='green', icon='play')
).add_to(m)

folium.Marker(
    coordinates[-1],
    popup=f"End<br>Time: {hike_data[-1]['timestamp']}<br>Alt: {altitudes[-1]:.1f}m",
    icon=folium.Icon(color='red', icon='stop')
).add_to(m)

# Add elevation scale
legend_html = '''
<div style="position: fixed; 
     bottom: 50px; left: 50px; width: 120px; height: 150px; 
     border:2px solid grey; z-index:9999; font-size:12px;
     background-color:white; padding: 5px;">
     <b>Elevation Scale</b><br>
     <div style="background: linear-gradient(to top, hsl(0, 100%, 50%), hsl(120, 100%, 50%)); 
          width: 100%; height: 100px; margin-top: 5px;">
     </div>
     <div style="display: flex; justify-content: space-between;">
         <span>{max:.0f}m</span>
         <span>{min:.0f}m</span>
     </div>
</div>
'''.format(max=max_alt, min=min_alt)
m.get_root().html.add_child(folium.Element(legend_html))

# Save map
m.save('hike_path.html')
print(f"Interactive map saved to hike_path.html with {len(hike_data)} points")

# --- 3. Create Data Visualizations ---
plt.style.use('ggplot')

# Convert timestamps
times = []
for point in hike_data:
    try:
        times.append(datetime.strptime(point["timestamp"], "%H:%M:%S"))
    except ValueError:
        # Handle timestamps with single-digit hours
        if point["timestamp"].count(':') == 1:
            times.append(datetime.strptime(point["timestamp"], "%M:%S"))
        else:
            times.append(datetime.strptime("00:00:00", "%H:%M:%S"))

# Create figure with subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# Altitude plot
ax1.plot(times, altitudes, 'b-', label='Altitude')
ax1.fill_between(times, altitudes, min_alt, color='blue', alpha=0.1)
ax1.set_ylabel('Altitude (m)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Temperature plot
ax2.plot(times, [p.get("dht_temp", 0) for p in hike_data], 'r-', label='Temperature')
ax2.set_ylabel('Temperature (°C)')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Humidity plot
ax3.plot(times, [p.get("dht_humidity", 0) for p in hike_data], 'g-', label='Humidity')
ax3.set_ylabel('Humidity (%)')
ax3.set_xlabel('Time')
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.xticks(rotation=45)
plt.suptitle('Hike Data Analysis', y=0.98)
plt.tight_layout()
plt.savefig('hike_data.png', dpi=120)
print("Data visualization saved to hike_data.png")
plt.show()