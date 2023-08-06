# Standard Library
import math

from osgeo import gdal
from shapely.geometry import Polygon, box

from geoai.data.utils import Image


class ImageTileIndexer:
    def __init__(self, image: Image, tile_size: int) -> None:
        self.image = image
        self.tile_size = tile_size

        self.nrows = math.ceil(self.image.height / self.tile_size)
        self.ncols = math.ceil(self.image.width / self.tile_size)

    def __len__(self) -> int:
        return self.nrows * self.ncols

    def __getitem__(self, index: int) -> dict:
        row, col = self.index_to_row_col(index)
        top, left = self.index_to_offset(index)
        return {"row": row, "col": col, "offset_y": top, "offset_x": left}
        pass

    def index_to_row_col(self, index: int) -> tuple[int, int]:
        return int(index // self.ncols), index % self.ncols

    def index_to_offset(self, index: int) -> tuple[int, int]:
        row, col = self.index_to_row_col(index)
        top = row * self.tile_size
        left = col * self.tile_size
        return top, left

    def index_to_bounds(self, index: int) -> tuple[float, float, float, float]:
        top, left = self.index_to_offset(index)
        dx, dy = self.image._cell_size
        xmin, _, _, ymax = self.image.bounds
        x_min = xmin + left * dx
        y_max = ymax + top * dy
        return [
            x_min,
            y_max + dy * self.tile_size,
            x_min + dx * self.tile_size,
            y_max,
        ]

    def index_to_bbox(self, index: int) -> Polygon:
        return box(*self.index_to_bounds(index))

    def index_to_tile(self, index: int) -> Image:
        top_y, left_x = self.index_to_offset(index)
        ds = gdal.Translate(
            "",
            self.image.ds,
            options=gdal.TranslateOptions(
                format="MEM", srcWin=[left_x, top_y, self.tile_size, self.tile_size]
            ),
        )
        return Image.from_gdal(ds)
