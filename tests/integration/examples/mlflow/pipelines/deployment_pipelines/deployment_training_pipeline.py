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

from pipelines.tracking_pipeline.tracking_pipeline import (
    mlflow_tracking_pipeline,
)

from zenml import pipeline
from zenml.config import DockerSettings
from zenml.constants import DEFAULT_SERVICE_START_STOP_TIMEOUT
from zenml.integrations.constants import MLFLOW, TENSORFLOW
from zenml.integrations.mlflow.steps import mlflow_model_deployer_step

docker_settings = DockerSettings(required_integrations=[MLFLOW, TENSORFLOW])


@pipeline(enable_cache=True, settings={"docker": docker_settings})
def mlflow_train_deploy_pipeline(
    epochs: int = 1,
    lr: float = 0.001,
    workers: int = 1,
    timeout: int = DEFAULT_SERVICE_START_STOP_TIMEOUT,
):
    model = mlflow_tracking_pipeline(epochs=epochs, lr=lr)
    mlflow_model_deployer_step(
        model=model,
        workers=workers,
        timeout=timeout,
    )
