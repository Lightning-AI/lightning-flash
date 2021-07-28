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
import torch

from flash.image.backbones import IMAGE_CLASSIFIER_BACKBONES


# Paper: Emerging Properties in Self-Supervised Vision Transformers
# https://arxiv.org/abs/2104.14294 from Mathilde Caron and al. (29 Apr 2021)
# weights from https://github.com/facebookresearch/dino
def dino_deits16(*_, **__):
    backbone = torch.hub.load('facebookresearch/dino:main', 'dino_deits16')
    return backbone, 384


def dino_deits8(*_, **__):
    backbone = torch.hub.load('facebookresearch/dino:main', 'dino_deits8')
    return backbone, 384


def dino_vitb16(*_, **__):
    backbone = torch.hub.load('facebookresearch/dino:main', 'dino_vitb16')
    return backbone, 768


def dino_vitb8(*_, **__):
    backbone = torch.hub.load('facebookresearch/dino:main', 'dino_vitb8')
    return backbone, 768


IMAGE_CLASSIFIER_BACKBONES(dino_deits16)
IMAGE_CLASSIFIER_BACKBONES(dino_deits8)
IMAGE_CLASSIFIER_BACKBONES(dino_vitb16)
IMAGE_CLASSIFIER_BACKBONES(dino_vitb8)
