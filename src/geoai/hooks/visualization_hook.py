# Standard Library
from typing import Sequence

import numpy as np
from mmengine.runner import Runner
from mmseg.engine.hooks.visualization_hook import SegVisualizationHook
from mmseg.registry import HOOKS
from mmseg.structures import SegDataSample

from geoai.data.utils import Image


@HOOKS.register_module()
class CustomSegVisualizationHook(SegVisualizationHook):
    def _after_iter(
        self,
        runner: Runner,
        batch_idx: int,
        data_batch: dict,
        outputs: Sequence[SegDataSample],
        mode: str = "val",
    ) -> None:
        """Run after every ``self.interval`` validation iterations.

        Args:
            runner (:obj:`Runner`): The runner of the validation process.
            batch_idx (int): The index of the current batch in the val loop.
            data_batch (dict): Data from dataloader.
            outputs (Sequence[:obj:`SegDataSample`]): Outputs from model.
            mode (str): mode (str): Current mode of runner. Defaults to 'val'.
        """
        if self.draw is False or mode == "train":
            return

        if self.every_n_inner_iters(batch_idx, self.interval):
            for i, output in enumerate(outputs):
                # try:
                img_meta = data_batch["data_samples"][i].img_meta

                # Read Image
                img = Image.from_meta(img_meta).ds.ReadAsArray()

                # Image to channel last
                img = np.transpose(img, (1, 2, 0))

                # Get min max percentiles for clip normalization
                min, max = np.percentile(img.reshape(-1, 3), [2, 98], axis=0)

                # Min max normalization
                img = (img - min) / (max - min)

                # Clip outliers
                img = np.clip(img, 0, 1)

                srcWin_ = "_".join([str(x) for x in img_meta["srcWin"]])
                window_name = f"""{mode}_{output.img_path.stem}_{srcWin_}"""

                self._visualizer.add_datasample(
                    window_name,
                    img,
                    data_sample=output,
                    show=self.show,
                    wait_time=self.wait_time,
                    step=runner.iter,
                )
                # except Exception as e:
                #     print(e)

                #     # Standard Library
                #     import pdb

                #     pdb.set_trace()
