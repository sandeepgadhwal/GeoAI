# Standard Library
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd

from geoai import config
from geoai.utils import download_file

COUNTRIES_URL = "https://datacatalogfiles.worldbank.org/ddh-published/0038272/DR0046666/wb_boundaries_geojson_highres.zip"

ADMIN_WORKDIR = config.WORK_DIR / "admin"


def get_countries():
    file_path = ADMIN_WORKDIR / Path(COUNTRIES_URL).name
    ADMIN_WORKDIR.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        download_file(COUNTRIES_URL, ADMIN_WORKDIR)
    with ZipFile(file_path) as gf:
        with gf.open("WB_Boundaries_GeoJSON_highres/WB_countries_Admin0.geojson") as f:
            return gpd.read_file(f)
