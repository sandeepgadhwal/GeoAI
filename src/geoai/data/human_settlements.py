import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from pathlib import Path
from pyproj import CRS

def create_clusters_from_building_footprints(data_store: Path, roi: Polygon, roi_crs: CRS):
    bf_tiles = gpd.read_file(data_store / 'tiles.geojson')

    file_store = []
    roi_4326 = gpd.GeoSeries([roi], crs=roi_crs).to_crs(4326).geometry.values[0]
    for tile_id in bf_tiles[bf_tiles.intersects(roi_4326)]['tile_id']:
        file_store.extend(data_store.glob(f'v3/feather/{tile_id}_buildings_*.feather'))
    print("Read files", file_store)

    df_store = []
    for file in file_store:
        gdf = gpd.read_feather(file, columns=["geometry"])
        df_store.append(
            gdf[gdf.intersects(roi_4326)]
        )
    gdf = gpd.GeoDataFrame(pd.concat(df_store).reset_index(drop=True), crs=4326)

    print('Project')
    gdf_prj = gdf.to_crs(roi_crs)
    del gdf

    buffer_distance = 25 # meters

    print('Buffer')
    # Buffer to convert buildings to clusters
    gdf_prj['geometry'] = gdf_prj.buffer(buffer_distance)

    print('Flatten out clusters')
    # Flatten out clusters
    gdf_cluster = gdf_prj.dissolve().explode(index_parts=False).reset_index(drop=True)
    del gdf_prj
    len(gdf_cluster)

    print('Remove Stray holes')
    # Remove Stray holes
    def remove_holes(geom):
        holes = []
        for hole in geom.interiors:
            if Polygon(hole).area > buffer_distance*buffer_distance*4:
                holes.append(hole)
        return Polygon(geom.exterior, holes)

    gdf_cluster['geometry'] = gdf_cluster['geometry'].apply(remove_holes)

    print('Reverse buffer')
    # Reverse buffer
    gdf_cluster = gdf_cluster.explode(index_parts=False).reset_index(drop=True)
    gdf_cluster['geometry'] = gdf_cluster.buffer(-buffer_distance/2)
    len(gdf_cluster)

    print('Remove stray buildings not visible in Sentinel')
    # Remove stray buildings not visible in Sentinel
    gdf_cluster = gdf_cluster.explode(index_parts=False).reset_index(drop=True)
    gdf_cluster = gdf_cluster[gdf_cluster.buffer(-buffer_distance).area > (buffer_distance*buffer_distance*4)]
    len(gdf_cluster)

    return gdf_cluster