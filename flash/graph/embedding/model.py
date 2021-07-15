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
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple, Type, Union

import torch
from pytorch_lightning.utilities import rank_zero_warn
from torch import nn
from torch.nn import functional as F
from torchmetrics import Accuracy, Metric

from flash.core.classification import ClassificationTask
from flash.core.data.data_source import DefaultDataKeys
from flash.core.data.process import Serializer
from flash.core.model import Task
from flash.core.registry import FlashRegistry
from flash.core.utilities.imports import _TORCH_GEOMETRIC_AVAILABLE
from flash.graph.backbones import GRAPH_CLASSIFICATION_BACKBONES
from flash.graph.classification.data import GraphClassificationPreprocess

if _TORCH_GEOMETRIC_AVAILABLE:
    from torch_geometric.nn import BatchNorm, GCNConv, global_mean_pool, MessagePassing
else:
    MessagePassing = type(object)
    GCNConv = object


class GraphEmbedder(Task):
    """The ``GraphEmbedder`` is a :class:`~flash.Task` for obtaining feature vectors (embeddings) from graphs. For more
    details, see :ref:`graph_embedder`.

    Args:
        embedding_dim: Dimension of the embedded vector. ``None`` uses the default from the backbone.
        backbone: A model to use to extract image features, defaults to ``"GraphUNet"``.
        pretrained: Use a pretrained backbone, defaults to ``True``.
        loss_fn: Loss function for training and finetuning, defaults to :func:`torch.nn.functional.cross_entropy`
        optimizer: Optimizer to use for training and finetuning, defaults to :class:`torch.optim.SGD`.
        metrics: Metrics to compute for training and evaluation. Can either be an metric from the `torchmetrics`
            package, a custom metric inherenting from `torchmetrics.Metric`, a callable function or a list/dict
            containing a combination of the aforementioned. In all cases, each metric needs to have the signature
            `metric(preds,target)` and return a single scalar tensor. Defaults to :class:`torchmetrics.Accuracy`.
        learning_rate: Learning rate to use for training, defaults to ``1e-3``.
        pooling_fn: Function used to pool image to generate embeddings, defaults to :func:`torch.max`.

    """

    backbones: FlashRegistry = GRAPH_CLASSIFICATION_BACKBONES

    required_extras: str = "graph"

    def __init__(
        self,
        embedding_dim: Optional[int] = None,
        backbone: str = "GraphUNet",
        pretrained: bool = False,
        loss_fn: Callable = F.cross_entropy,
        optimizer: Type[torch.optim.Optimizer] = torch.optim.SGD,
        metrics: Union[Metric, Callable, Mapping, Sequence, None] = (Accuracy()),
        learning_rate: float = 1e-3,
        pooling_fn: Callable = torch.max
    ):
        super().__init__(
            model=None,
            loss_fn=loss_fn,
            optimizer=optimizer,
            metrics=metrics,
            learning_rate=learning_rate,
            preprocess=GraphClassificationPreprocess()
        )

        self.save_hyperparameters()
        self.backbone_name = backbone
        self.embedding_dim = embedding_dim
        assert pooling_fn in [torch.mean, torch.max]
        self.pooling_fn = pooling_fn

        self.backbone = self.backbones.get(backbone)(pretrained=pretrained)

    def forward(self, x) -> torch.Tensor:
        x = self.backbone(x)
        return x

    def training_step(self, batch: Any, batch_idx: int) -> Any:
        batch = (batch, batch.y)
        return super().training_step(batch, batch_idx)

    def validation_step(self, batch: Any, batch_idx: int) -> Any:
        batch = (batch, batch.y)
        return super().validation_step(batch, batch_idx)

    def test_step(self, batch: Any, batch_idx: int) -> Any:
        batch = (batch, batch.y)
        return super().test_step(batch, batch_idx)

    def predict_step(self, batch: Any, batch_idx: int, dataloader_idx: int = 0) -> Any:
        batch = (batch[DefaultDataKeys.INPUT])
        return super().predict_step(batch, batch_idx, dataloader_idx=dataloader_idx)
