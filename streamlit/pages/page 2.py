import streamlit as st
import pydeck as pdk
from db import Cassandra
import json
import matplotlib.pyplot as plt
import contextily as ctx

# Global styles -------------------------------------------------------------------
st.set_page_config(layout="wide")

# Load the external CSS file
def local_css(file_name):
  with open(file_name) as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("./style.css")
# ---------------------------------------------------------------------------------

cassandra = Cassandra()
cassandra.exec("SELECT lon, lat, confidence, label, timestamp, image FROM crack")
data = cassandra.data

data['timestamp'] = data['timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S")

st.title("🌡️ Cracks heatmap")

# Initial view
view_state = pdk.ViewState(
    latitude=data['lat'].iloc[0],
    longitude=data['lon'].iloc[0],
    zoom=15,
    pitch=45
)

# Heatmap layer
heatmap_layer = pdk.Layer(
    "HeatmapLayer",
    data=data,
    get_position=["lon", "lat"],
    get_weight='confidence',
    aggregation="MEAN",
    radiusPixels=60,
    intensity=1.2,
    colorRange=[
        [46, 204, 113, 80],        # Emerald Green
        [241, 196, 15, 120],       # Yellow
        [230, 126, 34, 160],       # Orange
        [231, 76, 60, 200],        # Red
    ],
    pickable=False,
)

# Scatterplot layer for hover
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=data,
    get_position=["lon", "lat"],
    get_fill_color=[255, 140, 0],  # Color of points
    get_radius=1,
    pickable=True,                 # enables hover
    auto_highlight=True,
)

# Deck with both layers
deck = pdk.Deck(
    layers=[heatmap_layer, scatter_layer],
    initial_view_state=view_state,
    tooltip={
        "html": """
        <b>Image:</b> {image} <br/>
        <b>Timestamp:</b> {timestamp} <br/>
        <b>Crack Type:</b> {label} <br/> 
        <b>Confidence:</b> {confidence}""",
        "style": {
            "color": "white",
            "backgroundColor": "rgba(0, 0, 0, 0.7)",
            "fontSize": "14px",
        }
    }
)

# Display in Streamlit
st.pydeck_chart(deck)
# -----------------------------------------------------------------------------------------------
st.title("🗺️ Roads PCI Map")

cassandra.exec("SELECT x1,x2,y1,y2, road_index, label, ppm FROM crack")
cassandra.join_roads()
cassandra.calc_pci()
data = cassandra.data

color_map = {
    "Excellent": [0, 255, 0, 120],
    "Good": [0, 200, 255, 120],
    "Fair": [255, 255, 0, 120],
    "Poor": [255, 165, 0, 120],
    "Very Poor": [255, 0, 255, 120],
    "Failed": [255, 0, 0, 120]
}

data["color"] = data["condition"].map(color_map)

# Count per condition
summary = data\
    .drop_duplicates(subset=['road_index'], keep='first')['condition']\
    .value_counts().reindex(
    ["Excellent", "Good", "Fair", "Poor", "Very Poor", "Failed"], fill_value=0
)

st.markdown("Number of roads in each PCI category.")

# Display as colored cards
cols = st.columns(len(summary))
for i, (condition, count) in enumerate(summary.items()):
    r, g, b, a = color_map[condition]
    cols[i].markdown(
        f"""
        <div style="
            background-color: rgb({r},{g},{b}, {a});
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            color: white;
            font-weight: bold;
            font-size: 12px;
            color: black;
            margin-bottom: 10px;
        ">
            {condition}<br>{count}
        </div>
        """,
        unsafe_allow_html=True
    )

geojson_data = json.loads(data.to_json())

tooltip = {
    "html": """
        <b>Street:</b> {name}<br>
        <b>Condition:</b> {condition}<br>
        <b>PCI:</b> {pci}<br>
    """,
    "style": {
        "backgroundColor": "steelblue",
        "color": "white",
        "fontSize": "12px"
    }
}

# 2. Create Pydeck Layer
layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson_data,  # must be a dict or URL
    get_line_color="properties.color",  # must be stored in properties
    get_line_width=7,
    pickable=True,
    auto_highlight=True
)

# 3. Define view
view_state = pdk.ViewState(
    latitude=data.geometry.centroid.y.mean(),
    longitude=data.geometry.centroid.x.mean(),
    zoom=12
)

# 4. Render
deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style="light")
st.pydeck_chart(deck)
# ---------static map------------------------------------------------------------------------
# data = data.to_crs(epsg=3857)
# data.plot(label='condition')

# fig, ax = plt.subplots(figsize=(10, 10))
# data.plot(ax=ax, linewidth=3, color='green')
# ctx.add_basemap(ax)
# ax.set_axis_off()
# plt.tight_layout()
# st.pyplot(fig)