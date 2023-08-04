# Standard Library
from pathlib import Path

from osgeo import gdal
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, box
from shapely.ops import transform


class Image:
    def __init__(self, ds: gdal.Dataset) -> None:
        self.ds = ds

    def get_dataset(self) -> gdal.Dataset:
        return self.ds

    @property
    def bbox(self) -> Polygon:
        return box(*self.bounds)

    @property
    def bbox_4326(self) -> Polygon:
        return transform(
            Transformer.from_crs(self.crs, 4326, always_xy=True).transform, self.bbox
        )

    @property
    def height(self) -> int:
        return self.get_dataset().RasterYSize

    @property
    def width(self) -> int:
        return self.get_dataset().RasterXSize

    @property
    def bounds(self) -> list[float]:
        ul_x, dx, _, ul_y, _, dy = self.get_dataset().GetGeoTransform()
        return [ul_x, ul_y + dy * self.height, ul_x + dx * self.width, ul_y]

    @property
    def cell_size(self) -> list[float]:
        _, dx, _, _, _, dy = self.get_dataset().GetGeoTransform()
        return abs(dx), abs(dy)

    @property
    def crs(self) -> CRS:
        return CRS.from_wkt(self.get_dataset().GetSpatialRef().ExportToWkt())

    @classmethod
    def from_gdal(cls, ds: gdal.Dataset):
        return cls(ds)

    def save(self, path: Path):
        pass

    def get_indexer(self, tile_size: int):
        return ImageTileIndexer(self, tile_size)


class ImageTileIndexer:
    def __init__(self, image: Image, tile_size: int) -> None:
        self.image = image
        self.tile_size = tile_size

    def __len__(self):
        return self.nrows * self.ncols

    def __getitem__(self, index):
        row, col = self.index_to_row_col(index)
        # bounds =
        # return {
        #     'index': index,
        #     'row': row,
        #     'col': col,
        #     'bounds':
        # }

    def index_to_row_col(self, index: int):
        return int(index // self.ncols), index % self.ncols

    def get_bounds(self, row, col):
        pass

    def get_valid_indexes(
        self,
    ):
        pass
