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
from typing import Optional

import torch
from pytorch_lightning import Callback
from pytorch_lightning.utilities.exceptions import MisconfigurationException

from flash.core.utilities.imports import _SPARSEML_AVAILABLE

if _SPARSEML_AVAILABLE:
    from sparseml.pytorch.optim import ScheduledModifierManager
    from sparseml.pytorch.utils import ModuleExporter


class SparseMLCallback(Callback):
    """Enables SparseML aware training. Requires a recipe to run during training.

    Args:
        recipe_path: Path to a SparseML compatible yaml recipe.
            More information at https://docs.neuralmagic.com/sparseml/source/recipes.html
    """

    def __init__(self, recipe_path):
        if not _SPARSEML_AVAILABLE:
            raise MisconfigurationException("SparseML has not be installed, install with pip install sparseml")
        self.manager = ScheduledModifierManager.from_yaml(recipe_path)

    def on_fit_start(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
        optimizer = trainer.optimizers

        if len(optimizer) > 1:
            raise MisconfigurationException("SparseML only supports training with one optimizer.")
        optimizer = optimizer[0]
        print(self._num_training_steps_per_epoch(trainer))
        optimizer = self.manager.modify(pl_module, optimizer, self._num_training_steps_per_epoch(trainer), epoch=0)
        trainer.optimizers = [optimizer]

    def on_fit_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
        self.manager.finalize(pl_module)

    def _num_training_steps_per_epoch(self, trainer: "pl.Trainer") -> int:
        """Total training steps inferred from datamodule and devices."""
        if isinstance(trainer.limit_train_batches, int) and trainer.limit_train_batches != 0:
            dataset_size = trainer.limit_train_batches
        elif isinstance(trainer.limit_train_batches, float):
            # limit_train_batches is a percentage of batches
            dataset_size = len(trainer.datamodule.train_dataloader())
            dataset_size = int(dataset_size * trainer.limit_train_batches)
        else:
            dataset_size = len(trainer.datamodule.train_dataloader())

        num_devices = max(1, trainer.num_gpus, trainer.num_processes)
        if trainer.tpu_cores:
            num_devices = max(num_devices, trainer.tpu_cores)

        effective_batch_size = trainer.accumulate_grad_batches * num_devices
        max_estimated_steps = dataset_size // effective_batch_size

        if trainer.max_steps and trainer.max_steps < max_estimated_steps:
            return trainer.max_steps
        return max_estimated_steps

    @staticmethod
    def export_to_sparse_onnx(
        model: "pl.LightningModule", output_dir: str, sample_batch: Optional[torch.Tensor] = None
    ):
        exporter = ModuleExporter(model, output_dir=output_dir)
        sample_batch = sample_batch if sample_batch is not None else model.example_input_array
        exporter.export_onnx(sample_batch=sample_batch)
