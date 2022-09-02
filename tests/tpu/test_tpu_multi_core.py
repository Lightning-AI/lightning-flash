
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
import os

import pytest
import torch.nn.functional as F
from pytorch_lightning.accelerators.tpu import TPUAccelerator
from torch.utils.data import DataLoader

import flash
from tests.core.test_finetuning import DummyDataset, TestTaskWithFinetuning
from tests.helpers.boring_model import BoringDataModule, BoringModel
from tests.tpu.test_tpu import _assert_state_finished

# Current state of TPU with Flash (as of v0.8 release)
# Multi Core:
# TPU Training, Validation are supported, but prediction is not.

@pytest.mark.skipif(not os.getenv("FLASH_RUN_TPU_TESTS", "0") == "1", reason="Should run with TPU test")
def test_tpu_finetuning():
    task = TestTaskWithFinetuning(loss_fn=F.nll_loss)

    trainer = flash.Trainer(max_epochs=1, devices=8, accelerator="tpu")
    assert isinstance(trainer.accelerator, TPUAccelerator)

    ds = DummyDataset()
    trainer.finetune(model=task, train_dataloader=DataLoader(ds))
    _assert_state_finished(trainer, "fit")


@pytest.mark.skipif(not os.getenv("FLASH_RUN_TPU_TESTS", "0") == "1", reason="Should run with TPU test")
def test_tpu_prediction():
    boring_model = BoringModel()
    boring_dm = BoringDataModule()

    trainer = flash.Trainer(fast_dev_run=True, devices=8, accelerator="tpu")
    assert isinstance(trainer.accelerator, TPUAccelerator)

    trainer.fit(model=boring_model, datamodule=boring_dm)
    _assert_state_finished(trainer, "fit")
    trainer.validate(model=boring_model, datamodule=boring_dm)
    _assert_state_finished(trainer, "validate")
    trainer.test(model=boring_model, datamodule=boring_dm)
    _assert_state_finished(trainer, "test")

    with pytest.raises(NotImplementedError, match="not supported"):
        trainer.predict(model=boring_model, datamodule=boring_dm)
    return
