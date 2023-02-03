#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.


import pytest
from pydantic import ValidationError

from zenml.enums import StackComponentType
from zenml.models.component_models import ComponentBaseModel
from zenml.models.constants import STR_FIELD_MAX_LENGTH


def test_component_base_model_fails_with_long_flavor():
    """Test that the component base model fails with long flavor strings."""
    long_flavor = "a" * (STR_FIELD_MAX_LENGTH + 1)
    with pytest.raises(ValidationError):
        ComponentBaseModel(
            name="abc",
            type=StackComponentType.ANNOTATOR,
            flavor=long_flavor,
            configuration={},
        )
