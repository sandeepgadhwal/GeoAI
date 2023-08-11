from torch.utils.data import Dataset

from geoai.data.utils import Image, ImageTileIndexer


class TileDataset(Dataset):
    def __init__(self) -> None:
        super().__init__()
        self._indexer = None

    def get_image(self) -> Image:
        raise NotImplementedError

    @property
    def indexer(self) -> ImageTileIndexer:
        raise NotImplementedError
