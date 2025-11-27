import streamlit as st
from db import Cassandra
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
from azure.storage.blob import BlobServiceClient
import cv2
from dotenv import load_dotenv
import os
from colors import DASHBOARD_PALETTE
import pandas as pd

# Global styles -------------------------------------------------------------------
st.set_page_config(layout="wide")

# Load the external CSS file
def local_css(file_name):
  with open(file_name) as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")
# ---------------------------------------------------------------------------------
st.title("🛣️ Pavement eye")

# filters ---------------------------------------------------------------------------
cassandra = Cassandra()

# get dists from the db (only districts in the database)
dists = cassandra.exec(f"SELECT DISTINCT dist FROM crack")

# get max and min confidence from the db
max_conf = cassandra.exec(f"SELECT max(confidence) as max_conf FROM crack").values[0][0]
min_conf = cassandra.exec(f"SELECT min(confidence) as min_conf FROM crack").values[0][0]

# get max and min time from the db
max_ts = cassandra.exec(f"SELECT max(timestamp) FROM crack").values[0][0]
min_ts = cassandra.exec(f"SELECT min(timestamp) FROM crack").values[0][0]

# Convert numpy.datetime64 to Python datetime.date
max_date = pd.to_datetime(max_ts).date()
min_date = pd.to_datetime(min_ts).date()


date_range = st.date_input(
    "Select date range",
    value=(min_date, max_date),  # default selection
    min_value=min_date,
    max_value=max_date
)

print(date_range)

dists_list = dists.values.reshape(-1) # flatten the array

countries = st.multiselect("Select districts", options=dists_list, default=['Muntazah'])

# prepare the filters
dists_filter = ["'" + word + "'" for word in countries]
dists_filter = ", ".join(dists_filter)

confidence_value = st.slider("Select confidence minimum value", min_value=float(min_conf), max_value=float(max_conf), value=0.5, step=0.05)


start_date, end_date = date_range

# Convert to ISO string for Cassandra
start_iso = start_date.isoformat()
end_iso = end_date.isoformat()

cassandra.exec(f"""SELECT * 
               FROM crack 
               WHERE dist IN ({dists_filter}) 
               AND confidence >= {confidence_value}
                AND timestamp >= '{start_iso} 00:00:00' 
                AND timestamp <= '{end_iso} 11:59:59' 
               ALLOW FILTERING
""")

data = cassandra.join_roads()
data = data.drop(['geometry', 'index', 'road_index', 'id'], axis=1)


# ------------------------------------------------------------------------------
cassandra.exec("SELECT road_index, label FROM crack")
data2 = cassandra.join_roads()

col1, col2, col3 = st.columns(3)

data2 = data2.to_crs("EPSG:3857")
data2['length_km'] = data2.geometry.length / 1000
total_len_km = data2['length_km'].sum()

col1.metric("Total Number of cracks", len(data2))
col2.metric("Total length in Km", round(total_len_km, 2))
# ----------------------------------------------------------------------------------


st.markdown("###### Last cracks")
st.dataframe(data)


# ----------------------------------------------------------------------------------
st.markdown("### 🎯 Detection Results")
image_name = st.text_input("🔍 Enter image name (with extension):")
st.markdown("You can get image name form the table above.")

load_dotenv() # load vars from .env

# Your Azure Data Lake Storage credentials
# Replace with your actual values
account_name = os.getenv("account_name")
account_key = os.getenv("account_key")
connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
file_system_name = os.getenv("file_system_name")

if image_name:
    try:
        # Connect to Azure Blob
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=file_system_name, blob=f"raw/{image_name}")

        # Download image
        image_data = blob_client.download_blob().readall()
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # get detections of this image only (saved in cassandra)
        # image name is unique (lat,lon,timestamp)
        detections = data[data['image'] == image_name][['x1','x2','y1','y2','label','confidence']]

        # draw bounding boxes
        img_annotated = image.copy()
        for _, row in detections.iterrows():
            x1, x2, y1, y2 = int(row["x1"]), int(row["x2"]), int(row["y1"]), int(row["y2"])
            label = row.get("label", "unknown")
            conf = row.get("confidence", None)

            color = (0, 255, 0)  # Default color (green)
            cv2.rectangle(img_annotated, (x1, y1), (x2, y2), color, 2)

            # Label text
            text = f"{label}"
            if conf is not None:
                text += f" ({conf:.2f})"

            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img_annotated, (x1, y1 - th - 4), (x1 + tw, y1), color, -1)
            cv2.putText(img_annotated, text, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        # Convert to RGB and display
        img_rgb = cv2.cvtColor(img_annotated, cv2.COLOR_BGR2RGB)

        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.image(img_rgb, caption=f"Detections for {image_name}", width=500)

    except Exception as e:
        st.error(f"Could not load image: {e}")

# ----------------------------------------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
  st.markdown("###### Number of each crack type")
  data1 = cassandra.exec("SELECT label FROM crack")

  
  plot = data1.groupby('label')['label'].count().sort_values()

  fig = px.bar(
    x=plot.values,
    y=plot.index,
    orientation='h',
    title="Crack Count by Type",
    labels={'x': 'Count', 'y': 'Crack Type'},
    color=plot.index,    
    color_discrete_sequence=DASHBOARD_PALETTE
  )

  fig.update_layout(
    yaxis=dict(categoryorder='total ascending'),   # matches your sort_values()
    template='plotly_white'
  )

  st.plotly_chart(fig, use_container_width=True)
  
# -----------------------------------------------------------------------------------

grouped_df = data2.groupby(["fclass", "label"]).size().reset_index(name='count')

with col2:
  # Title
  st.markdown("###### Crack Type by Road Type")

  # Treemap plot
  fig = px.treemap(
    grouped_df,
    path=["fclass", "label"],
    values="count",
    color='fclass',
    title="Distribution of Crack Types Across Road Types",
    color_discrete_sequence=DASHBOARD_PALETTE
  )

  st.plotly_chart(fig, use_container_width=True)
# ----------------------------------------------------------------------------------
