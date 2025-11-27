# This class to init connection with 
# the running cassandra container

from cassandra.cluster import Cluster
import geopandas as gpd
import pandas as pd
from deduct_value_func import get_deduct_value
import numpy as np
from cassandra.io.libevreactor import LibevConnection
class Cassandra:
  def __init__(self, CASSANDRA_HOST='localhost', CASSANDRA_PORT=9042):
    try:
      print(f"Connecting to cassandra on host = {CASSANDRA_HOST}, port = {CASSANDRA_PORT} ...")

      # Connect to the cluster
      self.cluster = Cluster(
    [CASSANDRA_HOST],
    port=CASSANDRA_PORT
)

      # Create a session
      self.session = self.cluster.connect()

      # use our keyspace database
      self.session.set_keyspace('pavementeye')

      self.data = None
      
      print("Cassnadra connected successfully !")
    except:
      return "Error in cassandra connection"

  def exec(self, query):
    try:
      rows = self.session.execute(query)

      # parse data to be as normal python lists and dic
      data = []
      for row in rows:
        row_dict = dict(row._asdict())
        data.append(row_dict)

      self.data = pd.DataFrame(data)

      return self.data
    except:
      return "Error in the cassandra query"
    
  def join_roads(self):
    roads_df = gpd.read_file('../data/egypt/geo.geojson').to_crs(epsg=4326)

    roads_df['road_index'] = roads_df.index
    joined = roads_df\
      .merge(self.data, how='right', left_on='road_index', right_on='road_index')

    self.data = joined

    return self.data
  
  def calc_pci(self):
    df = self.data[self.data['road_index'] != -1].copy()

    # Calculate crack dimensions in meters (change 200 to actual ppm if needed)
    df['crack_width'] = abs(df['x2'] - df['x1']) / df['ppm']
    df['crack_length'] = abs(df['y2'] - df['y1']) / df['ppm']

    # Crack area in m²
    df['crack_area'] = df['crack_width'] * df['crack_length']

    # Project to metric CRS to get accurate lengths
    df = df.to_crs("EPSG:3857")
    df['road_length'] = df.geometry.length

    # Assume road width = 10m
    df['road_area'] = df['road_length'] * 10

    # Distress density (% of road area)
    df['dd'] = (df['crack_area'] / df['road_area']) * 100

    # Deduct value (medium severity)
    df['dv'] = df.apply(lambda row: get_deduct_value(row['label'], row['dd']), axis=1)

    # Sort by road_index and DV (descending)
    df = df.sort_values(by=['road_index', 'dv'], ascending=[True, False])

    # Group by road and calculate PCI
    pci_list = []
    for road_index, group in df.groupby('road_index'):
        deduct_values = group['dv'].tolist()
        q = sum(1 for dv in deduct_values if dv > 2)

        if not deduct_values:
            pci = 100.0
        elif len(deduct_values) == 1:
            pci = 100 - deduct_values[0]
        else:
            # Total Deduct Value
            tdv = sum(deduct_values)

            # Simple CDV correction approximation (more precise formula can be added)
            if tdv <= 100:
                cdv = tdv - (tdv**2 / 250)
            else:
                cdv = 100 - 10 * np.sqrt(tdv - 100)

            pci = max(0, 100 - cdv)

        pci_list.append({'road_index': road_index, 'pci': round(pci, 2)})

    # Convert to DataFrame for export/plot
    pci_df = pd.DataFrame(pci_list)

    pci_df['condition'] = pci_df['pci'].apply(self.pci_condition_label)

    
    self.data = self.data\
      .merge(pci_df,how='left', left_on='road_index', right_on='road_index')

    return self.data
  
  def pci_condition_label(self, pci):
    if pci >= 85:
        return "Excellent"
    elif pci >= 70:
        return "Good"
    elif pci >= 55:
        return "Fair"
    elif pci >= 40:
        return "Poor"
    elif pci >= 25:
        return "Very Poor"
    else:
        return "Failed"





