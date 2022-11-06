#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

from zenml.config import DockerSettings
from zenml.integrations.constants import DEEPCHECKS, SKLEARN
from zenml.pipelines import pipeline

docker_settings = DockerSettings(required_integrations=[DEEPCHECKS, SKLEARN])


@pipeline(enable_cache=False, settings={"docker": docker_settings})
def data_validation_pipeline(
    data_loader,
    trainer,
    data_validator,
    model_validator,
    data_drift_detector,
    model_drift_detector,
):
    """Links all the steps together in a pipeline"""
    df_train, df_test = data_loader()
    data_validator(dataset=df_train)
    data_drift_detector(
        reference_dataset=df_train,
        target_dataset=df_test,
    )
    model = trainer(df_train)
    model_validator(dataset=df_train, model=model)
    model_drift_detector(
        reference_dataset=df_train, target_dataset=df_test, model=model
    )
