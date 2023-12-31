from __future__ import annotations

# Standard Library
import json
from pathlib import Path

import numpy as np
import torch
from matplotlib import pyplot as plt
from mmengine.dataset import BaseDataset
from mmseg.registry import DATASETS
from torch.utils.data import ConcatDataset, Subset

from geoai.data.utils import Image, ImageTileIndexer


@DATASETS.register_module()
class CloudMaskDataset(ConcatDataset):
    def __init__(
        self,
        data_folder: Path,
        tile_size: int = 512,
        pipeline: list[dict] | None = None,
        metainfo: dict | None = None,
        label_coverage_threshold: float = 0.01,
        image_dir: str = "image",
        mask_dir: str = "mask",
    ) -> None:
        self.label_coverage_threshold = label_coverage_threshold
        self.data_folder = Path(data_folder)
        scenes = list((self.data_folder / image_dir).rglob("*.tif"))
        datasets = []
        for i, scene in enumerate(scenes):
            idx = scene.stem.split("_")[-1]
            label_file = Path(data_folder) / mask_dir / f"train_mask_{idx}.tif"
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

    def get_stats(self, force_recalculate: bool = False) -> dict:
        image_stats_file = self.data_folder / "cloud_mask_image_stats.json"
        if not image_stats_file.exists() or force_recalculate:
            image_stats = self.calculate_image_stats()
            for k in image_stats:
                image_stats[k] = image_stats[k].tolist()
            with open(image_stats_file, "w") as f:
                json.dump(image_stats, f)
        else:
            with open(image_stats_file) as f:
                image_stats = json.load(f)
            for k in image_stats:
                image_stats[k] = np.array(image_stats[k], dtype=np.float32)
        return {"image_stats": image_stats}

    def calculate_image_stats(self) -> dict:
        mean_store = []
        variance_store = []
        for i, dataset in enumerate(self.datasets):
            m = f"Calculating stats: ({i}/{len(self.datasets)})"
            print(m, " " * 5, end="\r")
            if self.label_coverage_threshold > 0:
                dataset = dataset.dataset
            stats = dataset.get_image().get_stats()
            mean_store.append(stats["mean"])
            variance_store.append(stats["variance"])
        print("")

        std = np.stack(variance_store).mean(axis=0) ** 0.5
        mean = np.stack(mean_store).mean(axis=0)
        return {"mean": mean, "std": std}


class CloudMaskTile(dict):
    def plot(
        self,
        ax: plt.axes = None,
        alpha: float = 0.7,
        percent_clip: list[int] | None = None,
    ) -> plt.axes:
        if percent_clip is None:
            percent_clip = [0, 100]
        if ax is None:
            _, ax = plt.subplots()
        min, max = np.percentile(self["img"].reshape(-1, 3), percent_clip, axis=0)
        arr = (self["img"] - min) / (max - min)
        arr = np.clip(arr, 0, 1)
        ax.imshow(arr)
        color_map = np.pad(self["color_map"], ((0, 0), (0, 1)))
        color_map[1:, 3] = int(alpha * 255)
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
        super().__init__(serialize_data=False, pipeline=pipeline, metainfo=metainfo)

    def __len__(self) -> int:
        return len(self.indexer)

    @property
    def indexer(self) -> ImageTileIndexer:
        return ImageTileIndexer(self.get_image(), self.tile_size)

    def full_init(self) -> None:
        super().full_init()
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
        arr = np.transpose(image_tile.ds.ReadAsArray(), (1, 2, 0))
        if arr.dtype == np.uint16:
            arr = arr.astype(np.int32)
        res["img"] = arr
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
