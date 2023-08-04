# Standard Library
from pathlib import Path

from geoai.data.human_settlements import get_human_settlements_from_sentinel_image

scenes = list(Path("/home/sandeep/workspace/data/human-settlements").glob("*/*.SAFE"))
for i, scene in enumerate(scenes):
    print(f"-- Progress: {i}/{len(scenes)} | ", scene)
    out_file = scene.with_suffix(".gpkg")
    if not out_file.exists() or 1 == 1:
        df = get_human_settlements_from_sentinel_image(scene)
        if len(df) > 0:
            df.to_file(out_file)
        del df
