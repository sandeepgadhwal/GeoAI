from geoai import config
from geoai.data.admin import get_countries
from pathlib import Path
from geoai.utils import download_file
import geopandas as gpd
import pandas as pd
from shapely import wkt
from geoai.db.postgres import get_connection
import os
from concurrent.futures import ProcessPoolExecutor

VERSION = 'V3'
GBF_WORKDIR = config.WORK_DIR / 'google-building-footprint'
TILES_URL = 'https://sites.research.google/open-buildings/tiles.geojson'

CHUNK_SIZE = 100000
VIEW_NAME = 'gbf_all'

def get_tiles():
    tiles_path = GBF_WORKDIR / Path(TILES_URL).name
    GBF_WORKDIR.mkdir(parents=True, exist_ok=True)

    if not tiles_path.exists():
        download_file(TILES_URL, GBF_WORKDIR)
    return gpd.read_file(tiles_path)

def main():
    cdf = get_countries()
    india_geom = cdf[cdf['NAME_EN'] == 'India'].unary_union
    tiles_df = get_tiles()
    urls = tiles_df[tiles_df.intersects(india_geom)]['tile_url'].values
    # table_names = []
    # for i, url in enumerate(urls):
    #    table_names.append(insert_tile(url))

    pool = ProcessPoolExecutor(max_workers=min(os.cpu_count(), 12))
    table_names = pool.map(insert_tile, urls)
    pool.shutdown()

    create_view(table_names)

def create_view(table_names):
    table_queries = []
    for table_name in table_names:
        if table_name is None:
            continue
        table_queries.append(
            f"""
            SELECT geometry FROM {table_name}
            """
        )
    query = f"""
    DROP VIEW IF EXISTS {VIEW_NAME};
    CREATE OR REPLACE VIEW {VIEW_NAME} AS 
    SELECT 
        ROW_NUMBER() OVER () AS FID,
        geometry       
    FROM (
        {"UNION ALL".join(table_queries)}
    ) AS v
    """
    print(f"-- Creating View: {VIEW_NAME}")
    with get_connection() as con:
        con.execute(query)
    print(f"-- Created View: {VIEW_NAME}")

def insert_tile(url):
    print(f"-- Processing: {url}")
    tile_name = Path(url).name
    table_name = f"gbf_{tile_name.split('.')[0]}"

    workdir = GBF_WORKDIR / VERSION
    if not workdir.exists():
        workdir.mkdir(parents=True)

    file_path = workdir / tile_name
    file_path_track = workdir / 'done' / file_path.with_suffix('.done').name
    if file_path_track.exists():
        print(f"-- Skipping tile: {tile_name} table Exists !")
        return table_name

    print(f"-- Parsing {file_path} to table {table_name}")
    download_file(url, workdir, exists_ok=True)
    if_exists = 'replace'
    with pd.read_csv(file_path, chunksize=CHUNK_SIZE) as reader:
        for i, chunk in enumerate(reader):
            print(f"-- Inserting table: {table_name} chunk: {i}")
            chunk['geometry'] = chunk['geometry'].apply(wkt.loads)
            gdf = gpd.GeoDataFrame(chunk, geometry='geometry', crs=4326).explode(index_parts=False)
            with get_connection() as con:
                gdf.to_postgis(table_name, con=con, if_exists=if_exists)
            if_exists = 'append'
    print(f"-- Inserted table: {table_name}")

    file_path_track.parent.mkdir(exist_ok=True)
    with open(file_path_track, 'w') as f:
        pass

    return table_name        
    
def get_download_list():
    pass

if __name__=='__main__':
    main()