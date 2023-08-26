# GeoAI

## Precommit
```pip install pre-commit isort```

## Conda Environment
```bash
conda activate base
conda env remove -n geoai -y
conda create -n geoai python=3.10 gdal pyarrow jupyter docker-py psycopg2 -y
conda activate geoai
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y

pip install geopandas google-cloud-storage geoalchemy2 wandb
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

## Human Settlements

Enable Weights and Biases
```bash
export WANDB_API_KEY=YOurkey
```

Train model
```bash
./dist_train.sh ./configs/human_settlements/deeplab.py --work-dir /home/sandeep/workspace/Tasks/Task-4-human-settlements/mmseg_test
```
