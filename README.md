# GeoAI

# Environment
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