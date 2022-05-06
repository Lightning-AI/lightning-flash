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

from flash.core.utilities.imports import _CORE_TESTING
from flash.core.utilities.stability import _raise_beta_warning, beta


@beta()
class _BetaType:
    pass


@beta("_BetaTypeCustomMessage is currently in Beta.")
class _BetaTypeCustomMessage:
    pass


@beta()
def _beta_func():
    pass


@beta("_beta_func_custom_message is currently in Beta.")
def _beta_func_custom_message():
    pass


@pytest.mark.skipif(not _CORE_TESTING, reason="Not testing core.")
@pytest.mark.parametrize(
    "callable, match",
    [
        (_BetaType, "This feature is currently in Beta."),
        (_BetaTypeCustomMessage, "_BetaTypeCustomMessage is currently in Beta."),
        (_beta_func, "This feature is currently in Beta."),
        (_beta_func_custom_message, "_beta_func_custom_message is currently in Beta."),
    ],
)
def test_beta(callable, match):
    # Clear warning cache
    _raise_beta_warning.cache_clear()

    with pytest.warns(UserWarning, match=match):
        callable()
