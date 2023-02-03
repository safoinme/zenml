---
description: How to execute individual steps in Vertex AI
---

The Vertex step operator is a [step operator](./step-operators.md) flavor 
provided with the ZenML `gcp` integration that uses 
[Vertex AI](https://cloud.google.com/vertex-ai) to execute individual steps of 
ZenML pipelines.

## When to use it

You should use the Vertex step operator if:
* one or more steps of your pipeline require computing resources 
(CPU, GPU, memory) that are not provided by your orchestrator.
* you have access to Vertex AI. If you're using a different cloud provider, take 
a look at the [SageMaker](./amazon-sagemaker.md) or [AzureML](./azureml.md) 
step operators.

## How to deploy it

* Enable Vertex AI [here](https://console.cloud.google.com/vertex-ai).
* Create a [service account](https://cloud.google.com/iam/docs/service-accounts) 
with the right permissions to create Vertex AI jobs (`roles/aiplatform.admin`)
and push to the container registry (`roles/storage.admin`).

## How to use it

To use the Vertex step operator, we need:
* The ZenML `gcp` integration installed. If you haven't done so, run 
    ```shell
    zenml integration install gcp
    ```
* [Docker](https://www.docker.com) installed and running.
* Vertex AI enabled and a service account file. See the [deployment section](#how-do-you-deploy-it)
for detailed instructions.
* A [GCR container registry](../container-registries/gcloud.md) as part of our 
stack.
* (Optional) A machine type that we want to execute our steps on (this 
defaults to `n1-standard-4`). See [here](https://cloud.google.com/vertex-ai/docs/training/configure-compute#machine-types)
for a list of available machine types.
* A [remote artifact store](../artifact-stores/artifact-stores.md) as part of 
your stack. This is needed so that both your orchestration environment and 
VertexAI can read and write step artifacts. Check out the documentation page 
of the artifact store you want to use for more information on how to set that up
and configure authentication for it.

We can then register the step operator and use it in our active stack:
```shell
zenml step-operator register <NAME> \
    --flavor=vertex \
    --project=<GCP_PROJECT> \
    --region=<REGION> \
    --service_account_path=<SERVICE_ACCOUNT_PATH> \
#   --machine_type=<MACHINE_TYPE> # optionally specify the type of machine to run on

# Add the step operator to the active stack
zenml stack update -s <NAME>
```

Once you added the step operator to your active stack, you can use it to
execute individual steps of your pipeline by specifying it in the `@step` 
decorator as follows:
```python
from zenml.steps import step

@step(step_operator=<NAME>)
def trainer(...) -> ...:
    """Train a model."""
    # This step will be executed in Vertex.
```

{% hint style="info" %}
ZenML will build a Docker image called `<CONTAINER_REGISTRY_URI>/zenml:<PIPELINE_NAME>`
which includes your code and use it to run your steps in Vertex AI. Check out
[this page](../../advanced-guide/pipelines/containerization.md) if you want to 
learn more about how ZenML builds these images and how you can customize them.
{% endhint %}

### Additional configuration

For additional configuration of the Vertex step operator, you can pass
`VertexStepOperatorSettings` when defining or running your pipeline.
Check out the
[API docs](https://apidocs.zenml.io/latest/integration_code_docs/integrations-gcp/#zenml.integrations.gcp.flavors.vertex_step_operator_flavor.VertexStepOperatorSettings)
for a full list of available attributes and [this docs page](../..//advanced-guide/pipelines/settings.md)
for more information on how to specify settings.

A concrete example of using the Vertex step operator can be found 
[here](https://github.com/zenml-io/zenml/tree/main/examples/step_operator_remote_training).

For more information and a full list of configurable attributes of the Vertex 
step operator, check out the [API Docs](https://apidocs.zenml.io/latest/integration_code_docs/integrations-gcp/#zenml.integrations.gcp.step_operators.vertex_step_operator.VertexStepOperator).

### Enabling CUDA for GPU-backed hardware

Note that if you wish to use this step operator to run steps on a GPU, you will
need to follow [the instructions on this page](../../advanced-guide/pipelines/gpu-hardware.md) to ensure that it works. It
requires adding some extra settings customization and is essential to enable
CUDA for the GPU to give its full acceleration.
