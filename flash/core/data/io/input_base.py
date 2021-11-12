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
import abc
import functools
from typing import Any, Generic, Iterable, MutableMapping, Sequence, TypeVar, Union

from torch.utils.data import Dataset, IterableDataset

from flash.core.data.data_pipeline import DataPipeline
from flash.core.data.properties import Properties
from flash.core.utilities.stages import RunningStage

T = TypeVar("T")


def _has_len(data: Union[Sequence, Iterable]) -> bool:
    try:
        len(data)
        return True
    except (TypeError, NotImplementedError):
        return False


def _validate_input(input: "InputBase"):
    if input.data is not None:
        has_len = _has_len(input.data)
        if isinstance(input, Input) and not has_len:
            raise RuntimeError("`Input.data` is not a sequence with a defined length. Use `IterableInput` instead.")
        elif isinstance(input, IterableInput) and has_len:
            raise RuntimeError("`IterableInput.data` is a sequence with a defined length. Use `Input` instead.")


def _wrap_init(dct):
    if "__init__" in dct:
        fn = dct["__init__"]

        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            fn(self, *args, **kwargs)
            _validate_input(self)

        dct["__init__"] = wrapper


class _InputMeta(abc.ABCMeta):
    def __new__(mcs, name, bases, dct):
        _wrap_init(dct)
        return super().__new__(mcs, name, bases, dct)


class _IterableInputMeta(_InputMeta, type(IterableDataset)):
    def __new__(mcs, name, bases, dct):
        return super().__new__(mcs, name, bases, dct)


class InputBase(Generic[T], Properties, metaclass=_InputMeta):
    """``InputBase`` is the base class for the :class:`~flash.core.data.io.input_base.Input` and
    :class:`~flash.core.data.io.input_base.IterableInput` dataset implementations in Flash. These datasets are
    constructed via the ``load_data`` and ``load_sample`` hooks, which allow a single dataset object to include custom
    loading logic according to the running stage (e.g. train, validate, test, predict).

    Args:
        running_stage: The running stage for which the input will be used.
        *args: Any arguments that are to be passed to the ``load_data`` hook.
        **kwargs: Any additional keyword arguments to pass to the ``load_data`` hook.
    """

    def __init__(
        self,
        running_stage: RunningStage,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()

        self._running_stage = running_stage

        self.data = None
        if len(args) >= 1 and args[0] is not None:
            self.data = self._call_load_data(*args, **kwargs)

    def _call_load_data(self, *args: Any, **kwargs: Any) -> T:
        load_data = getattr(
            self, DataPipeline._resolve_function_hierarchy("load_data", self, self.running_stage, InputBase)
        )
        return load_data(*args, **kwargs)

    def _call_load_sample(self, sample: Any) -> Any:
        load_sample = getattr(
            self,
            DataPipeline._resolve_function_hierarchy(
                "load_sample",
                self,
                self.running_stage,
                InputBase,
            ),
        )
        return load_sample(sample)

    @staticmethod
    def load_data(*args: Any, **kwargs: Any) -> T:
        """The ``load_data`` hook should return a collection of samples. To reduce the memory footprint, these
        samples should typically not have been loaded. For example, an input which loads images from disk would
        only return the list of filenames here rather than the loaded images.

        Args:
            *args: Any arguments that the input requires.
            **kwargs: Any additional keyword arguments that the input requires.
        """
        return args[0]

    @staticmethod
    def load_sample(sample: MutableMapping[str, Any]) -> Any:
        """The ``load_sample`` hook is called for each ``__getitem__`` or ``__next__`` call to the dataset with a
        single sample from the output of the ``load_data`` hook as input.

        Args:
            sample: A single sample from the output of the ``load_data`` hook.
        """
        return sample

    def __getstate__(self):
        """Temporarily override pickle behaviour.

        TODO: New DataPipeline should avoid this being pickled.
        """
        state = self.__dict__.copy()
        state.pop("data")
        if "data_iter" in state:
            state.pop("data_iter")
        return state

    def __setstate__(self, newstate):
        """Temporarily override pickle behaviour.

        TODO: New DataPipeline should avoid this being pickled.
        """
        newstate["data"] = None
        self.__dict__.update(newstate)


class Input(InputBase[Sequence], Dataset):
    def __getitem__(self, index: int) -> Any:
        return self._call_load_sample(self.data[index])

    def __len__(self) -> int:
        return len(self.data) if self.data is not None else 0


class IterableInput(InputBase[Iterable], IterableDataset, metaclass=_IterableInputMeta):
    def __iter__(self):
        self.data_iter = iter(self.data)
        return self

    def __next__(self) -> Any:
        return self._call_load_sample(next(self.data_iter))
