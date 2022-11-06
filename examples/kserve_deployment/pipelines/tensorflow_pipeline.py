#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
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
from zenml.integrations.constants import KSERVE, TENSORFLOW
from zenml.pipelines import pipeline

docker_settings = DockerSettings(
    requirements=["Pillow"], required_integrations=[KSERVE, TENSORFLOW]
)


@pipeline(enable_cache=True, settings={"docker": docker_settings})
def tensorflow_training_deployment_pipeline(
    importer,
    normalizer,
    trainer,
    evaluator,
    deployment_trigger,
    model_deployer,
):
    # Link all the steps artifacts together
    x_train, y_train, x_test, y_test = importer()
    x_trained_normed, x_test_normed = normalizer(x_train=x_train, x_test=x_test)
    model = trainer(x_train=x_trained_normed, y_train=y_train)
    accuracy = evaluator(x_test=x_test_normed, y_test=y_test, model=model)
    deployment_decision = deployment_trigger(accuracy=accuracy)
    model_deployer(deployment_decision, model)


@pipeline(enable_cache=True, settings={"docker": docker_settings})
def tensorflow_inference_pipeline(
    predict_preprocessor,
    prediction_service_loader,
    predictor,
):
    # Link all the steps artifacts together
    inference_data = predict_preprocessor()
    model_deployment_service = prediction_service_loader()
    predictor(model_deployment_service, inference_data)
