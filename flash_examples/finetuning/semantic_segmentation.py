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
import flash
from flash.data.utils import download_data
from flash.vision import SemanticSegmentation, SemanticSegmentationData
from flash.vision.segmentation.serialization import SegmentationLabels

# 1. Download the data
# This is a Dataset with Semantic Segmentation Labels generated via CARLA self-driving simulator.
# The data was generated as part of the Lyft Udacity Challenge.
# More info here: https://www.kaggle.com/kumaresanmanickavelu/lyft-udacity-challenge
download_data(
    "https://github.com/ongchinkiat/LyftPerceptionChallenge/releases/download/v0.1/carla-capture-20180513A.zip", "data/"
)

# 2.1 Load the data
datamodule = SemanticSegmentationData.from_folders(
    train_folder="data/CameraRGB",
    train_target_folder="data/CameraSeg",
    batch_size=4,
    val_split=0.3,
    image_size=(200, 200),  # (600, 800)
    num_classes=21,
)

# 2.2 Visualise the samples
datamodule.show_train_batch(["load_sample", "post_tensor_transform"])

# 3. Build the model
model = SemanticSegmentation(
    backbone="torchvision/fcn_resnet50",
    num_classes=datamodule.num_classes,
    serializer=SegmentationLabels(visualize=True)
)

# 4. Create the trainer.
trainer = flash.Trainer(
    max_epochs=1,
    fast_dev_run=1,
)

# 5. Train the model
trainer.finetune(model, datamodule=datamodule, strategy="freeze")

predictions = model.predict([
    "data/CameraRGB/F61-1.png",
    "data/CameraRGB/F62-1.png",
    "data/CameraRGB/F63-1.png",
])

# 7. Save it!
trainer.save_checkpoint("semantic_segmentation_model.pt")
