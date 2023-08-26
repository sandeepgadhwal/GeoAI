# Standard Library
from pathlib import Path

from osgeo import gdal
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, box
from shapely.ops import transform

# from typing import Self
Self = "Self"


class Image:
    def __init__(self, ds: gdal.Dataset, meta: dict | None = None) -> None:
        self.ds = ds
        self.meta = meta
        if self.meta is None:
            self.meta = {}

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
        dx, dy = self._cell_size
        return abs(dx), abs(dy)

    @property
    def _cell_size(self) -> list[float]:
        _, dx, _, _, _, dy = self.get_dataset().GetGeoTransform()
        return dx, dy

    @property
    def crs(self) -> CRS:
        return CRS.from_wkt(self.get_dataset().GetSpatialRef().ExportToWkt())

    def save(self, path: Path) -> None:
        drv = gdal.GetDriverByName("GTiff")

        def progress_callback(complete: float, message: str, unknown: None) -> None:
            m = f"-- Progress: {complete*100} % | {message}   "
            print(m, end="\r")

        ds = drv.CreateCopy(str(path), self.ds, callback=progress_callback)
        ds.FlushCache()
        del ds
        print("Done.", " " * 25)

    @classmethod
    def from_gdal(cls, ds: gdal.Dataset) -> Self:
        return cls(ds)

    @classmethod
    def from_path(cls, path: Path) -> Self:
        return cls.from_gdal(gdal.Open(str(path)))

    @classmethod
    def from_meta(cls, meta: dict) -> Self:
        ds = gdal.Translate(
            "",
            str(meta["path"]),
            options=gdal.TranslateOptions(format="MEM", srcWin=meta["srcWin"]),
        )
        return cls(ds, meta=meta)
