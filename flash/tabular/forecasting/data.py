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
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Sequence, Mapping

from flash.core.data.callback import BaseDataFetcher
from flash.core.data.data_module import DataModule
from flash.core.data.data_source import DataSource, DefaultDataKeys, DefaultDataSources
from flash.core.data.process import Deserializer, Postprocess, Preprocess
from flash.core.data.properties import ProcessState
from flash.core.utilities.imports import _PANDAS_AVAILABLE, _FORECASTING_AVAILABLE, requires_extras

if _PANDAS_AVAILABLE:
    from pandas.core.frame import DataFrame
else:
    DataFrame = object

if _FORECASTING_AVAILABLE:
    from pytorch_forecasting import TimeSeriesDataSet


@dataclass(unsafe_hash=True, frozen=True)
class TimeSeriesDataSetState(ProcessState):
    """
    A :class:`~flash.core.data.properties.ProcessState` containing ``labels``,
    a mapping from class index to label.
    """

    time_series_dataset: Optional[TimeSeriesDataSet]


class TabularForecastingDataFrameDataSource(DataSource[DataFrame]):

    @requires_extras("tabular")
    def __init__(
            self,
            time_idx: str,
            target: Union[str, List[str]],
            group_ids: List[str],
            **data_source_kwargs: Any
    ):
        self.time_idx = time_idx
        self.target = target
        self.group_ids = group_ids
        self.data_source_kwargs = data_source_kwargs
        super().__init__()

        self.dataset = None

    def load_data(self, data: DataFrame, dataset: Optional[Any] = None):
        if self.training:
            dataset.time_series_dataset = TimeSeriesDataSet(
                data, time_idx=self.time_idx, group_ids=self.group_ids, target=self.target, **self.data_source_kwargs
            )
            self.set_state(TimeSeriesDataSetState(dataset.time_series_dataset))
            return dataset.time_series_dataset
        else:
            train_time_series_dataset = self.get_state(TimeSeriesDataSetState).time_series_dataset
            eval_time_series_dataset = TimeSeriesDataSet.from_dataset(
                    train_time_series_dataset, data,
                    min_prediction_idx=train_time_series_dataset.index.time.max() + 1,
                    stop_randomization=True
            )
            return eval_time_series_dataset

    @staticmethod
    def load_sample(sample: Mapping[str, Any], dataset: Optional[Any] = None) -> Any:
        return {DefaultDataKeys.INPUT: sample[0], DefaultDataKeys.TARGET: sample[1]}


class TabularForecastingPreprocess(Preprocess):

    def __init__(
            self,
            train_transform: Optional[Dict[str, Callable]] = None,
            val_transform: Optional[Dict[str, Callable]] = None,
            test_transform: Optional[Dict[str, Callable]] = None,
            predict_transform: Optional[Dict[str, Callable]] = None,
            deserializer: Optional[Deserializer] = None,
            **data_source_kwargs: Any
    ):
        self.data_source_kwargs = data_source_kwargs
        super().__init__(
            train_transform=train_transform,
            val_transform=val_transform,
            test_transform=test_transform,
            predict_transform=predict_transform,
            data_sources={
                DefaultDataSources.DATAFRAME: TabularForecastingDataFrameDataSource(
                    **data_source_kwargs
                ),
            },
            deserializer=deserializer
        )

    def get_state_dict(self, strict: bool = False) -> Dict[str, Any]:
        return {
            **self.transforms,
            **self.data_source_kwargs
        }

    @classmethod
    def load_state_dict(cls, state_dict: Dict[str, Any], strict: bool = True) -> 'Preprocess':
        return cls(**state_dict)


class TabularForecastingData(DataModule):
    """Data module for tabular tasks"""

    preprocess_cls = TabularForecastingPreprocess

    @property
    def data_source(self) -> DataSource:
        return self._data_source

    @classmethod
    def from_data_frame(
            cls,
            time_idx: str,
            target: Union[str, List[str]],
            group_ids: List[str],
            train_data_frame: Optional[DataFrame] = None,
            val_data_frame: Optional[DataFrame] = None,
            test_data_frame: Optional[DataFrame] = None,
            predict_data_frame: Optional[DataFrame] = None,
            train_transform: Optional[Dict[str, Callable]] = None,
            val_transform: Optional[Dict[str, Callable]] = None,
            test_transform: Optional[Dict[str, Callable]] = None,
            predict_transform: Optional[Dict[str, Callable]] = None,
            data_fetcher: Optional[BaseDataFetcher] = None,
            preprocess: Optional[Preprocess] = None,
            val_split: Optional[float] = None,
            batch_size: int = 4,
            num_workers: Optional[int] = None,
            **preprocess_kwargs: Any,
    ):
        """Creates a :class:`~flash.tabular.data.TabularData` object from the given data frames.

        Args:
            group_ids:
            target:
            time_idx:
            train_data_frame: The pandas ``DataFrame`` containing the training data.
            val_data_frame: The pandas ``DataFrame`` containing the validation data.
            test_data_frame: The pandas ``DataFrame`` containing the testing data.
            predict_data_frame: The pandas ``DataFrame`` containing the data to use when predicting.
            train_transform: The dictionary of transforms to use during training which maps
                :class:`~flash.core.data.process.Preprocess` hook names to callable transforms.
            val_transform: The dictionary of transforms to use during validation which maps
                :class:`~flash.core.data.process.Preprocess` hook names to callable transforms.
            test_transform: The dictionary of transforms to use during testing which maps
                :class:`~flash.core.data.process.Preprocess` hook names to callable transforms.
            predict_transform: The dictionary of transforms to use during predicting which maps
                :class:`~flash.core.data.process.Preprocess` hook names to callable transforms.
            data_fetcher: The :class:`~flash.core.data.callback.BaseDataFetcher` to pass to the
                :class:`~flash.core.data.data_module.DataModule`.
            preprocess: The :class:`~flash.core.data.data.Preprocess` to pass to the
                :class:`~flash.core.data.data_module.DataModule`. If ``None``, ``cls.preprocess_cls``
                will be constructed and used.
            val_split: The ``val_split`` argument to pass to the :class:`~flash.core.data.data_module.DataModule`.
            batch_size: The ``batch_size`` argument to pass to the :class:`~flash.core.data.data_module.DataModule`.
            num_workers: The ``num_workers`` argument to pass to the :class:`~flash.core.data.data_module.DataModule`.
            preprocess_kwargs: Additional keyword arguments to use when constructing the preprocess. Will only be used
                if ``preprocess = None``.

        Returns:
            The constructed data module.

        Examples::

            data_module = TabularData.from_data_frame(
                "categorical_input",
                "numerical_input",
                "target",
                train_data_frame=train_data,
            )

        """

        return cls.from_data_source(
            time_idx=time_idx,
            target=target,
            group_ids=group_ids,
            data_source=DefaultDataSources.DATAFRAME,
            train_data=train_data_frame,
            val_data=val_data_frame,
            test_data=test_data_frame,
            predict_data=predict_data_frame,
            train_transform=train_transform,
            val_transform=val_transform,
            test_transform=test_transform,
            predict_transform=predict_transform,
            data_fetcher=data_fetcher,
            preprocess=preprocess,
            val_split=val_split,
            batch_size=batch_size,
            num_workers=num_workers,
            **preprocess_kwargs,
        )
