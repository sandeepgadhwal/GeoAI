# Standard Library
from pathlib import Path

import numpy as np
import torch
from matplotlib import pyplot as plt
from mmengine.dataset import BaseDataset
from torch.utils.data import ConcatDataset, Subset

from geoai.data.utils import Image, ImageTileIndexer


class CloudMaskDataset(ConcatDataset):
    def __init__(
        self,
        data_folder: Path,
        tile_size: int = 512,
        pipeline: list[dict] | None = None,
        metainfo: dict | None = None,
        label_coverage_threshold: float = 0.01,
    ) -> None:
        scenes = list((Path(data_folder) / "train_true_color").rglob("*.tif"))
        datasets = []
        for i, scene in enumerate(scenes):
            idx = scene.stem.split("_")[-1]
            label_file = Path(data_folder) / "train_mask" / f"train_mask_{idx}.tif"
            dataset = CloudMaskScene(
                scene,
                label_file,
                tile_size=tile_size,
                pipeline=pipeline,
                metainfo=metainfo,
            )
            if label_coverage_threshold > 0:
                subset = dataset.get_subset(label_coverage_threshold)
            else:
                subset = dataset
            datasets.append(subset)
            m = f"Prepared Dataset: ({i}/{len(scenes)}) {scene} filtered ({len(subset)}/{len(dataset)})"
            print(m, " " * 5, end="\r")
        print("")
        super().__init__(datasets)
        if label_coverage_threshold > 0:
            self.metainfo = self.datasets[0].dataset.metainfo
        else:
            self.metainfo = self.datasets[0].metainfo


class CloudMaskTile(dict):
    def plot(self, ax: plt.axes = None, alpha: float = 0.7) -> plt.axes:
        if ax is None:
            _, ax = plt.subplots()
        min, max = np.percentile(self["img"].reshape(-1, 3), [2, 98], axis=0)
        arr = (self["img"] - min) / (max - min)
        arr = np.clip(arr, 0, 1)
        ax.imshow(arr)
        color_map = np.pad(self["color_map"], ((0, 0), (0, 1)))
        color_map[:, 3] = int(alpha * 255)
        sem_seg = color_map[self["gt_seg_map"]]
        ax.imshow(sem_seg)
        return ax


class CloudMaskScene(BaseDataset):
    METAINFO = {
        "classes": ["background", "cloud"],
        "palette": [[0, 0, 0], [245, 66, 66]],
    }

    def __init__(
        self,
        image: Path,
        mask: Path,
        tile_size: int = 512,
        pipeline: list[dict] | None = None,
        metainfo: dict | None = None,
    ) -> None:
        self.image_filepath = Path(image)
        self.mask_filepath = Path(mask)
        self.tile_size = tile_size

        # self._image_path = None
        # self._image = None
        # self._label = None

        super().__init__(serialize_data=False, pipeline=pipeline, metainfo=metainfo)

    def __len__(self) -> int:
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

    def get_image(self) -> Image:
        return Image.from_path(self.image_filepath)

    def get_image_tile(self, index: int) -> Image:
        top_y, left_x = self.indexer.index_to_offset(index)
        meta = {
            "path": self.image_filepath,
            "srcWin": [left_x, top_y, self.tile_size, self.tile_size],
        }
        return Image.from_meta(meta=meta)

    def get_label_tile(self, index: int) -> Image:
        top_y, left_x = self.indexer.index_to_offset(index)
        meta = {
            "path": self.mask_filepath,
            "srcWin": [left_x, top_y, self.tile_size, self.tile_size],
        }
        return Image.from_meta(meta=meta)

    def get_data_info(self, index: int) -> CloudMaskTile:
        res = self.indexer[0]
        res["img_path"] = self.image_filepath
        res["seg_map_path"] = self.mask_filepath
        image_tile = self.get_image_tile(index)
        label_tile = self.get_label_tile(index)
        res["color_map"] = self.color_map
        res["img"] = np.transpose(image_tile.ds.ReadAsArray(), (1, 2, 0))
        res["ori_shape"] = res["img"].shape[:2]
        res["img_meta"] = image_tile.meta
        res["gt_seg_map"] = label_tile.ds.ReadAsArray()
        return CloudMaskTile(res)

    def get_label_coverage(self) -> torch.Tensor:
        label_coverage = torch.zeros(len(self), dtype=torch.float)
        for idx in range(len(self)):
            label_pixels = self.get_label_tile(idx).ds.ReadAsArray().sum()
            total_pixels = self.tile_size * self.tile_size
            label_coverage[idx] = label_pixels / total_pixels
        return label_coverage

    def get_subset(self, label_coverage_threshold: float = 0.01) -> Subset:
        indexes = torch.argwhere(self.get_label_coverage() > label_coverage_threshold)[
            :, 0
        ].tolist()
        return Subset(self, indexes)
