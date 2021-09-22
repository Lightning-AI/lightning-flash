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
from typing import Any, Dict, List, Optional, Type, Union

import torch
import warnings
from torch.optim.lr_scheduler import _LRScheduler

from flash.core.adapter import AdapterTask
from flash.core.data.data_source import DefaultDataKeys
from flash.core.data.transforms import ApplyToKeys
from flash.core.registry import FlashRegistry
from flash.core.data.states import (
    CollateFn,
    ToTensorTransform,
    PostTensorTransform,
    PreTensorTransform,
)
from flash.core.utilities.imports import _VISSL_AVAILABLE

if _VISSL_AVAILABLE:
    import classy_vision
    import classy_vision.generic.distributed_util

    from flash.image.embedding.backbones import IMAGE_EMBEDDER_BACKBONES
    from flash.image.embedding.strategies import IMAGE_EMBEDDER_STRATEGIES
    from flash.image.embedding.transforms import IMAGE_EMBEDDER_TRANSFORMS

    # patch this to avoid classy vision/vissl based distributed training
    classy_vision.generic.distributed_util.get_world_size = lambda: 1
else:
    IMAGE_EMBEDDER_BACKBONES = FlashRegistry("backbones")
    IMAGE_EMBEDDER_STRATEGIES = FlashRegistry("embedder_training_strategies")
    IMAGE_EMBEDDER_TRANSFORMS = FlashRegistry("embedder_transforms")


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

    training_strategies: FlashRegistry = IMAGE_EMBEDDER_STRATEGIES
    backbones: FlashRegistry = IMAGE_EMBEDDER_BACKBONES
    transforms: FlashRegistry = IMAGE_EMBEDDER_TRANSFORMS

    required_extras: str = "image"

    def __init__(
        self,
        training_strategy: str,
        head: str,
        pretraining_transform: str,
        backbone: str = "resnet",
        pretrained: bool = True,
        optimizer: Type[torch.optim.Optimizer] = torch.optim.SGD,
        optimizer_kwargs: Optional[Dict[str, Any]] = None,
        scheduler: Optional[Union[Type[_LRScheduler], str, _LRScheduler]] = None,
        scheduler_kwargs: Optional[Dict[str, Any]] = None,
        learning_rate: float = 1e-3,
        backbone_kwargs: Optional[Dict[str, Any]] = None,
        training_strategy_kwargs: Optional[Dict[str, Any]] = None,
        pretraining_transform_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.save_hyperparameters()

        if backbone_kwargs is None:
            backbone_kwargs = {}

        if training_strategy_kwargs is None:
            training_strategy_kwargs = {}

        backbone, _ = self.backbones.get(backbone)(pretrained=pretrained, **backbone_kwargs)

        metadata = self.training_strategies.get(training_strategy, with_metadata=True)
        loss_fn, head, hooks = metadata["fn"](head=head, **training_strategy_kwargs)

        adapter = metadata["metadata"]["adapter"].from_task(
            self,
            loss_fn=loss_fn,
            backbone=backbone,
            head=head,
            hooks=hooks,
        )

        super().__init__(
            adapter=adapter,
            optimizer=optimizer,
            optimizer_kwargs=optimizer_kwargs,
            scheduler=scheduler,
            scheduler_kwargs=scheduler_kwargs,
            learning_rate=learning_rate,
        )

        transform, collate_fn = self.transforms.get(pretraining_transform)(**pretraining_transform_kwargs)
        to_tensor_transform = ApplyToKeys(
            DefaultDataKeys.INPUT,
            transform,
        )

        self.adapter.set_state(CollateFn(collate_fn))
        self.adapter.set_state(ToTensorTransform(to_tensor_transform))
        self.adapter.set_state(PostTensorTransform(None))
        self.adapter.set_state(PreTensorTransform(None))

        warnings.warn("Warning: VISSL ImageEmbedder overrides any user provided transforms"
                      " with pre-defined transforms for the training strategy.")

    def on_train_start(self) -> None:
        self.adapter.on_train_start()

    def on_train_epoch_end(self) -> None:
        self.adapter.on_train_epoch_end()

    def on_train_batch_end(self, outputs: Any, batch: Any, batch_idx: int, dataloader_idx: int) -> None:
        self.adapter.on_train_batch_end(outputs, batch, batch_idx, dataloader_idx)

    @classmethod
    def available_training_strategies(cls) -> List[str]:
        registry: Optional[FlashRegistry] = getattr(cls, "training_strategies", None)
        if registry is None:
            return []
        return registry.available_keys()
