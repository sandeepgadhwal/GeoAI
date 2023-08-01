from torch.utils.data import Dataset

from geoai.data.utils import TileIndexer


class TileDataset(Dataset):
    def __init__(self) -> None:
        super().__init__()
        self._indexer = None

    def get_image(self):
        raise NotImplementedError

    @property
    def indexer(self):
        if self._indexer is None:
            image = self.get_image()
            self._indexer = TileIndexer(image.footprint, image.crs, self.tile_size)
        return self._indexer
