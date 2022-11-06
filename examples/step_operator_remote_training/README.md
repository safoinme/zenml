# 🧮 Train models on remote environments

This example shows how you can use the `StepOperator` class to run your training
jobs on remote backends.

The step operator defers the execution of individual steps in a pipeline to
specialized runtime environments that are optimized for Machine Learning
workloads.

## 🗺 Overview

Here we train a simple sklearn classifier on the MNIST dataset using one of
three step operators:

- AWS Sagemaker
- GCP Vertex AI
- Microsoft AzureML

Currently, step operators only work with a local orchestrator but support for
cloud orchestrators is on the way soon!

# 🖥 Run it locally

## 👣 Step-by-Step

### 📄 Prerequisites

In order to run this example, you need to install and initialize ZenML and the
necessary integrations:

```shell
# install CLI
pip install "zenml[server]"

# install ZenML integrations
zenml integration install sklearn

# pull example
zenml example pull step_operator_remote_training
cd zenml_examples/step_operator_remote_training

# initialize
zenml init

# Start the ZenServer to enable dashboard access
zenml up
```

Each type of step operator has their own prerequisites.

Before running this example, you must set up the individual cloud providers in a
certain way. The complete guide can be found in
the [docs](https://docs.zenml.io/component-gallery/step-operators/step-operators).

Please jump to the section applicable to
the step operator you would like to use:

### 🌿 Sagemaker

Sagemaker offers specialized compute instances to run your training jobs and has
a beautiful UI to track and manage your models and logs. You can now use ZenML
to submit individual steps to be run on compute instances managed by Amazon
Sagemaker.

The stack will consist of:

* The **local metadata store** which will track the configuration of your
  executions.
* The **local orchestrator** which will be executing your pipelines steps.
* An **S3 artifact store** which will be responsible for storing the
  artifacts of your pipeline.
* The **Sagemaker step operator** which will be utilized to run the training
  step on Sagemaker.

To configure resources for the step operators, please
follow [this guide](https://docs.zenml.io/component-gallery/step-operators/amazon-sagemaker)
and then proceed with the following steps:

```bash
# install ZenML integrations
zenml integration install aws s3

zenml artifact-store register s3_store \
    --flavor=s3 \
    --path=<S3_BUCKET_PATH>

# create the sagemaker step operator
zenml step-operator register sagemaker \
    --flavor=sagemaker \
    --role=<SAGEMAKER_ROLE> \
    --instance_type=<SAGEMAKER_INSTANCE_TYPE>
    --base_image=<CUSTOM_BASE_IMAGE>
    --bucket_name=<S3_BUCKET_NAME>
    --experiment_name=<SAGEMAKER_EXPERIMENT_NAME>

# register the container registry
zenml container-registry register ecr_registry --flavor=aws --uri=<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# register and activate the sagemaker stack
zenml stack register sagemaker_stack \
    -o default \
    -c ecr_registry \
    -a s3_store \
    -s sagemaker \
    --set
```

### 🪟 Microsoft AzureML

[AzureML](https://azure.microsoft.com/en-us/services/machine-learning/)
offers specialized compute instances to run your training jobs and
has a beautiful UI to track and manage your models and logs. You can now use
ZenML to submit individual steps to be run on compute instances managed by
AzureML.

The stack will consist of:

* The **local metadata store** which will track the configuration of your
  executions.
* The **local orchestrator** which will be executing your pipelines steps.
* An **azure artifact store** which will be responsible for storing the
  artifacts of your pipeline.
* The **azureml step operator** which will be utilized to run the training step
  on Azure.

To configure resources for the step operators, please
follow [this guide](https://docs.zenml.io/component-gallery/step-operators/azureml)
and then proceed with the following steps:

```bash
# install ZenML integrations
zenml integration install azure

zenml artifact-store register azure_store \
    --flavor=azure \
    --path=<AZURE_BLOB_CONTAINER_PATH>

zenml step-operator register azureml \
    --flavor=azureml \
    --subscription_id=<AZURE_SUBSCRIPTION_ID> \
    --resource_group=<AZURE_RESOURCE_GROUP> \
    --workspace_name=<AZURE_WORKSPACE_NAME> \
    --compute_target_name=<AZURE_COMPUTE_TARGET_NAME> \
    --environment_name=<AZURE_ENVIRONMENT_NAME>

zenml stack register azureml_stack \
    -o default \
    -a azure_store \
    -s azureml \
    --set
```

### 📐 GCP Vertex AI

[Vertex AI](https://cloud.google.com/vertex-ai) offers specialized compute to
run
[custom training jobs](https://cloud.google.com/vertex-ai/docs/training/custom-training)
and has a beautiful UI to track and manage your models and logs. You can now use
ZenML to submit an individual step to
run on a managed training job managed on Vertex AI.

The stack will consist of:

* The **local metadata store** which will track the configuration of your
  executions.
* The **local orchestrator** which will be executing your pipelines steps.
* A **GCP Bucket artifact store** which will be responsible for storing the
  artifacts of your pipeline.
* The **Vertex AI step operator** which will be used to run the training
  step
  on GCP.

To configure resources for the step operators, please
follow [this guide](https://docs.zenml.io/component-gallery/step-operators/gcloud-vertexai)
and then proceed with the following steps:

```bash
# install ZenML integrations
zenml integration install gcp

zenml artifact-store register gcp_store \
    --flavor=gcp \
    --path=<GCP_BUCKET_PATH>

# create the vertex step operator
zenml step-operator register vertex \
    --flavor=vertex \
    --project=<PROJECT_NAME> \
    --region=<REGION> \
    --machine_type=<MACHINE_TYPE> \
    --base_image=<CUSTOM_BASE_IMAGE>

# register the container registry
zenml container-registry register gcr_registry --flavor=gcp --uri=gcr.io/<PROJECT-ID>

# register and activate the vertex ai stack
zenml stack register vertex_training_stack \
    -o default \
    -c gcr_registry \
    -a gcp_store \
    -s vertex \
    --set
```

### ▶️ Run the Code

Now we're ready. Execute:

```shell
python run.py
```

### 🧽 Clean up

In order to clean up, delete the remaining ZenML references.

```shell
rm -rf zenml_examples
```

# 📜 Learn more

Our docs for the step operator integrations can be
found [here](https://docs.zenml.io/component-gallery/step-operators/step-operators).

If you want to learn more about step operators in general or about how to build
your own step operator in ZenML
check out our [docs](https://docs.zenml.io/component-gallery/step-operators/custom).
