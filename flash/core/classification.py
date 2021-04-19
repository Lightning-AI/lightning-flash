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
from typing import Any

import torch
import torch.nn.functional as F

from flash.core.model import Task
from flash.data.process import Postprocess


class ClassificationPostprocess(Postprocess):

    def per_sample_transform(self, samples: Any) -> Any:
        return torch.argmax(samples, -1).tolist()


class ClassificationTask(Task):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, default_postprocess=ClassificationPostprocess(), **kwargs)

    def to_metrics_format(self, x: torch.Tensor) -> torch.Tensor:
        return F.softmax(x, -1)
