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
from typing import Optional, Sequence

import torch.nn as nn

from flash.core.registry import FlashRegistry
from flash.core.utilities.imports import _VISSL_AVAILABLE

if _VISSL_AVAILABLE:
    from classy_vision.dataset.transforms import TRANSFORM_REGISTRY


def simclr_transform(
    total_num_crops: int = 2,
    num_crops: Sequence[int] = [2],
    size_crops: Sequence[int] = [224],
    crop_scales: Sequence[Sequence[float]] = [[0.4, 1]],
    gaussian_blur: bool = True,
    jitter_strength: float = 1.0,
    normalize: Optional[nn.Module] = None,
) -> nn.Module:
    """For simclr, barlow twins and moco."""
    transform = TRANSFORM_REGISTRY["multicrop_ssl_transform"](
        total_num_crops=total_num_crops,
        num_crops=num_crops,
        size_crops=size_crops,
        crop_scales=crop_scales,
        gaussian_blur=gaussian_blur,
        jitter_strength=jitter_strength,
        normalize=normalize,
    )

    return transform


def swav_transform(
    total_num_crops: int = 8,
    num_crops: Sequence[int] = [2, 6],
    size_crops: Sequence[int] = [224, 96],
    crop_scales: Sequence[Sequence[float]] = [[0.4, 1], [0.05, 0.4]],
    gaussian_blur: bool = True,
    jitter_strength: float = 1.0,
    normalize: Optional[nn.Module] = None,
) -> nn.Module:
    """For swav and dino."""
    transform = TRANSFORM_REGISTRY["multicrop_ssl_transform"](
        total_num_crops=total_num_crops,
        num_crops=num_crops,
        size_crops=size_crops,
        crop_scales=crop_scales,
        gaussian_blur=gaussian_blur,
        jitter_strength=jitter_strength,
        normalize=normalize,
    )

    return transform


def register_vissl_transforms(register: FlashRegistry):
    for transform in (simclr_transform, swav_transform):
        register(transform)
