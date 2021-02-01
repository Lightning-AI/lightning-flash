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
import pytest
import torch
from pytorch_lightning.utilities.exceptions import MisconfigurationException
from torch import nn
from torch.nn import functional as F

from flash import ClassificationTask, Trainer
from flash.core.finetuning import NoFreeze
from tests.core.test_model import DummyDataset


@pytest.mark.parametrize(
    "finetune_strategy", ['no_freeze', 'freeze', 'freeze_unfreeze', 'unfreeze_milestones', None, 'cls', 'chocolat']
)
def test_finetuning(tmpdir: str, finetune_strategy):
    model = nn.Sequential(nn.Flatten(), nn.Linear(28 * 28, 10), nn.LogSoftmax())
    train_dl = torch.utils.data.DataLoader(DummyDataset())
    val_dl = torch.utils.data.DataLoader(DummyDataset())
    task = ClassificationTask(model, F.nll_loss)
    trainer = Trainer(fast_dev_run=True, default_root_dir=tmpdir)
    if finetune_strategy == "cls":
        finetune_strategy = NoFreeze()
    if finetune_strategy == 'chocolat':
        with pytest.raises(MisconfigurationException, match="finetune_strategy should be within"):
            trainer.finetune(task, train_dl, val_dl, finetune_strategy=finetune_strategy)
    elif finetune_strategy is None:
        with pytest.raises(MisconfigurationException, match="finetune_strategy should"):
            trainer.finetune(task, train_dl, val_dl, finetune_strategy=finetune_strategy)
    else:
        trainer.finetune(task, train_dl, val_dl, finetune_strategy=finetune_strategy)
