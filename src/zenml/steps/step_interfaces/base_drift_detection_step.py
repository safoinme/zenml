#  Copyright (c) ZenML GmbH 2021. All Rights Reserved.
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
"""Base drift detection step."""

from abc import abstractmethod
from typing import Any

from zenml.artifacts import DataArtifact
from zenml.steps import BaseParameters, BaseStep, StepContext


class BaseDriftDetectionParameters(BaseParameters):
    """Base class for drift detection step parameters."""


class BaseDriftDetectionStep(BaseStep):
    """Base step implementation for any drift detection step implementation."""

    @abstractmethod
    def entrypoint(  # type: ignore[override]
        self,
        reference_dataset: DataArtifact,
        comparison_dataset: DataArtifact,
        params: BaseDriftDetectionParameters,
        context: StepContext,
    ) -> Any:
        """Base entrypoint for any drift detection implementation.

        Args:
            reference_dataset: The reference dataset.
            comparison_dataset: The comparison dataset.
            params: The parameters for the step.
            context: The context for the step.

        Returns:
            The result of the drift detection.
        """
