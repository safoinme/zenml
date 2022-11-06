---
description: How to manage external, longer-lived services
---

ZenML interacts with external systems (e.g. prediction services, monitoring
systems, visualization services) via a so-called `Service` abstraction.
The concrete implementation of this abstraction deals with functionality
concerning the life-cycle management and tracking of an external service 
(e.g. process, container, Kubernetes deployment etc.).

## Using Services in Steps

Services can be passed through steps like any other object, and used to 
interact with the external systems that they represent:

```python
from zenml.steps import step


@step
def my_step(my_service: MyService) -> ...:
    if not my_service.is_running:
        my_service.start()  # starts service
    my_service.stop()  # stops service
```

## Examples

One concrete example of a `Service` is the built-in `LocalDaemonService`, a
service represented by a local daemon process which extends the base `Service`
class with functionality concerning the life-cycle management and tracking
of local daemon processes. The `LocalDaemonService` is used by various
integrations to connect your local machines to remote components such as a
[Metadata Store in Kubeflow](../../mlops-stacks/metadata-stores/kubeflow.md).

Another example is the `TensorboardService`.
It enables visualizing [TensorBoard](https://www.tensorflow.org/tensorboard)
logs by managing a local TensorBoard server, which couples nicely with
the `TensorboardVisualizer` to visualize Tensorboard logs:

```python
from zenml.integrations.tensorboard.services.tensorboard_service import (
    TensorboardService,
    TensorboardServiceConfig
)

service = TensorboardService(
    TensorboardServiceConfig(
        logdir=logdir,
    )
)

# start the service
service.start(timeout=20)

# stop the service
service.stop()
```

You can find full examples of using services here:

* Visualizing training with TensorBoard in the
[Kubeflow TensorBoard example](https://github.com/zenml-io/zenml/tree/main/examples/kubeflow_pipelines_orchestration).
* Interacting with the services of deployed models in the
[MLflow deployment example](https://github.com/zenml-io/zenml/tree/main/examples/mlflow_deployment).
* Interacting with the services of deployed models in the
[Seldon deployment example](https://github.com/zenml-io/zenml/tree/main/examples/seldon_deployment).
* Interacting with the services of deployed models in the
[KServe deployment example](https://github.com/zenml-io/zenml/tree/main/examples/kserve_deployment).
