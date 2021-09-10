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
from typing import Any, Optional, Dict, Type, Union

import torch
from torch.optim.lr_scheduler import _LRScheduler

from flash.core.adapter import AdapterTask
from flash.core.registry import FlashRegistry
from flash.core.utilities.imports import _VISSL_AVAILABLE

if _VISSL_AVAILABLE:
    from flash.image.embedding.backbones import IMAGE_EMBEDDER_BACKBONES
    from flash.image.embedding.strategies import IMAGE_EMBEDDER_STRATEGIES
else:
    IMAGE_EMBEDDER_BACKBONES = FlashRegistry("backbones")
    IMAGE_EMBEDDER_STRATEGIES = FlashRegistry("embedder_training_strategies")


class ImageEmbedder(AdapterTask):
    """The ``ImageEmbedder`` is a :class:`~flash.Task` for obtaining feature vectors (embeddings) from images. For
    more details, see :ref:`image_embedder`.

    Args:
        embedding_dim: Dimension of the embedded vector. ``None`` uses the default from the backbone.
        backbone: A model to use to extract image features, defaults to ``"swav-imagenet"``.
        pretrained: Use a pretrained backbone, defaults to ``True``.
        loss_fn: Loss function for training and finetuning, defaults to :func:`torch.nn.functional.cross_entropy`
        optimizer: Optimizer to use for training and finetuning, defaults to :class:`torch.optim.SGD`.
        optimizer_kwargs: Additional kwargs to use when creating the optimizer (if not passed as an instance).
        scheduler: The scheduler or scheduler class to use.
        scheduler_kwargs: Additional kwargs to use when creating the scheduler (if not passed as an instance).
        metrics: Metrics to compute for training and evaluation. Can either be an metric from the `torchmetrics`
            package, a custom metric inherenting from `torchmetrics.Metric`, a callable function or a list/dict
            containing a combination of the aforementioned. In all cases, each metric needs to have the signature
            `metric(preds,target)` and return a single scalar tensor. Defaults to :class:`torchmetrics.Accuracy`.
        learning_rate: Learning rate to use for training, defaults to ``1e-3``.
        pooling_fn: Function used to pool image to generate embeddings, defaults to :func:`torch.max`.
    """

    training_strategy_registry: FlashRegistry = IMAGE_EMBEDDER_STRATEGIES
    backbones_registry: FlashRegistry = IMAGE_EMBEDDER_BACKBONES

    required_extras: str = "image_extras"

    def __init__(
        self,
        training_strategy: str,
        embedding_dim: Optional[int] = None,
        backbone: str = "resnet50",
        pretrained: bool = True,
        optimizer: Type[torch.optim.Optimizer] = torch.optim.SGD,
        optimizer_kwargs: Optional[Dict[str, Any]] = None,
        scheduler: Optional[Union[Type[_LRScheduler], str, _LRScheduler]] = None,
        scheduler_kwargs: Optional[Dict[str, Any]] = None,
        learning_rate: float = 1e-3,
        **kwargs: Any,
    ):
        self.save_hyperparameters()

        backbone, num_features = self.backbones_registry.get(backbone)(pretrained=pretrained, **kwargs)

        # TODO: add linear layer to backbone to get num_feature -> embedding_dim before applying heads
        # assert embedding_dim == num_features

        metadata = self.training_strategy_registry.get(training_strategy, with_metadata=True)
        loss_fn, head = metadata["fn"](**kwargs)
        hooks = metadata["metadata"]["hooks"]

        adapter = metadata["metadata"]["adapter"].from_task(
            self,
            loss_fn=loss_fn,
            backbone=backbone,
            embedding_dim=embedding_dim,
            head=head,
            hooks=hooks,
            **kwargs,
        )

        super().__init__(adapter=adapter)
