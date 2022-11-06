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
from typing import cast

import click
from kserve_pytorch.pipelines.kserve_pytroch_pipelines import (
    pytorch_custom_code_pipeline,
    pytorch_inference_pipeline,
)
from kserve_pytorch.steps.deployer import kserve_pytorch_custom_deployment
from kserve_pytorch.steps.deployment_trigger import (
    DeploymentTriggerParameters,
    deployment_trigger,
)
from kserve_pytorch.steps.inference_image_loader import (
    InferenceImageLoaderStepParameters,
    inference_image_loader,
)
from kserve_pytorch.steps.predection_service_loader import (
    PredectionServiceLoaderStepParameters,
    kserve_prediction_service_loader,
)
from kserve_pytorch.steps.predictor import kserve_predictor
from kserve_pytorch.steps.pytorch_data_loader import (
    PytorchDataLoaderParameters,
    pytorch_data_loader,
)
from kserve_pytorch.steps.pytorch_evaluator import pytorch_evaluator
from kserve_pytorch.steps.pytorch_trainer import (
    PytorchTrainerParameters,
    pytorch_trainer,
)
from rich import print

from zenml.integrations.kserve.model_deployers.kserve_model_deployer import (
    KServeModelDeployer,
)
from zenml.integrations.kserve.services.kserve_deployment import (
    KServeDeploymentService,
)

DEPLOY = "deploy"
PREDICT = "predict"
DEPLOY_AND_PREDICT = "deploy_and_predict"

PYTORCH = "pytorch"
TENSORFLOW = "tensorflow"


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Choice([DEPLOY, PREDICT, DEPLOY_AND_PREDICT]),
    default="deploy_and_predict",
    help="Optionally you can choose to only run the deployment "
    "pipeline to train and deploy a model (`deploy`), or to "
    "only run a prediction against the deployed model "
    "(`predict`). By default both will be run "
    "(`deploy_and_predict`).",
)
@click.option(
    "--batch-size",
    default=4,
    help="Number of epochs for training (PyTorch hyper-parameters)",
)
@click.option(
    "--epochs",
    default=3,
    help="Number of epochs for training (PyTorch hyper-parameters)",
)
@click.option(
    "--lr",
    default=0.01,
    help="Learning rate for training (PyTorch hyper-parameters, default: 0.003)",
)
@click.option(
    "--momentum",
    default=0.5,
    help="Learning rate for training (PyTorch hyper-parameters, default: 0.003)",
)
@click.option(
    "--min-accuracy",
    default=0.80,
    help="Minimum accuracy required to deploy the model (default: 0.92)",
)
@click.option(
    "--prediction-image-url",
    "-imgurl",
    type=str,
    default="https://raw.githubusercontent.com/kserve/kserve/master/docs/samples/v1beta1/torchserve/v1/imgconv/1.png",
    required=False,
)
def main(
    config: str,
    batch_size: int,
    epochs: int,
    lr: float,
    momentum: float,
    min_accuracy: float,
    prediction_image_url: str,
):
    """Run the custom code deployment example training/deployment or inference pipeline

    Example usage:

        python run.py --config deploy_and_predict --model-deployer Seldon Core

    """
    deploy = config == DEPLOY or config == DEPLOY_AND_PREDICT
    predict = config == PREDICT or config == DEPLOY_AND_PREDICT

    deployment_pipeline_name = "pytorch_custom_code_pipeline"
    step_name = "kserve_custom_model_deployer_step"
    model_name = "kserve-pytorch-custom-model"

    model_deployer = KServeModelDeployer.get_active_model_deployer()

    if deploy:
        # Initialize and run a continuous deployment pipeline run
        pytorch_custom_code_pipeline(
            data_loader=pytorch_data_loader(
                PytorchDataLoaderParameters(
                    train_batch_size=batch_size, test_batch_size=batch_size
                )
            ),
            trainer=pytorch_trainer(
                PytorchTrainerParameters(
                    epochs=epochs, lr=lr, momentum=momentum
                )
            ),
            evaluator=pytorch_evaluator(),
            deployment_trigger=deployment_trigger(
                params=DeploymentTriggerParameters(
                    min_accuracy=min_accuracy,
                )
            ),
            deployer=kserve_pytorch_custom_deployment,
        ).run()

    if predict:
        # Initialize an inference pipeline run
        pytorch_inference_pipeline(
            inference_image_loader=inference_image_loader(
                InferenceImageLoaderStepParameters(
                    img_url=prediction_image_url,
                ),
            ),
            prediction_service_loader=kserve_prediction_service_loader(
                PredectionServiceLoaderStepParameters(
                    pipeline_name=deployment_pipeline_name,
                    step_name=step_name,
                    model_name=model_name,
                )
            ),
            predictor=kserve_predictor(),
        ).run()

    services = model_deployer.find_model_server(
        pipeline_name=deployment_pipeline_name,
        pipeline_step_name=step_name,
        model_name=model_name,
    )
    if services:
        service = cast(KServeDeploymentService, services[0])
        if service.is_running:
            print(
                f"The KServe prediction server is running remotely as a Kubernetes "
                f"service and accepts inference requests at:\n"
                f"    {service.prediction_url}\n"
                f"    With the hostname: {service.prediction_hostname}.\n"
                f"To stop the service, run "
                f"[italic green]`zenml served-models delete "
                f"{str(service.uuid)}`[/italic green]."
            )
        elif service.is_failed:
            print(
                f"The KServe prediction server is in a failed state:\n"
                f" Last state: '{service.status.state.value}'\n"
                f" Last error: '{service.status.last_error}'"
            )
    else:
        print(
            "No prediction server is currently running. The deployment "
            "pipeline must run first to train a model and deploy it. Execute "
            "the same command with the `--deploy` argument to deploy a model."
        )


if __name__ == "__main__":
    main()
