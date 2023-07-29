from shapely.geometry import box, Polygon
import numpy as np
from pyproj import CRS
from dataclasses import dataclass

# @dataclass
# class Tile():
#     index: int
#     row: int
#     col: int
#     bounds: list[float]
#     geometry: Polygon


# class TileIndexer():
#     def __init__(self, footprint: Polygon, crs: CRS, tile_size: int) -> None:
#         self.footprint = footprint
#         self.crs = crs
#         self.tile_size = tile_size
#         self.bounds = footprint.bounds

#     def __len__(self):
#         return self.nrows*self.ncols
    
#     def __getitem__(self, index):
#         row, col = self.index_to_row_col(index)
#         bounds = 
#         return {
#             'index': index,
#             'row': row,
#             'col': col,
#             'bounds': 
#         }

#     def index_to_row_col(self, index: int):
#         return int(index // self.ncols), index % self.ncols

#     def get_bounds(self, row, col):
#         se

