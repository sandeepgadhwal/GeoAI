# Standard Library
from pathlib import Path

from torch.utils.data import ConcatDataset, Dataset

from geoai.data.human_settlements.utils import get_human_settlements_from_sentinel_image


class HumanSettlementsDataset(ConcatDataset):
    def __init__(self, data_folder: Path, tile_size: int) -> None:
        datasets = []
        for sentinel_scene in Path(data_folder).glob("*.SAFE"):
            datasets.append(
                HumanSettlementsTile(
                    sentinel_scene, sentinel_scene.with_suffix(".gpkg")
                )
            )
        super().__init__(datasets)


class HumanSettlementsTile(Dataset):
    def __init__(self, sentinel_image: Path, human_settlements_filepath: Path) -> None:
        super().__init__()
        self.sentinel_image = sentinel_image
        self.human_settlements_filepath = human_settlements_filepath

    def __len__(self):
        pass
