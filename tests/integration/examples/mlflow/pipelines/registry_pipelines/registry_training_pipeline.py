#  Copyright (c) ZenML GmbH 2020. All Rights Reserved.
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
from zenml.integrations.constants import MLFLOW, TENSORFLOW
from zenml.integrations.mlflow.steps.mlflow_registry import (
    mlflow_register_model_step,
)
from zenml.model_registries.base_model_registry import (
    ModelRegistryModelMetadata,
)

docker_settings = DockerSettings(required_integrations=[MLFLOW, TENSORFLOW])


@pipeline(enable_cache=False, settings={"docker": docker_settings})
def mlflow_registry_training_pipeline(
    epochs: int = 1,
    lr: float = 0.001,
    num_run: int = 1,
):
    model = mlflow_tracking_pipeline(epochs=epochs, lr=lr)
    mlflow_register_model_step(
        model=model,
        name="tensorflow-mnist-model",
        metadata=ModelRegistryModelMetadata(
            lr=lr, epochs=epochs, optimizer="Adam"
        ),
        description=(
            f"Run #{num_run} of the mlflow_registry_training_pipeline."
        ),
    )
