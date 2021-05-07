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
from typing import Callable, Dict

import torch
import torchvision
from torch import nn

from flash.data.transforms import ApplyToKeys


def default_transforms() -> Dict[str, Callable]:
    return {
        "to_tensor_transform": nn.Sequential(
            ApplyToKeys('input', torchvision.transforms.ToTensor()),
            ApplyToKeys(
                'target',
                nn.Sequential(
                    ApplyToKeys('boxes', torch.as_tensor),
                    ApplyToKeys('labels', torch.as_tensor),
                    ApplyToKeys('image_id', torch.as_tensor),
                    ApplyToKeys('area', torch.as_tensor),
                    ApplyToKeys('iscrowd', torch.as_tensor),
                )
            ),
        ),
    }
