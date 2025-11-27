import streamlit as st
from db import Cassandra
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import numpy as np

# Global styles -------------------------------------------------------------------
st.set_page_config(layout="wide")

# Load the external CSS file
def local_css(file_name):
  with open(file_name) as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("./style.css")

cmap = plt.get_cmap('Dark2')
# ---------------------------------------------------------------------------------

st.title("📈 Historical PCI (Pavement Condition index)")

cassandra = Cassandra()
cassandra.exec("SELECT x1,x2,y1,y2, road_index, label, ppm, timestamp FROM crack")
cassandra.join_roads()
cassandra.calc_pci()
data = cassandra.data

data = data.to_crs(epsg=3857)

data = data.sort_values("timestamp")
data = data.set_index("timestamp")

monthly_pci = data["pci"].resample("ME").mean().fillna(method='ffill')


x = monthly_pci.index.astype(int)
y = monthly_pci.values

fig, ax = plt.subplots(figsize=(8, 5), dpi=200)  # Create figure and axis

X_Y_Spline1 = make_interp_spline(x, y, k=min(3, len(x) - 1))

X_1 = np.linspace(x.min(), x.max(), 500)
Y_1 = X_Y_Spline1(X_1)


ax.plot(X_1, Y_1, label="Monthly PCI")

months = monthly_pci.index.to_period('M')
ax.set_xticks(x)
ax.set_xticklabels(months)

ax.set_xlabel("Month")
ax.set_ylabel("PCI")
ax.set_title("Monthly PCI")
ax.legend()
ax.grid(True, alpha=0.7)

st.pyplot(fig)
