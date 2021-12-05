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
from dataclasses import dataclass
from typing import Callable

import torch
from pytorch_lightning import seed_everything

from flash import Task, Trainer
from flash.core.data.input_transform import InputTransform
from flash.core.data.io.input_base import Input
from flash.core.data.new_data_module import DataModule
from flash.core.utilities.stages import RunningStage


def test_data_module():
    seed_everything(42)

    def train_fn(data):
        return data - 100

    def val_fn(data):
        return data + 100

    def test_fn(data):
        return data - 1000

    def predict_fn(data):
        return data + 1000

    class TestDataset(Input):
        pass

    @dataclass
    class TestTransform(InputTransform):
        def per_batch_transform_on_device(self) -> Callable:
            if self.training:
                return train_fn
            elif self.validating:
                return val_fn
            elif self.testing:
                return test_fn
            elif self.predicting:
                return predict_fn

    transform = TestTransform(RunningStage.TRAINING)
    assert transform._running_stage == RunningStage.TRAINING
    train_dataset = TestDataset(RunningStage.TRAINING, range(10), transform=transform)
    assert train_dataset.running_stage == RunningStage.TRAINING

    transform = TestTransform(RunningStage.VALIDATING)
    assert transform._running_stage == RunningStage.VALIDATING
    val_dataset = TestDataset(RunningStage.VALIDATING, range(10), transform=transform)
    assert val_dataset.running_stage == RunningStage.VALIDATING

    transform = TestTransform(RunningStage.TESTING)
    assert transform._running_stage == RunningStage.TESTING
    test_dataset = TestDataset(RunningStage.TESTING, range(10), transform=transform)
    assert test_dataset.running_stage == RunningStage.TESTING

    transform = TestTransform(RunningStage.PREDICTING)
    assert transform._running_stage == RunningStage.PREDICTING
    predict_dataset = TestDataset(RunningStage.PREDICTING, range(10), transform=transform)
    assert predict_dataset.running_stage == RunningStage.PREDICTING

    dm = DataModule(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        test_dataset=test_dataset,
        predict_dataset=predict_dataset,
        batch_size=2,
    )

    batch = next(iter(dm.train_dataloader()))
    assert batch.shape == torch.Size([2])
    assert batch.min() >= 0 and batch.max() < 10

    class TestModel(Task):
        def training_step(self, batch, batch_idx):
            assert sum(batch < 0) == 2

        def validation_step(self, batch, batch_idx):
            assert sum(batch > 0) == 2

        def test_step(self, batch, batch_idx):
            assert sum(batch < 500) == 2

        def predict_step(self, batch, batch_idx):
            assert sum(batch > 500) == 2
            assert torch.equal(batch, torch.tensor([1000, 1001]))

        def on_train_dataloader(self) -> None:
            pass

        def on_val_dataloader(self) -> None:
            pass

        def on_test_dataloader(self, *_) -> None:
            pass

        def on_predict_dataloader(self) -> None:
            pass

        def on_predict_end(self) -> None:
            pass

        def on_fit_end(self) -> None:
            pass

    model = TestModel(torch.nn.Linear(1, 1))
    trainer = Trainer(fast_dev_run=True)
    trainer.fit(model, dm)
    trainer.validate(model, dm)
    trainer.test(model, dm)
    trainer.predict(model, dm)

    class CustomDataModule(DataModule):
        pass

    CustomDataModule.register_flash_dataset("custom", TestDataset)
    train_dataset, *_ = DataModule.create_inputs("custom", range(10))
    assert train_dataset[0] == 0
