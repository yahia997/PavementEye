import streamlit as st
from db import Cassandra
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np

# Global styles -------------------------------------------------------------------
st.set_page_config(layout="wide")

# Load the external CSS file
def local_css(file_name):
  with open(file_name) as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")
# ---------------------------------------------------------------------------------

cassandra = Cassandra()
cassandra.exec("SELECT * FROM crack LIMIT 10")
data = cassandra.join_roads()
data = data.drop(['geometry', 'index', 'road_index', 'id'], axis=1)

st.title("Pavement eye 🛣️")


st.markdown("###### Last 10 cracks")
st.dataframe(data)

# ----------------------------------------------------------------------------------

col1, col2 = st.columns([1, 2])

with col1:
  st.markdown("###### Percentage of each crack type")
  data1 = cassandra.exec("SELECT label FROM crack")

  cmap = plt.get_cmap('Dark2')

  # Get a list of 8 colors from the colormap

  fig, ax = plt.subplots(1, 1)

  plot = data1.groupby('label')['label'].count()

  colors = cmap(np.linspace(0, 1, len(plot.index)))
  ax.pie(plot, labels=plot.index, autopct='%.2f%%', colors=colors)
  st.pyplot(fig)
# -----------------------------------------------------------------------------------
cassandra.exec("SELECT road_index, label FROM crack")
data2 = cassandra.join_roads()

grouped_df = data2.groupby(["fclass", "label"]).size().reset_index(name='count')

with col2:
  # Title
  st.markdown("###### Crack Type by Road Type")

  # Treemap plot
  fig = px.treemap(
    grouped_df,
    path=["fclass", "label"],
    values="count",
    color="fclass",
    title="Distribution of Crack Types Across Road Types",
    color_discrete_sequence=px.colors.qualitative.Dark24
  )

  st.plotly_chart(fig, use_container_width=True)
# ----------------------------------------------------------------------------------
data2 = data2.to_crs("EPSG:3857")
data2['length_km'] = data2.geometry.length / 1000
total_len_km = data2['length_km'].sum()

st.markdown(f"""
##### Total Number of cracks = {len(data2)} Crack


##### Total length in Km = {total_len_km} KM
""")