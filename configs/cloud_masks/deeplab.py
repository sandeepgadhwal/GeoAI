_base_ = ["mmseg::deeplabv3plus/deeplabv3plus_r18b-d8_4xb2-80k_cityscapes-769x769.py"]

custom_imports = dict(
    imports=["geoai.data.cloud_masks", "geoai.hooks.visualization_hook"],
    allow_failed_imports=False,
)

tile_size = 250
crop_size = (tile_size, tile_size)
data_preprocessor = dict(
    bgr_to_rgb=False,
    mean=[2315.30928245, 2460.91824484, 2424.48493796],
    pad_val=0,
    seg_pad_val=0,
    size=crop_size,
    std=[1370.40949558, 1372.04831436, 1484.2985879],
    type="SegDataPreProcessor",
)
data_root = (
    "/home/sandeep/workspace/competitions/MaskingCloudsinSatelliteImageries/data/split"
)
dataset_type = "CloudMaskDataset"
classes = ["background", "clouds"]
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

total_images_train = 800
batch_size = 64
per_epoch_iters = int(total_images_train // batch_size)
epochs = 100
train_cfg = dict(
    max_iters=epochs * per_epoch_iters,
    type="IterBasedTrainLoop",
    val_interval=10 * per_epoch_iters,
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
    ),
    num_workers=12,
    batch_size=batch_size,
)

val_pipeline = [PackSegInputs]
val_dataloader = dict(
    dataset=dict(
        _delete_=True,
        type=dataset_type,
        data_folder=data_root + "/val",
        tile_size=tile_size,
        pipeline=val_pipeline,
    )
)

vis_backends = [
    dict(type="LocalVisBackend"),
    dict(
        type="WandbVisBackend",
        init_kwargs=dict(entity="sandeepgadhwal1", project="cloud_masks"),
    ),
]
visualizer = dict(
    name="visualizer",
    type="SegLocalVisualizer",
    vis_backends=vis_backends,
)

default_hooks = dict(
    checkpoint=dict(
        by_epoch=False, interval=per_epoch_iters * 10, type="CheckpointHook"
    ),
    logger=dict(interval=1, log_metric_by_epoch=False, type="LoggerHook"),
    param_scheduler=dict(type="ParamSchedulerHook"),
    sampler_seed=dict(type="DistSamplerSeedHook"),
    timer=dict(type="IterTimerHook"),
    visualization=dict(type="CustomSegVisualizationHook", draw=True, interval=10),
)

optimizer = dict(lr=0.01, momentum=0.9, type="SGD", weight_decay=0.0005)
optim_wrapper = dict(clip_grad=None, optimizer=optimizer, type="OptimWrapper")
