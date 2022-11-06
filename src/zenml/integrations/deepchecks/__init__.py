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
"""Deepchecks integration for ZenML.

The Deepchecks integration provides a way to validate your data in your pipelines.
It includes a way to detect data anomalies and define checks to ensure quality of
data.

The integration includes custom materializers to store Deepchecks `SuiteResults` and
a visualizer to visualize the results in an easy way on a notebook and in your
browser.
"""

from typing import List, Type

from zenml.enums import StackComponentType
from zenml.integrations.constants import DEEPCHECKS
from zenml.integrations.integration import Integration
from zenml.models import FlavorModel
from zenml.stack import Flavor

DEEPCHECKS_DATA_VALIDATOR_FLAVOR = "deepchecks"


class DeepchecksIntegration(Integration):
    """Definition of [Deepchecks](https://github.com/deepchecks/deepchecks) integration for ZenML."""

    NAME = DEEPCHECKS
    REQUIREMENTS = ["deepchecks[vision]==0.8.0", "torchvision==0.11.2"]
    APT_PACKAGES = ["ffmpeg", "libsm6", "libxext6"]

    @staticmethod
    def activate() -> None:
        """Activate the Deepchecks integration."""
        from zenml.integrations.deepchecks import materializers  # noqa
        from zenml.integrations.deepchecks import visualizers  # noqa

    @classmethod
    def flavors(cls) -> List[Type[Flavor]]:
        """Declare the stack component flavors for the Deepchecks integration.

        Returns:
            List of stack component flavors for this integration.
        """
        from zenml.integrations.deepchecks.flavors import (
            DeepchecksDataValidatorFlavor,
        )

        return [DeepchecksDataValidatorFlavor]


DeepchecksIntegration.check_installation()
