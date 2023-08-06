# Standard Library
from pathlib import Path

from mmengine.dataset import BaseDataset
from torch.utils.data import ConcatDataset

from geoai.data.utils import Image, ImageTileIndexer


class HumanSettlementsDataset(ConcatDataset):
    def __init__(self, data_folder: Path, tile_size: int) -> None:
        datasets = []
        for sentinel_scene in Path(data_folder).glob("*.SAFE"):
            datasets.append(
                HumanSettlementsTile(
                    sentinel_scene,
                    sentinel_scene.with_suffix(".gpkg"),
                    tile_size=tile_size,
                )
            )
        super().__init__(datasets)


class HumanSettlementsTile(BaseDataset):
    def __init__(
        self, sentinel_image: Path, human_settlements_filepath: Path, tile_size: int
    ) -> None:
        super().__init__()
        self.sentinel_image = sentinel_image
        self.human_settlements_filepath = human_settlements_filepath
        self.tile_size = tile_size

    def __len__(self) -> ImageTileIndexer:
        return len(self.indexer)

    def get_image(self) -> Image:
        im = Image.from_path.Open(f"{self.sentinel_image}/MTD_MSIL2A.xml")
        ds_RGB_path = im.ds.GetSubDatasets()[-1][0]
        return Image.from_path(ds_RGB_path)

    @property
    def indexer(self) -> ImageTileIndexer:
        return ImageTileIndexer(self.get_image(), self.tile_size)
