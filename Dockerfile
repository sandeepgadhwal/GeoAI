FROM ubuntu:latest

RUN apt-get update && apt-get install -y wget g++ && rm -rf /var/lib/apt/lists/*

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/mininconda.sh && \
    sh /tmp/mininconda.sh -b -p /miniconda && \
    rm /tmp/mininconda.sh && \
    rm -rf /miniconda/pkgs

ENV PATH=/miniconda/bin:$PATH
ARG PATH=/miniconda/bin:$PATH

RUN . /miniconda/etc/profile.d/conda.sh && \
    conda install pytorch-cuda=11.8 -c pytorch -c nvidia -y && \
    conda clean -a -y && \
    rm -rf /miniconda/pkgs

RUN . /miniconda/etc/profile.d/conda.sh && \
    conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia -y && \
    conda clean -a -y && \
    rm -rf /miniconda/pkgs

RUN . /miniconda/etc/profile.d/conda.sh && \
    conda install gdal pyarrow -y && \
    pip install geopandas --no-cache-dir && \
    conda clean -a -y && \
    rm -rf /miniconda/pkgs

RUN . /miniconda/etc/profile.d/conda.sh && \
    pip install -U openmim --no-cache-dir && \
    mim install mmengine "mmcv>=2.0.0"  --no-cache-dir

RUN . /miniconda/etc/profile.d/conda.sh && \
    pip install "mmsegmentation>=1.0.0" mmdet --no-cache-dir

ADD ./ /geoai
RUN . /miniconda/etc/profile.d/conda.sh && \
    pip install -e /geoai

RUN chmod +x /geoai/entrypoint.sh

ENTRYPOINT ["/geoai/entrypoint.sh"]