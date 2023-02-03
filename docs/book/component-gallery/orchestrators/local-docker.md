---
description: How to orchestrate pipelines locally in Docker
---

The local Docker orchestrator is an [orchestrator](./orchestrators.md) flavor 
which comes built-in with ZenML and runs your pipelines locally using Docker.

## When to use it

You should use the local Docker orchestrator if:
* you want the steps of your pipeline to run locally in isolated environments.
* you want to debug issues that happen when running your pipeline in Docker 
containers without waiting and paying for remote infrastructure.

## How to deploy it

To use the local Docker orchestrator, you only need to have [Docker](https://www.docker.com/) 
installed and running.

## How to use it

To use the local Docker orchestrator, we can register it and use it in our 
active stack:

```shell
zenml orchestrator register <ORCHESTRATOR_NAME> --flavor=local_docker

# Register and activate a stack with the new orchestrator
zenml stack register <STACK_NAME> -o <ORCHESTRATOR_NAME> ... --set
```

You can now run any ZenML pipeline using the local Docker orchestrator:
```shell
python file_that_runs_a_zenml_pipeline.py
```

### Additional configuration

For additional configuration of the Local Docker orchestrator, you can pass
`LocalDockerOrchestratorSettings` when defining or running your pipeline.
Check out the
[API docs](https://apidocs.zenml.io/latest/core_code_docs/core-orchestrators/#zenml.orchestrators.local_docker.local_docker_orchestrator.LocalDockerOrchestratorSettings)
for a full list of available attributes and [this docs page](../..//advanced-guide/pipelines/settings.md)
for more information on how to specify settings.


For more information and a full list of configurable attributes of the local 
Docker orchestrator, check out the [API Docs](https://apidocs.zenml.io/latest/core_code_docs/core-orchestrators/#zenml.orchestrators.local_docker.local_docker_orchestrator.LocalDockerOrchestrator).

### Enabling CUDA for GPU-backed hardware

Note that if you wish to use this orchestrator to run steps on a GPU, you will
need to follow [the instructions on this page](../../advanced-guide/pipelines/gpu-hardware.md) to ensure that it works. It
requires adding some extra settings customization and is essential to enable
CUDA for the GPU to give its full acceleration.
