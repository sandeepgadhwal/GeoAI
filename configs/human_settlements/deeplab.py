_base_ = ["mmseg::deeplabv3plus/deeplabv3plus_r18b-d8_4xb2-80k_cityscapes-769x769.py"]

custom_imports = dict(
    imports=["geoai.data.human_settlements"], allow_failed_imports=False
)

tile_size = 769
crop_size = (tile_size, tile_size)
data_preprocessor = dict(
    bgr_to_rgb=False,
    mean=[
        123.675,
        116.28,
        103.53,
    ],
    pad_val=0,
    seg_pad_val=255,
    size=crop_size,
    std=[
        58.395,
        57.12,
        57.375,
    ],
    type="SegDataPreProcessor",
)
data_root = "/home/sandeep/workspace/data/human-settlements"
data_train = data_root + ""
dataset_type = "HumanSettlementsDataset"
classes = ["background", "settlements"]
num_classes = len(classes)
model = dict(
    auxiliary_head=dict(
        num_classes=num_classes,
    ),
    data_preprocessor=data_preprocessor,
    decode_head=dict(
        num_classes=num_classes,
    ),
)

# test_pipeline = []
# test_dataloader = dict(
#     dataset=dict(
#         _delete_=True,
#         type=dataset_type,
#         pipeline=test_pipeline
#     )
# )
test_pipeline = None
test_dataloader = None
test_evaluator = None
test_cfg = None

train_cfg = dict(
    _scope_="mmseg", max_iters=40000, type="IterBasedTrainLoop", val_interval=4000
)
train_pipeline = [dict(type="PackSegInputs")]
train_dataloader = dict(
    dataset=dict(
        _delete_=True,
        type=dataset_type,
        data_folder=data_train,
        tile_size=tile_size,
        pipeline=train_pipeline,
    ),
    num_workers=8,
)

val_pipeline = [dict(type="PackSegInputs")]
val_dataloader = dict(
    dataset=dict(
        _delete_=True,
        type=dataset_type,
        data_folder=data_train,
        tile_size=tile_size,
        pipeline=val_pipeline,
    )
)
