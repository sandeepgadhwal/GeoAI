from osgeo import gdal
from pathlib import Path
from dataclasses import dataclass
from pyproj import CRS, Transformer
from shapely.geometry import box, Polygon
from shapely.ops import transform

@dataclass
class Image():
    ds: gdal.Dataset

    def get_dataset(self) -> gdal.Dataset:
        return self.ds

    @property
    def bbox(self) -> Polygon:
        return box(*self.bounds)
    
    @property
    def bbox_4326(self) -> Polygon:
        return transform(
            Transformer.from_crs(self.crs, 4326, always_xy=True).transform,
            self.bbox
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
        return [
            ul_x, 
            ul_y+dy*self.height, 
            ul_x+dx*self.width, 
            ul_y
        ]

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