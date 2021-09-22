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
from typing import Any, Callable, Dict, Optional

import numpy as np
import torch
from pytorch_lightning import LightningDataModule
from pytorch_lightning.utilities.exceptions import MisconfigurationException
from torch.utils.data import DataLoader, Dataset, random_split

from flash import DataModule
from flash.core.data.auto_dataset import BaseAutoDataset
from flash.core.data.data_pipeline import DataPipeline
from flash.core.utilities.imports import _BAAL_AVAILABLE, requires

if _BAAL_AVAILABLE:
    from baal.active.dataset import ActiveLearningDataset
    from baal.active.heuristics import AbstractHeuristic, BALD
else:

    class AbstractHeuristic:
        pass

    class BALD(AbstractHeuristic):
        def __init__(self, reduction: Callable):
            super().__init__()


def dataset_to_non_labelled_tensor(dataset: BaseAutoDataset) -> torch.tensor:
    return torch.zeros(len(dataset))


def filter_unlabelled_data(dataset: BaseAutoDataset) -> Dataset:
    return dataset


def train_val_split(dataset: ActiveLearningDataset, val_size=0.1):
    L = len(dataset)
    train_size = int(L * (1 - val_size))
    val_size = L - train_size
    return random_split(dataset, [train_size, val_size], generator=torch.Generator().manual_seed(42))


class ActiveLearningDataModule(LightningDataModule):
    @requires("baal")
    def __init__(
        self,
        labelled: Optional[DataModule] = None,
        heuristic: "AbstractHeuristic" = BALD(reduction=np.mean),
        map_dataset_to_labelled: Optional[Callable] = dataset_to_non_labelled_tensor,
        filter_unlabelled_data: Optional[Callable] = filter_unlabelled_data,
        num_label_randomly: int = 5,
        val_split: Optional[float] = None,
    ):
        """The `ActiveLearningDataModule` handles data manipulation for ActiveLearning.

        Args:
            labelled: DataModule containing labelled train data for research use-case.
                The labelled data would be masked.
            heuristic: Sorting algorithm used to rank samples on how likely they can help with model performance.
            map_dataset_to_labelled: Function used to emulate masking on labelled dataset.
            filter_unlabelled_data: Function used to filter the unlabelled data while computing uncertainties.
            num_label_randomly: Number of samples to randomly labelled from the uncertaintie scores
            val_split: Float to split train dataset into train and validation set.
        """
        self.labelled = labelled
        self.heuristic = heuristic
        self.map_dataset_to_labelled = map_dataset_to_labelled
        self.filter_unlabelled_data = filter_unlabelled_data
        self.num_label_randomly = num_label_randomly
        self.val_split = val_split
        self._dataset: Optional[ActiveLearningDataset] = None

        if not self.labelled:
            raise MisconfigurationException("The labelled `datamodule` should be provided.")

        if not self.labelled.num_classes:
            raise MisconfigurationException("The labelled dataset should be labelled")

        if self.labelled and (
            self.labelled._val_ds is not None
            or self.labelled._test_ds is not None
            or self.labelled._predict_ds is not None
        ):
            raise MisconfigurationException("The labelled `datamodule` should have only train data.")

        self._dataset = ActiveLearningDataset(
            self.labelled._train_ds, labelled=self.map_dataset_to_labelled(self.labelled._train_ds)
        )

        if not self.val_split or not self.has_labelled_data:
            self.val_dataloader = None
        elif self.val_split < 0 or self.val_split > 1:
            raise MisconfigurationException("The `val_split` should a float between 0 and 1.")

    @property
    def has_labelled_data(self) -> bool:
        return self._dataset.n_labelled > 0

    @property
    def has_unlabelled_data(self) -> bool:
        return self._dataset.n_unlabelled > 0

    @property
    def num_classes(self) -> Optional[int]:
        return getattr(self.labelled, "num_classes", None) or getattr(self.unlabelled, "num_classes", None)

    @property
    def data_pipeline(self) -> "DataPipeline":
        return self.labelled.data_pipeline

    def train_dataloader(self) -> "DataLoader":
        if self.val_split:
            self.labelled._train_ds = train_val_split(self._dataset, self.val_split)[0]
        else:
            self.labelled._train_ds = self._dataset

        if self.has_labelled_data and self.val_split:
            self.val_dataloader = self._val_dataloader

        return self.labelled.train_dataloader()

    def _val_dataloader(self) -> "DataLoader":
        self.labelled._val_ds = train_val_split(self._dataset, self.val_split)[1]
        return self.labelled._val_dataloader()

    def predict_dataloader(self) -> "DataLoader":
        self.labelled._train_ds = self.filter_unlabelled_data(self._dataset.pool)
        return self.labelled.train_dataloader()

    def label(self, uncertainties: Any = None, indices=None):
        if uncertainties and indices:
            raise MisconfigurationException(
                "The `uncertainties` and `indices` are mutually exclusive, pass only of one them."
            )
        if uncertainties:
            indices = np.argsort(uncertainties)
            if self._dataset is not None:
                self._dataset.labelled[indices[-self.num_label_randomly :]] = True
        else:
            self._dataset.label_randomly(self.num_label_randomly)

    def state_dict(self) -> Dict[str, torch.Tensor]:
        return self._dataset.state_dict()

    def load_state_dict(self, state_dict) -> None:
        return self._dataset.load_state_dict(state_dict)
