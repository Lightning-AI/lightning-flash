<div align="center">

<img src="docs/source/_static/images/logo.svg" width="400px">


**Your PyTorch AI Factory**

---

<p align="center">
  <a href="#step-0-install">Installation</a> •
  <a href="https://lightning-flash.readthedocs.io/en/stable/?badge=stable">Docs</a> •
  <a href="#how-to-use">How to Use</a> •
  <a href="#contribute">Contribute</a> •
  <a href="#community">Community</a> •
  <a href="https://www.pytorchlightning.ai/">Website</a> •
  <a href="#license">License</a>
</p>


[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/lightning-flash)](https://pypi.org/project/lightning-flash/)
[![PyPI Status](https://badge.fury.io/py/lightning-flash.svg)](https://badge.fury.io/py/lightning-flash)
[![Slack](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://join.slack.com/t/pytorch-lightning/shared_invite/zt-pw5v393p-qRaDgEk24~EjiZNBpSQFgQ)
[![license](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/PytorchLightning/pytorch-lightning/blob/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/lightning-flash/badge/?version=latest)](https://lightning-flash.readthedocs.io/en/stable/?badge=stable)
![CI testing](https://github.com/PyTorchLightning/lightning-flash/workflows/CI%20testing/badge.svg?branch=master&event=push)
[![codecov](https://codecov.io/gh/PyTorchLightning/lightning-flash/branch/master/graph/badge.svg?token=oLuUr9q1vt)](https://codecov.io/gh/PyTorchLightning/lightning-flash)

</div>

---

## Flash Makes Complex PyTorch Recipes Simple

Flash enables you to easily configure and run complex AI recipes for [over 15 tasks across 7 data domains](https://lightning-flash.readthedocs.io/en/stable/).

<div align="center">
  <a href="https://lightning-flash.readthedocs.io/en/stable">
    <img src="https://pl-flash-data.s3.amazonaws.com/assets/banner.gif">
  </a>
</div>

## Getting stated

From PyPI:

```bash
pip install lightning-flash
```

See [our installation guide](https://lightning-flash.readthedocs.io/en/latest/installation.html) for more options.

## Flash in 3 steps

### Step 1. Load your data

All data loading in Flash is performed via a `from_*` classmethod on a `DataModule`.
Which `DataModule` to use and which `from_*` methods are available depends on the task you want to perform.
For example, for image segmentation where your data is stored in folders, you would use the [`from_folders` method of the `SemanticSegmentationData` class](https://lightning-flash.readthedocs.io/en/latest/reference/semantic_segmentation.html#from-folders):

```py
from flash.image import SemanticSegmentationData

dm = SemanticSegmentationData.from_folders(
    train_folder="data/CameraRGB",
    train_target_folder="data/CameraSeg",
    val_split=0.1,
    image_size=(256, 256),
    num_classes=21,
)

```

### Step 2: Configure your model

Our tasks come loaded with pre-trained backbones and (where applicable) heads.
You can view the available backbones to use with your task using [`available_backbones`](https://lightning-flash.readthedocs.io/en/latest/general/backbones.html).
Once you've chosen, create the model:

```py
from flash.image import SemanticSegmentation

print(SemanticSegmentation.available_heads())
# ['deeplabv3', 'deeplabv3plus', 'fpn', 'linknet', 'manet', 'pan', 'pspnet', 'unet', 'unetplusplus']

print(SemanticSegmentation.available_backbones('fpn'))
# ['densenet121', ..., 'xception'] # + 113 models

print(SemanticSegmentation.available_pretrained_weights('efficientnet-b0'))
# ['imagenet', 'advprop']

model = SemanticSegmentation(head="fpn", backbone='efficientnet-b0', pretrained="advprop", num_classes=dm.num_classes)
```

### Step 3: Finetune!

```py
from flash import Trainer

trainer = Trainer(max_epochs=3)
trainer.finetune(model, datamodule=datamodule, strategy="freeze")
```

---

## PyTorch Recipes

### Flash Transforms


Flash includes some simple augmentations for each task by default, however, you will often want to override these and control your own augmentation recipe.
To this end, Flash supports custom transformations backed by our powerful data pipeline.
You can provide transforms to be applied per sample or per batch either on or off device.
Transforms are applied to the whole data dict (typically containing "input", "target", and "metadata"),
so you can implement complex transforms (like MixUp) with ease.

The example makes use of our [`ApplyToKeys`](https://lightning-flash.readthedocs.io/en/latest/api/generated/flash.core.data.transforms.ApplyToKeys.html#flash.core.data.transforms.ApplyToKeys) utility to just apply the torchvision augmentations to the "input".
The example also uses our [`merge_transforms`](https://lightning-flash.readthedocs.io/en/latest/api/generated/flash.core.data.transforms.merge_transforms.html#flash.core.data.transforms.merge_transforms) utility to merge our augmentations with the default transforms for images (which handle resizing and converting to a tensor).

For a more advanced example, here's how you can include MixUp in your transform recipe:

```py
import torch
import numpy as np
from torchvision import transforms as T
from flash.core.data.transforms import ApplyToKeys, merge_transforms
from flash.image import ImageClassificationData
from flash.image.classification.transforms import default_transforms

def mixup(batch, alpha=1.0):
    images = batch["input"]
    targets = batch["target"].float().unsqueeze(1)

    lam = np.random.beta(alpha, alpha)
    perm = torch.randperm(images.size(0))

    batch["input"] = images * lam + images[perm] * (1 - lam)
    batch["target"] = targets * lam + targets[perm] * (1 - lam)
    return batch

train_transform = {
    "post_tensor_transform": ApplyToKeys("input", T.Compose([T.RandomHorizontalFlip(), T.ColorJitter()])),
    "per_batch_transform_on_device": mixup, # this would be applied on GPUS !
}
train_transform = merge_transforms(default_transforms((64, 64)), train_transform)

datamodule = ImageClassificationData.from_folders(
    train_folder = "./train_folder",
    predict_folder = "./predict_folder",
    train_transform=train_transform,
    ...
)
```


## Flash-Zero - no code experience !

Flash Zero is a zero-code machine learning platform built directly into lightning-flash and over [`lightning CLI`](https://pytorch-lightning.readthedocs.io/en/stable/common/lightning_cli.html).
To get started and view the available tasks, run:

```bash
  flash --help
```

For example, to train an image classifier for 10 epochs with a `resnet50` backbone on 2 gpus over you own data, you can use:

```bash
  flash image_classification --trainer.max_epochs 10 --trainer.gpus 2 --model.backbone resnet50 --train_folder {PATH_TO_DATA}
```

---

## News

- Jul 12: Flash Task-a-thon community sprint with 25+ community members
- Jul 1: [Lightning Flash 0.4](https://devblog.pytorchlightning.ai/lightning-flash-0-4-flash-serve-fiftyone-multi-label-text-classification-and-jit-support-97428276c06f)
- Jun 22: [Ushering in the New Age of Video Understanding with PyTorch](https://medium.com/pytorch/ushering-in-the-new-age-of-video-understanding-with-pytorch-1d85078e8015)
- May 24: [Lightning Flash 0.3](https://devblog.pytorchlightning.ai/lightning-flash-0-3-new-tasks-visualization-tools-data-pipeline-and-flash-registry-api-1e236ba9530)
- May 20: [Video Understanding with PyTorch](https://towardsdatascience.com/video-understanding-made-simple-with-pytorch-video-and-lightning-flash-c7d65583c37e)
- Feb 2: [Read our launch blogpost](https://pytorch-lightning.medium.com/introducing-lightning-flash-the-fastest-way-to-get-started-with-deep-learning-202f196b3b98)

__Note:__ Flash is currently being tested on real-world use cases and is in active development. Please [open an issue](https://github.com/PyTorchLightning/lightning-flash/issues/new/choose) if you find anything that isn't working as expected.

---

## Contribute!
The lightning + Flash team is hard at work building more tasks for common deep-learning use cases. But we're looking for incredible contributors like you to submit new tasks!

Join our [Slack](https://join.slack.com/t/pytorch-lightning/shared_invite/zt-pw5v393p-qRaDgEk24~EjiZNBpSQFgQ) and/or read our [CONTRIBUTING](https://github.com/PyTorchLightning/lightning-flash/blob/master/.github/CONTRIBUTING.md) guidelines to get help becoming a contributor!

---

## Community
Flash is maintained by our [core contributors](https://lightning-flash.readthedocs.io/en/latest/governance.html).

For help or questions, join our huge community on [Slack](https://join.slack.com/t/pytorch-lightning/shared_invite/zt-pw5v393p-qRaDgEk24~EjiZNBpSQFgQ)!

---

## Citations
We’re excited to continue the strong legacy of opensource software and have been inspired over the years by Caffe, Theano, Keras, PyTorch, torchbearer, and fast.ai. When/if a paper is written about this, we’ll be happy to cite these frameworks and the corresponding authors.

Flash leverages models from many different frameworks in order to cover such a wide range of domains and tasks. The full list of providers can be found in [our documentation](https://lightning-flash.readthedocs.io/en/latest/integrations/providers.html).

---

## License
Please observe the Apache 2.0 license that is listed in this repository.
