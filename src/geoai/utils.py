import requests
from pathlib import Path
import shutil

def download_file(url: str, out_path: Path, file_name: str | None = None, overwrite=False, exists_ok=False):
    if not out_path.exists():
        raise Exception("output directory does not exist.")
    
    if file_name is None:
        file_name = url.split('/')[-1]
    file_path = out_path / file_name
    file_path_temp = file_path.with_suffix('.tmp')
    if file_path.exists():
        if exists_ok:
            return file_path
        if not overwrite:
            raise Exception("File already exists on disk")
    with requests.get(url, stream=True) as r:
        # with open(file_path_temp, 'wb') as f:
        #     shutil.copyfileobj(r.raw, f)
        r.raise_for_status()
        with open(file_path_temp, 'wb') as f:
            for chunk in r.iter_content(chunk_size=10*2**20): 
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk: 
                f.write(chunk)

    shutil.move(file_path_temp, file_path)

    return file_path