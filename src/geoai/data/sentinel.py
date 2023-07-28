from pathlib import Path
import os
import pandas as pd
import geopandas as gpd
import geoai.config as config
from geoai.utils import download_file

sentinel_work_dir = Path(config.WORK_DIR) / 'sentinel'

sentinel2_work_dir = sentinel_work_dir / 'sentinel2' / 'index.feather'

sentinel2_index = sentinel2_work_dir

INDEX_URL = 'https://storage.googleapis.com/gcp-public-data-sentinel-2/L2/index.csv.gz'


def get_sentinel2_work_dir():
    return Path(config.WORK_DIR) / 'sentinel' / 'sentinel2'

def download_index():
    sentinel2_work_dir = get_sentinel2_work_dir()
    if not sentinel2_work_dir.exists():
        os.makedirs(sentinel2_work_dir)
    
    return download_file(INDEX_URL, sentinel2_work_dir)

def recreate_index():
    downloaded_index_path = get_sentinel2_work_dir() / Path(INDEX_URL).name
    if not downloaded_index_path.exists():
        download_index()
    
    df = pd.read_csv(downloaded_index_path)

def query_index(gdf: gpd.GeoDataFrame):
    if not sentinel2_index.exists():
        recreate_index()