# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import collections
import json
import os
from unittest import mock

import numpy as np
import pytest

from flash import Trainer
from flash.__main__ import main
from flash.core.utilities.imports import _ICEVISION_AVAILABLE, _IMAGE_AVAILABLE
from flash.image import InstanceSegmentation, InstanceSegmentationData

if _IMAGE_AVAILABLE:
    from PIL import Image

COCODataConfig = collections.namedtuple("COCODataConfig", "train_folder train_ann_file predict_folder")


@pytest.fixture
def coco_instances(tmpdir):
    rand_image = Image.fromarray(np.random.randint(0, 255, (64, 64, 3), dtype="uint8"))
    os.makedirs(tmpdir / "train_folder", exist_ok=True)
    os.makedirs(tmpdir / "predict_folder", exist_ok=True)

    train_folder = tmpdir / "train_folder"
    train_ann_file = tmpdir / "train_annotations.json"
    predict_folder = tmpdir / "predict_folder"

    _ = [rand_image.save(str(train_folder / f"image_{i}.png")) for i in range(1, 4)]
    _ = [rand_image.save(str(predict_folder / f"predict_image_{i}.png")) for i in range(1, 4)]
    annotations = {
        "annotations": [
            {
                "area": 50,
                "bbox": [10, 20, 5, 10],
                "category_id": 1,
                "id": 1,
                "image_id": 1,
                "iscrowd": 0,
                "segmentation": [[10, 20, 15, 20, 15, 30, 10, 30]],
            },
            {
                "area": 100,
                "bbox": [20, 30, 10, 10],
                "category_id": 2,
                "id": 2,
                "image_id": 2,
                "iscrowd": 0,
                "segmentation": [[20, 30, 30, 30, 30, 40, 20, 40]],
            },
            {
                "area": 125,
                "bbox": [10, 20, 5, 25],
                "category_id": 1,
                "id": 3,
                "image_id": 3,
                "iscrowd": 0,
                "segmentation": [[10, 20, 15, 20, 15, 45, 10, 45]],
            },
        ],
        "categories": [
            {"id": 1, "name": "cat", "supercategory": "annimal"},
            {"id": 2, "name": "dog", "supercategory": "annimal"},
        ],
        "images": [
            {"file_name": "image_1.png", "height": 64, "width": 64, "id": 1},
            {"file_name": "image_2.png", "height": 64, "width": 64, "id": 2},
            {"file_name": "image_3.png", "height": 64, "width": 64, "id": 3},
        ],
    }
    with open(train_ann_file, "w") as annotation_file:
        json.dump(annotations, annotation_file)

    return COCODataConfig(train_folder, train_ann_file, predict_folder)


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
@pytest.mark.skipif(not _ICEVISION_AVAILABLE, reason="IceVision is not installed for testing")
@pytest.mark.parametrize("backbone, head", [("resnet18_fpn", "mask_rcnn")])
def test_model(coco_instances, backbone, head):
    datamodule = InstanceSegmentationData.from_coco(
        train_folder=coco_instances.train_folder,
        train_ann_file=coco_instances.train_ann_file,
        predict_folder=coco_instances.predict_folder,
        transform_kwargs=dict(image_size=(128, 128)),
        batch_size=2,
    )

    assert datamodule.num_classes == 3
    assert datamodule.labels == ["background", "cat", "dog"]

    model = InstanceSegmentation(num_classes=datamodule.num_classes, backbone=backbone, head=head)
    trainer = Trainer(fast_dev_run=True)
    trainer.fit(model, datamodule=datamodule)
    trainer.predict(model, datamodule=datamodule)


@pytest.mark.skipif(not _IMAGE_AVAILABLE, reason="image libraries aren't installed.")
@pytest.mark.skipif(not _ICEVISION_AVAILABLE, reason="IceVision is not installed for testing")
def test_cli():
    cli_args = ["flash", "instance_segmentation", "--trainer.fast_dev_run", "True"]
    with mock.patch("sys.argv", cli_args):
        try:
            main()
        except SystemExit:
            pass
