_base_ = ["mmseg::deeplabv3plus/deeplabv3plus_r18b-d8_4xb2-80k_cityscapes-769x769.py"]

custom_imports = dict(
    imports=["geoai.data.human_settlements", "geoai.hooks.visualization_hook"],
    allow_failed_imports=False,
)

tile_size = 512
crop_size = (tile_size, tile_size)
data_preprocessor = dict(
    bgr_to_rgb=False,
    mean=[108.73695208, 96.00274168, 68.79838085],
    pad_val=0,
    seg_pad_val=0,
    size=crop_size,
    std=[69.4116911, 49.14411098, 40.29631649],
    type="SegDataPreProcessor",
)
data_root = "/home/sandeep/workspace/data/human-settlements"
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

metainfo = {"classes": classes}
total_images = 9680
batch_size = 20
per_epoch_iters = int(total_images // batch_size)
epochs = 10
train_cfg = dict(
    max_iters=epochs * per_epoch_iters,
    type="IterBasedTrainLoop",
    val_interval=10,  # per_epoch_iters
)

meta_keys = (
    "img_path",
    "seg_map_path",
    "ori_shape",
    "img_shape",
    "pad_shape",
    "scale_factor",
    "flip",
    "flip_direction",
    "reduce_zero_label",
    "img_meta",
)
PackSegInputs = dict(type="PackSegInputs", meta_keys=meta_keys)
train_pipeline = [PackSegInputs]
train_dataloader = dict(
    dataset=dict(
        _delete_=True,
        type=dataset_type,
        data_folder=data_root + "/train",
        tile_size=tile_size,
        pipeline=train_pipeline,
        metainfo=metainfo,
    ),
    num_workers=12,
    batch_size=batch_size,
)

val_pipeline = [PackSegInputs]
val_dataloader = dict(
    dataset=dict(
        _delete_=True,
        type=dataset_type,
        data_folder=data_root + "/valid",
        tile_size=tile_size,
        pipeline=val_pipeline,
        metainfo=metainfo,
    )
)

vis_backends = [
    dict(type="LocalVisBackend"),
    dict(
        type="WandbVisBackend",
        init_kwargs=dict(entity="sandeepgadhwal1", project="human-settlements"),
    ),
]
visualizer = dict(
    name="visualizer",
    type="SegLocalVisualizer",
    vis_backends=vis_backends,
)

default_hooks = dict(
    checkpoint=dict(by_epoch=False, interval=4000, type="CheckpointHook"),
    logger=dict(interval=10, log_metric_by_epoch=False, type="LoggerHook"),
    param_scheduler=dict(type="ParamSchedulerHook"),
    sampler_seed=dict(type="DistSamplerSeedHook"),
    timer=dict(type="IterTimerHook"),
    visualization=dict(type="CustomSegVisualizationHook", draw=True, interval=20),
)

optimizer = dict(lr=0.01, momentum=0.9, type="SGD", weight_decay=0.0005)
optim_wrapper = dict(clip_grad=None, optimizer=optimizer, type="OptimWrapper")
