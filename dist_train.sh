# This script is just a utility. Please modify before using it.
SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

CONFIG=$1
MMSEG_REPO=${MMSEG_REPO:-"$SCRIPTPATH/../mmsegmentation"}
GPUS=${GPUS:-1}
NNODES=${NNODES:-1}
NODE_RANK=${NODE_RANK:-0}
PORT=${PORT:-29500}
MASTER_ADDR=${MASTER_ADDR:-"127.0.0.1"}

python -m torch.distributed.launch \
    --nnodes=$NNODES \
    --node_rank=$NODE_RANK \
    --master_addr=$MASTER_ADDR \
    --nproc_per_node=$GPUS \
    --master_port=$PORT \
    $MMSEG_REPO/tools/train.py \
    $CONFIG \
    --launcher pytorch ${@:2}
