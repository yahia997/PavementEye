import streamlit as st
from db import Cassandra
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from colors import DASHBOARD_PALETTE

# Global styles -------------------------------------------------------------------
st.set_page_config(layout="wide")

# Load the external CSS file
def local_css(file_name):
  with open(file_name) as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("./style.css")

cmap = plt.get_cmap('Dark2')
# ---------------------------------------------------------------------------------

cassandra = Cassandra()
cassandra.exec("SELECT label, road_index FROM crack")
cassandra.join_roads()
cracks_df = cassandra.data



st.markdown("##### 🚦 Comparison between different road speeds")

# Filter valid speeds
cracks_df = cracks_df[cracks_df['maxspeed'] > 0]

  # Group by maxspeed and crack type
speed_cracks = (
      cracks_df.groupby(["maxspeed", "label"])
      .size()
      .reset_index(name="count")
  )

  # Pivot to have crack types as columns (actual counts)
pivot_speed = speed_cracks.pivot(
      index="maxspeed", columns="label", values="count"
  ).fillna(0)

  # Melt to long-form for Plotly
pivot_long = pivot_speed.reset_index().melt(
      id_vars='maxspeed',
      var_name='Crack Type',
      value_name='Count'
  )

  # Total counts for annotation
total_counts = cracks_df.groupby('maxspeed').size().sort_index()

  # Map colors to your professional palette
color_map = {k: v for k, v in zip(pivot_long['Crack Type'].unique(), DASHBOARD_PALETTE)}

  # Plotly stacked horizontal bar chart
fig = px.bar(
      pivot_long,
      x='maxspeed',
      y='Count',
      color='Crack Type',
      color_discrete_map=color_map,
      text='Count',
      labels={'maxspeed': 'Maxspeed (KM/H)', 'Count': 'Number of Cracks'},
      title="Number of Crack Types per Maxspeed",
      template='plotly_white'
  )

  # Make bars stacked
fig.update_layout(
    barmode='stack',
    xaxis=dict(type='category', categoryorder='category ascending'),
    bargap=0,  
    width=1200,
    height=600
)
  # Add total count annotations above each stack
for speed in total_counts.index:
      fig.add_annotation(
          x=speed,
          y=total_counts.loc[speed] + 2,  # slightly above total
          text=f"{total_counts.loc[speed]} cracks",
          showarrow=False,
          font=dict(size=12)
      )

fig.update_layout(width=1200, height=600)

  # Display in Streamlit
st.plotly_chart(fig, use_container_width=True)
# ------------------------------------------------------------------------------------------


st.markdown("##### 🔄 One way roads vs both")
df = cassandra.data

oneway_B = df[df['oneway'] == 'B'].groupby('label').size()
oneway_F = df[df['oneway'] == 'F'].groupby('label').size()
  

categories_B = oneway_B.index
categories_F = oneway_F.index

fig = go.Figure()

fig.add_trace(go.Scatterpolar(
      r=oneway_B.values,
      theta=categories_B,
      fill='toself',
      name='Both',
  ))
fig.add_trace(go.Scatterpolar(
      r=oneway_F.values,
      theta=categories_F,
      fill='toself',
      name='False'
  ))

fig.update_layout(
      polar=dict(
          radialaxis=dict(
              visible=True,
              range=[0, max(max(oneway_B.values), max(oneway_F.values)) + 1]
          )
      ),
      showlegend=True
  )

st.plotly_chart(fig, use_container_width=True)
# -------------------------------------------------------------------------------------

