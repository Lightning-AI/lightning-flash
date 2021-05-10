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
from typing import Any, Mapping, Sequence, Union

from torch import nn

from flash.data.utils import convert_to_modules


class ApplyToKeys(nn.Sequential):

    def __init__(self, keys: Union[str, Sequence[str]], *args):
        super().__init__(*[convert_to_modules(arg) for arg in args])
        if isinstance(keys, str):
            keys = [keys]
        self.keys = keys

    def forward(self, x: Mapping[str, Any]) -> Mapping[str, Any]:
        keys = list(filter(lambda key: key in x, self.keys))
        inputs = [x[key] for key in keys]
        if len(inputs) > 0:
            if len(inputs) == 1:
                inputs = inputs[0]
            outputs = super().forward(inputs)
            if not isinstance(outputs, Sequence):
                outputs = (outputs, )

            result = {}
            result.update(x)
            for i, key in enumerate(keys):
                result[key] = outputs[i]
            return result
        return x


class KorniaParallelTransforms(nn.Sequential):
    """The ``KorniaParallelTransforms`` class is an ``nn.Sequential`` which will apply the given transforms to each
    input (to ``.forward``) in parallel, whilst sharing the random state (``._params``). This should be used when
    multiple elements need to be augmented in the same way (e.g. an image and corresponding segmentation mask)."""

    def __init__(self, *args):
        super().__init__(*[convert_to_modules(arg) for arg in args])

    def forward(self, inputs: Any):
        result = list(inputs) if isinstance(inputs, Sequence) else [inputs]
        for transform in self.children():
            inputs = result
            for i, input in enumerate(inputs):
                if hasattr(transform, "_params") and bool(transform._params):
                    params = transform._params
                    result[i] = transform(input, params)
                else:  # case for non random transforms
                    result[i] = transform(input)
            if hasattr(transform, "_params") and bool(transform._params):
                transform._params = None
        return result
