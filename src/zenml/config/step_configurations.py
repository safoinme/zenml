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
"""Pipeline configuration classes."""
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional

from zenml.config.base_settings import BaseSettings, SettingsOrDict
from zenml.config.constants import RESOURCE_SETTINGS_KEY
from zenml.config.strict_base_model import StrictBaseModel

if TYPE_CHECKING:
    from zenml.config import ResourceSettings


class PartialArtifactConfiguration(StrictBaseModel):
    """Class representing a partial input/output artifact configuration."""

    artifact_source: Optional[str] = None
    materializer_source: Optional[str] = None


class ArtifactConfiguration(PartialArtifactConfiguration):
    """Class representing a complete input/output artifact configuration."""

    artifact_source: str
    materializer_source: str


class StepConfigurationUpdate(StrictBaseModel):
    """Class for step configuration updates."""

    name: Optional[str] = None
    enable_cache: Optional[bool] = None
    step_operator: Optional[str] = None
    experiment_tracker: Optional[str] = None
    parameters: Dict[str, Any] = {}
    settings: Dict[str, BaseSettings] = {}
    extra: Dict[str, Any] = {}

    outputs: Mapping[str, PartialArtifactConfiguration] = {}


class PartialStepConfiguration(StepConfigurationUpdate):
    """Class representing a partial step configuration."""

    name: str
    enable_cache: bool
    inputs: Mapping[str, PartialArtifactConfiguration] = {}
    outputs: Mapping[str, PartialArtifactConfiguration] = {}


class StepConfiguration(PartialStepConfiguration):
    """Step configuration class."""

    docstring: Optional[str]
    inputs: Mapping[str, ArtifactConfiguration] = {}
    outputs: Mapping[str, ArtifactConfiguration] = {}

    @property
    def resource_settings(self) -> "ResourceSettings":
        """Resource settings of this step configuration.

        Returns:
            The resource settings of this step configuration.
        """
        from zenml.config import ResourceSettings

        model_or_dict: SettingsOrDict = self.settings.get(
            RESOURCE_SETTINGS_KEY, {}
        )
        return ResourceSettings.parse_obj(model_or_dict)


class StepSpec(StrictBaseModel):
    """Specification of a pipeline."""

    source: str
    upstream_steps: List[str]

    @property
    def module_name(self) -> str:
        """The step module name.

        Returns:
            The step module name.
        """
        module_name, _ = self.source.rsplit(".", maxsplit=1)
        return module_name

    @property
    def class_name(self) -> str:
        """The step class name.

        Returns:
            The step class name.
        """
        _, class_name = self.source.rsplit(".", maxsplit=1)
        return class_name

    def __eq__(self, other: Any) -> bool:
        """Returns whether the other object is referring to the same step.

        This is the case if the other objects is a `StepSpec` with the same
        `upstream_steps` and a `source` that meets one of the following
        conditions:
            - it is the same as the `source` of this step
            - it refers to the same absolute path as the `source` of this step

        Args:
            other: The other object to compare to.

        Returns:
            True if the other object is referring to the same step.
        """
        if isinstance(other, StepSpec):

            if self.upstream_steps != other.upstream_steps:
                return False

            if self.source == other.source:
                return True

            if self.source.endswith(other.source):
                return True

            if other.source.endswith(self.source):
                return True

            return False

        return NotImplemented


class Step(StrictBaseModel):
    """Class representing a ZenML step."""

    spec: StepSpec
    config: StepConfiguration
