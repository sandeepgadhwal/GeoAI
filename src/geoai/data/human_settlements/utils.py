# Standard Library
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from osgeo import gdal
from shapely.geometry import Polygon, box

from geoai.data.building_footprint.insert_data_to_postgis import get_tiles
from geoai.data.utils.image import Image
from geoai.db.postgres import get_connection


def get_human_settlements_from_sentinel_image(
    image_path: Path, **kwargs: dict
) -> gpd.GeoDataFrame:
    """
    This Code creates human settlements from building footprint data for an  input sentinel image.

    for example:
    df = get_human_settlements('/pathto/S2B_MSIL2A_20230518T050659_N0509_R019_T43PGQ_20230518T091909.SAFE')

    """
    ds = gdal.Open(f"{image_path}/MTD_MSIL2A.xml")
    ds_RGB = gdal.Open(ds.GetSubDatasets()[-1][0])
    im = Image.from_gdal(ds_RGB)
    gdf = gpd.GeoDataFrame(geometry=[im.bbox], crs=im.crs)
    return get_human_settlements_from_df(gdf, **kwargs)


def remove_holes(geom: Polygon, area: float) -> Polygon:
    holes = []
    for hole in geom.interiors:
        if Polygon(hole).area > area:
            holes.append(hole)
    return Polygon(geom.exterior, holes)


def get_dataframe(query: str) -> gpd.GeoDataFrame:
    with get_connection() as conn:
        return gpd.read_postgis(query, con=conn, geom_col="geometry")

        # query = f"""
        # SELECT
        #     (ST_DUMP(ST_UNION(
        #         ST_Buffer(
        #             ST_SimplifyPreserveTopology(
        #                 ST_Transform(
        #                     geometry,
        #                     {roi_crs}
        #                 ),
        #                 {simplification_tolerance}
        #             ),
        #             {buffer_distance},
        #             'endcap=flat join=flat'
        #         )
        #     ))).geom AS geometry
        # FROM
        #     {table_name}
        # WHERE
        #     ST_Intersects(
        #         geometry,
        #         ST_Transform(
        #             ST_GeomFromText('{window_bbox.wkt}', {roi_crs}),
        #             4326
        #         )
        #     )
        # LIMIT 100
        # """
        # buffer_distance = 0


def get_human_settlements_from_df(
    roi_df: gpd.GeoDataFrame,
    grid_size: int = 10000,  # meters
    buffer_distance: int = 25,  # meters
    max_workers: int = None,
    # simplification_tolerance=10,
) -> gpd.GeoDataFrame:
    """
    roi_df should be in projected coordinate system.
    """
    bounds = roi_df.total_bounds
    roi_crs = roi_df.crs.to_epsg()
    ymins = np.arange(bounds[1], bounds[3], grid_size)
    xmins = np.arange(bounds[0], bounds[2], grid_size)
    print(f"Total windows : {len(ymins)*len(xmins)}")

    if max_workers is None:
        max_workers = min(os.cpu_count(), 12)

    with get_connection() as _:
        pass

    tdf = get_tiles()

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = []
        counter = 0
        for ymin in ymins:
            for xmin in xmins:
                window_bbox = box(xmin, ymin, xmin + grid_size, ymin + grid_size)
                with np.errstate(invalid="ignore"):
                    bbox_4326 = (
                        gpd.GeoDataFrame(geometry=[window_bbox], crs=roi_crs)
                        .to_crs(tdf.crs)
                        .geometry.values[0]
                    )
                    tile_ids = tdf[tdf.intersects(bbox_4326)]["tile_id"].values
                for tile_id in tile_ids:
                    counter += 1
                    table_name = f"gbf_{tile_id}_buildings"
                    query = f"""
                    SELECT
                        (ST_DUMP(ST_UNION(
                            ST_Buffer(
                                ST_Transform(
                                    geometry,
                                    {roi_crs}
                                ),
                                {buffer_distance},
                                'endcap=square join=mitre'
                            )
                        ))).geom AS geometry
                    FROM
                        {table_name}
                    WHERE
                        ST_Intersects(
                            geometry,
                            ST_Transform(
                                ST_GeomFromText('{window_bbox.wkt}', {roi_crs}),
                                4326
                            )
                        )
                    """
                    future = pool.submit(get_dataframe, query)
                    futures.append(future)

        print(f"Reading total windows {len(futures)}")
        df_store = []
        for i, future in enumerate(as_completed(futures)):
            print(f"Read window : {i}/{len(futures)}", end="\r")
            df = future.result()
            if len(df) > 0:
                df_store.append(df)
        print(f"Read all windows: {len(futures)}              ")

    print("Concat data")
    if not df_store:
        return gpd.GeoDataFrame()
    df = gpd.GeoDataFrame(pd.concat(df_store), crs=roi_crs)

    print("Remove holes, rows:", len(df))
    df["geometry"] = df["geometry"].apply(
        lambda x: remove_holes(x, buffer_distance * buffer_distance * 4)
    )

    print("Dissolve to merge windows, rows:", len(df))
    df = df.dissolve().explode(index_parts=False).reset_index(drop=True)

    print("Reverse buffer, rows:", len(df))
    df["geometry"] = df.buffer(
        -buffer_distance / 2, cap_style="flat", join_style="mitre"
    )

    print("Remove stray buildings not visible in Sentinel, rows:", len(df))
    # Remove stray buildings not visible in Sentinel
    df = df.explode(index_parts=False).reset_index(drop=True)
    df = df[
        df.buffer(-buffer_distance, cap_style="flat", join_style="mitre").area
        > (buffer_distance * buffer_distance * 4)
    ]

    print("Done, rows:", len(df))
    return df
