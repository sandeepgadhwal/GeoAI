# Standard Library
from pathlib import Path

import numpy as np
import torch
from matplotlib import pyplot as plt
from mmengine.dataset import BaseDataset
from mmseg.registry import DATASETS
from osgeo import gdal, ogr
from torch.utils.data import ConcatDataset, Subset

from geoai.data.utils import Image, ImageTileIndexer


def get_color_map() -> np.array:
    return np.array([[0, 0, 0, 0], [245, 66, 66, 255]], dtype=np.uint8)


@DATASETS.register_module()
class HumanSettlementsDataset(ConcatDataset):
    def __init__(
        self,
        data_folder: Path,
        tile_size: int = 512,
        pipeline: list[dict] | None = None,
        metainfo: dict | None = None,
        label_coverage_threshold: float = 0.01,
    ) -> None:
        sentinel_scenes = list(Path(data_folder).rglob("*.SAFE"))
        labels = {
            **{x.name: x for x in Path(data_folder).rglob("**/QA/*.gpkg")},
            **{x.name: x for x in Path(data_folder).rglob("**/fakeQA/*.gpkg")},
        }
        datasets = []
        for i, sentinel_scene in enumerate(sentinel_scenes):
            label_file = sentinel_scene.with_suffix(".gpkg").name
            if label_file in labels:
                dataset = HumanSettlementsScene(
                    sentinel_scene,
                    labels[label_file],
                    tile_size=tile_size,
                    pipeline=pipeline,
                    metainfo=metainfo,
                )
                if label_coverage_threshold > 0:
                    subset = dataset.get_subset(label_coverage_threshold)
                else:
                    subset = dataset
                datasets.append(subset)
                m = f"Prepared Dataset: ({i}/{len(sentinel_scenes)}) {sentinel_scene} filtered ({len(subset)}/{len(dataset)})"
                print(m, " " * 5, end="\r")
        print("")
        super().__init__(datasets)
        if label_coverage_threshold > 0:
            self.metainfo = self.datasets[0].dataset.metainfo
        else:
            self.metainfo = self.datasets[0].metainfo


class HumanSettlementsTile(dict):
    def plot(self, ax: plt.axes = None, alpha: float = 0.7) -> plt.axes:
        if ax is None:
            _, ax = plt.subplots()
        ax.imshow(self["img"])
        color_map = np.copy(self["color_map"])
        color_map[:, 3] = int(alpha * 255)
        sem_seg = color_map[self["gt_seg_map"]]
        ax.imshow(sem_seg)
        return ax


class HumanSettlementsScene(BaseDataset):
    METAINFO = {
        "classes": ["background", "settlements"],
        "palette": [[0, 0, 0], [245, 66, 66]],
    }

    def __init__(
        self,
        sentinel_image: Path,
        human_settlements_filepath: Path,
        tile_size: int = 512,
        pipeline: list[dict] | None = None,
        metainfo: dict | None = None,
    ) -> None:
        self.sentinel_image = Path(sentinel_image)
        self.human_settlements_filepath = Path(human_settlements_filepath)
        self.tile_size = tile_size

        self._image_path = None
        self._image = None
        self._label = None

        super().__init__(serialize_data=False, pipeline=pipeline, metainfo=metainfo)

    def __len__(self) -> ImageTileIndexer:
        return len(self.indexer)

    @property
    def indexer(self) -> ImageTileIndexer:
        return ImageTileIndexer(self.get_image(), self.tile_size)

    def full_init(self) -> None:
        super().full_init()
        # _ = self.get_image()
        # _ = self.get_label()
        self.color_map = np.array(self.metainfo["palette"], dtype=np.uint8)

    def load_data_list(self) -> list:
        return []

    def get_image_path(self) -> Path:
        if self._image_path is None:
            im = Image.from_path(f"{self.sentinel_image}/MTD_MSIL2A.xml")
            ds_RGB_path = im.ds.GetSubDatasets()[-1][0]
            self._image_path = ds_RGB_path
        return self._image_path

    def get_image(self) -> Image:
        if self._image is None:
            self._image = Image.from_path(self.get_image_path())
        return self._image

    def get_image_tile(self, index: int) -> Image:
        top_y, left_x = self.indexer.index_to_offset(index)
        meta = {
            "path": self.get_image_path(),
            "srcWin": [left_x, top_y, self.tile_size, self.tile_size],
        }
        return Image.from_meta(meta=meta)

    def get_label_tile(self, index: int) -> Image:
        return self._get_label_tile(self.get_image_tile(index))

    def _get_label_tile(self, image_tile: Image) -> Image:
        label_ds = ogr.Open(str(self.human_settlements_filepath))
        lyr_name = label_ds.GetLayer().GetDescription()
        label_layer = label_ds.ExecuteSQL(
            f"SELECT * FROM {lyr_name}", ogr.CreateGeometryFromWkb(image_tile.bbox.wkb)
        )
        label_tile = get_label_like(image_tile)
        label_tile.ds
        _ = gdal.RasterizeLayer(label_tile.ds, [1], label_layer, burn_values=[1])
        del label_ds, label_layer
        return label_tile

    def get_label(self) -> Image:
        """
        Not to be used within a data loader.
        """
        if self._label is None:
            label_ds = ogr.Open(str(self.human_settlements_filepath))
            label_layer = label_ds.GetLayer()
            label_image = get_label_like(self.get_image())
            _ = gdal.RasterizeLayer(label_image.ds, [1], label_layer, burn_values=[1])
            self._label = label_image
        return self._label

    def get_data_info(self, index: int) -> HumanSettlementsTile:
        res = self.indexer[0]
        res["img_path"] = self.sentinel_image
        res["seg_map_path"] = self.human_settlements_filepath
        image_tile = self.get_image_tile(index)
        label_tile = self._get_label_tile(image_tile)
        res["color_map"] = self.color_map
        res["img"] = np.transpose(image_tile.ds.ReadAsArray(), (1, 2, 0))
        res["ori_shape"] = res["img"].shape[:2]
        res["img_meta"] = image_tile.meta
        res["gt_seg_map"] = label_tile.ds.ReadAsArray()
        return HumanSettlementsTile(res)

    def get_label_coverage(self) -> torch.Tensor:
        label_coverage = torch.zeros(len(self), dtype=torch.float)
        label = self.get_label()
        for i in range(len(self)):
            top, left = self.indexer.index_to_offset(i)
            ysize, xsize = self.indexer.index_to_valid_pixels(i)
            label_pixels = label.ds.ReadAsArray(left, top, xsize, ysize).sum()
            total_pixels = self.tile_size * self.tile_size
            label_coverage[i] = label_pixels / total_pixels
        return label_coverage

    def get_subset(self, label_coverage_threshold: float = 0.01) -> Subset:
        indexes = torch.argwhere(self.get_label_coverage() > label_coverage_threshold)[
            :, 0
        ].tolist()
        return Subset(self, indexes)


def get_label_like(image: Image) -> Image:
    ds = gdal.GetDriverByName("MEM").Create(
        "", image.width, image.height, bands=1, eType=gdal.GDT_Byte
    )
    ds.SetGeoTransform(image.ds.GetGeoTransform())
    ds.SetSpatialRef(image.ds.GetSpatialRef())
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(0)
    return Image.from_gdal(ds)
