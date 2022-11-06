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
"""Initialization for the ZenML MLflow integration.

The MLflow integrations currently enables you to use MLflow tracking as a
convenient way to visualize your experiment runs within the MLflow UI.
"""
from typing import List, Type

from zenml.enums import StackComponentType
from zenml.integrations.constants import MLFLOW
from zenml.integrations.integration import Integration
from zenml.models import FlavorModel
from zenml.stack import Flavor

MLFLOW_MODEL_DEPLOYER_FLAVOR = "mlflow"
MLFLOW_MODEL_EXPERIMENT_TRACKER_FLAVOR = "mlflow"


class MlflowIntegration(Integration):
    """Definition of MLflow integration for ZenML."""

    NAME = MLFLOW
    REQUIREMENTS = [
        "mlflow>=1.2.0,<1.26.0",
        "mlserver>=0.5.3",
        "mlserver-mlflow>=0.5.3",
    ]

    @classmethod
    def activate(cls) -> None:
        """Activate the MLflow integration."""
        from zenml.integrations.mlflow import services  # noqa

    @classmethod
    def flavors(cls) -> List[Type[Flavor]]:
        """Declare the stack component flavors for the MLflow integration.

        Returns:
            List of stack component flavors for this integration.
        """
        from zenml.integrations.mlflow.flavors import (
            MLFlowExperimentTrackerFlavor,
            MLFlowModelDeployerFlavor,
        )

        return [MLFlowModelDeployerFlavor, MLFlowExperimentTrackerFlavor]


MlflowIntegration.check_installation()
