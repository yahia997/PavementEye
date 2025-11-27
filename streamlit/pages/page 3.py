import streamlit as st
import matplotlib.pyplot as plt
from db import Cassandra
import plotly.express as px
import pandas as pd
import numpy as np
from colors import DASHBOARD_PALETTE, color_scale


# Global styles -------------------------------------------------------------------
st.set_page_config(layout="wide")

# Load the external CSS file
def local_css(file_name):
  with open(file_name) as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("./style.css")

cmap = plt.get_cmap('Dark2')
# ---------------------------------------------------------------------------------

st.title("🌉 Number of each crack type for different road infrastructure")
st.markdown("""
Normal road means road that is not tunnel or bridge.
""")

cassandra = Cassandra()
cassandra.exec("SELECT road_index, label FROM crack")
df = cassandra.join_roads()

# Group by label
bridge = df[df['bridge'] == 'T'].groupby('label').size().rename('count').sort_values(ascending=False)
tunnel = df[df['tunnel'] == 'T'].groupby('label').size().rename('count').sort_values(ascending=False)
normal = df[(df['bridge'] == 'F') & (df['tunnel'] == 'F')].groupby('label').size().rename('count').sort_values(ascending=False)

# Helper to create horizontal bar chart
def plot_hbar(series, title):
    df_plot = series.reset_index()          # convert Series to DataFrame
    df_plot.columns = ['Crack Type', 'Count']  # rename columns

    # Map colors using your professional palette
    color_map = {k: v for k, v in zip(df_plot['Crack Type'], DASHBOARD_PALETTE[:len(df_plot)])}

    fig = px.bar(
        df_plot,
        x='Count',
        y='Crack Type',
        orientation='h',
        text='Count',
        color='Crack Type',
        color_discrete_map=color_map,
        labels={'Count': 'Number of Cracks', 'Crack Type': 'Crack Type'},
        title=title,
        template='plotly_white',
        hover_data={'Count': True, 'Crack Type': True}
    )
    fig.update_layout(showlegend=False, height=400)
    return fig


col1, col2, col3 = st.columns(3)

# Plot each
with col1:
    st.plotly_chart(plot_hbar(bridge, "Bridge Cracks"), use_container_width=True)

with col2:
    st.plotly_chart(plot_hbar(tunnel, "Tunnel Cracks"), use_container_width=True)

with col3:
    st.plotly_chart(plot_hbar(normal, "Normal Roads Cracks"), use_container_width=True)

# ----------------------------------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    cassandra.exec("SELECT x1,x2,y1,y2, road_index, label, ppm FROM crack")
    cassandra.join_roads()
    cassandra.calc_pci()
    df = cassandra.data
    df['road_index'] = df['road_index'].astype(str)

    df = df[df['road_index'] != -1]


    group = df.groupby(['road_index']).agg({
    'name': 'first',
    'pci': 'mean',
    'fclass': 'first'
    }).reset_index()

    group['name'].fillna(group['road_index'], inplace=True)

    plot = group.sort_values(by='pci', ascending=True).iloc[:10]

    top_10_damaged_roads = plot['road_index'].to_list()[:10]

    # Horizontal bar chart
    fig = px.bar(
    plot,
    x='pci',
    y='road_index',   # as roads name may be repeated
    orientation='h',
    title="🚧 Top 10 Damaged Roads by PCI",
    labels={'pci': 'PCI', 'road_index': 'Road Index'},
    hover_data={'name': True, 'pci': True, 'fclass': True},
    template='plotly_white',
    color_discrete_sequence=['#1E3A8A'] 
)

    fig.update_yaxes(categoryorder='array', categoryarray=plot['road_index'])
    st.plotly_chart(fig, use_container_width=True)
# -----------------------------------------------------------------------------------------
with col2:
    # Filter top 10 damaged roads
    top_damaged_df = df[df['road_index'].isin(top_10_damaged_roads)]

    # Replace missing names with road_index
    top_damaged_df['name'] = top_damaged_df['name'].fillna(top_damaged_df['road_index'])

    # Pivot table: counts of cracks per road and crack type
    pv = pd.pivot_table(
        top_damaged_df,
        index=['road_index', 'name'],   # include name in index
        columns='label',
        values='geometry',
        aggfunc='count'
    ).fillna(0).astype(int)

    # Flatten pivot table
    pv_reset = pv.reset_index()  # now road_index and name are columns

    # Melt to long-form for Plotly
    pv_long = pv_reset.melt(
        id_vars=['road_index', 'name'],
        var_name='Crack Type',
        value_name='Count'
    )

    # Create stacked horizontal bar chart
    fig = px.bar(
        pv_long,
        y='road_index',                # unique identifier
        x='Count',
        color='Crack Type',
        color_discrete_sequence=DASHBOARD_PALETTE,
        hover_data={'name': True, 'road_index': True, 'Count': True},
        title='🛠️ Crack Types for the Top 10 Damaged Roads',
        labels={'road_index': 'Road (ID)', 'Count': 'Number of Cracks'}
    )

    fig.update_layout(
        barmode='stack',
        yaxis={'categoryorder': 'array', 'categoryarray': top_10_damaged_roads},  # maintain order
        template='plotly_white',
    )

    st.plotly_chart(fig, use_container_width=True)
# -----------------------------------------------------------------------------------------
