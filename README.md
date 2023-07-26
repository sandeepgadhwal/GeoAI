# GeoAI

## Conda Environment
```bash
conda env remove -n geoai -y
conda create -n geoai python gdal jupyter -y
conda activate geoai
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y

pip install -U openmim
mim install mmengine "mmcv>=2.0.0"
pip install "mmsegmentation>=1.0.0"

pip install -e .
```

## Docker Image
```bash
docker build -t sandeepgadhwal/geoai:0.1 . && docker images sandeepgadhwal/geoai:0.1
docker push sandeepgadhwal/geoai:0.1
```

aria2c https://naipeuwest.blob.core.windows.net/naip/v002/de/2018/de_060cm_2018/38075/m_3807521_ne_18_060_20180810.tif --max-connection-per-server=10