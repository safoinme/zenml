---
description: Orchestrating your pipelines to run on Airflow.
---

# Airflow Orchestrator

ZenML pipelines can be executed natively as [Airflow](https://airflow.apache.org/) 
DAGs. This brings together the power of the Airflow orchestration with the 
ML-specific benefits of ZenML pipelines. Each ZenML step runs in a separate 
Docker container which is scheduled and started using Airflow.

{% hint style="warning" %}
If you're going to use a remote deployment of Airflow, you'll also need
a [remote ZenML deployment](/docs/book/deploying-zenml/zenml-self-hosted/zenml-self-hosted.md).
{% endhint %}

### When to use it

You should use the Airflow orchestrator if

* you're looking for a proven production-grade orchestrator.
* you're already using Airflow.
* you want to run your pipelines locally.
* you're willing to deploy and maintain Airflow.

### How to deploy it

The Airflow orchestrator can be used to run pipelines locally as well as remotely. In the local case, no additional
setup is necessary.

There are many options to use a deployed Airflow server:

* Use one of [ZenML's Airflow stack recipes](https://github.com/zenml-io/mlstacks). This is the simplest solution to
  get ZenML working with Airflow, as the recipe also takes care of additional steps such as installing required Python
  dependencies in your Airflow server environment.
* Use a managed deployment of Airflow such as [Google Cloud Composer](https://cloud.google.com/composer)
  , [Amazon MWAA](https://aws.amazon.com/managed-workflows-for-apache-airflow/),
  or [Astronomer](https://www.astronomer.io/).
* Deploy Airflow manually. Check out the
  official [Airflow docs](https://airflow.apache.org/docs/apache-airflow/stable/production-deployment.html) for more
  information.

If you're not using `mlstacks` to deploy Airflow, there are some additional Python packages that you'll need to
install in the Python environment of your Airflow server:

* `pydantic~=1.9.2`: The Airflow DAG files that ZenML creates for you require Pydantic to parse and validate
  configuration files.
* `apache-airflow-providers-docker` or `apache-airflow-providers-cncf-kubernetes`, depending on which Airflow operator
  you'll be using to run your pipeline steps. Check out [this section](airflow.md#using-different-airflow-operators) for
  more information on supported operators.

### How to use it

To use the Airflow orchestrator, we need:

* The ZenML `airflow` integration installed. If you haven't done so, run

  ```shell
  zenml integration install airflow
  ```
* [Docker](https://docs.docker.com/get-docker/) installed and running.
* The orchestrator registered and part of our active stack:

```shell
zenml orchestrator register <ORCHESTRATOR_NAME> \
    --flavor=airflow \
    --local=True  # set this to `False` if using a remote Airflow deployment

# Register and activate a stack with the new orchestrator
zenml stack register <STACK_NAME> -o <ORCHESTRATOR_NAME> ... --set
```

{% tabs %}
{% tab title="Local" %}
In the local case, we need to install one additional Python package that is needed for the local Airflow server:

```bash
pip install apache-airflow-providers-docker
```

Once that is installed, we can start the local Airflow server by running:

```shell
zenml stack up
```

This command will start up an Airflow server on your local machine that's running in the same Python environment that
you used to provision it. When it is finished, it will print a username and password which you can use to log in to the
Airflow UI [here](http://0.0.0.0:8080).

As long as you didn't configure any custom value for the `dag_output_dir` attribute of your orchestrator, running a
pipeline locally is as simple as calling:

```shell
python file_that_runs_a_zenml_pipeline.py
```

This call will produce a `.zip` file containing a representation of your ZenML pipeline to the Airflow DAGs directory.
From there, the local Airflow server will load it and run your pipeline (It might take a few seconds until the pipeline
shows up in the Airflow UI).

{% hint style="info" %}
The ability to provision resources using the `zenml stack up` command is deprecated and will be removed in a future
release. While it is still available for the Airflow orchestrator, we recommend following the steps to set up a local
Airflow server manually.

1. Install the `apache-airflow` package in your Python environment where ZenML is installed.
2. The Airflow environment variables are used to configure the behavior of the Airflow server. The following variables
   are particularly important to set:
3. `AIRFLOW_HOME`: This variable defines the location where the Airflow server stores its database and configuration
   files. The default value is \~/airflow.
4. `AIRFLOW__CORE__DAGS_FOLDER`: This variable defines the location where the Airflow server looks for DAG files. The
   default value is \<AIRFLOW\_HOME>/dags.
5. `AIRFLOW__CORE__LOAD_EXAMPLES`: This variable controls whether the Airflow server should load the default set of
   example DAGs. The default value is false, which means that the example DAGs will not be loaded.
6. `AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL`: This variable controls how often the Airflow scheduler checks for new or
   updated DAGs. By default, the scheduler will check for new DAGs every 30 seconds. This variable can be used to
   increase or decrease the frequency of the checks, depending on the specific needs of your pipeline.

    ```bash
    export AIRFLOW_HOME=...
    export AIRFLOW__CORE__DAGS_FOLDER=...
    export AIRFLOW__CORE__LOAD_EXAMPLES=false
    export AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=10
    
    # Prevent crashes during forking on MacOS
    # https://github.com/apache/airflow/issues/28487
    export no_proxy=*
    ```

7. Run `airflow standalone` to initialize the database, create a user, and start all components for you.
{% endhint %}
{% endtab %}

{% tab title="Remote" %}
When using the Airflow orchestrator with a remote deployment, you'll additionally need:

* A remote ZenML server deployed to the cloud. See
  the [deployment guide](/docs/book/deploying-zenml/zenml-self-hosted/zenml-self-hosted.md) 
  for more information.
* A deployed Airflow server. See the [deployment section](airflow.md#how-to-deploy-it) for more information.
* A [remote artifact store](../artifact-stores/artifact-stores.md) as part of your stack.
* A [remote container registry](../container-registries/container-registries.md) as part of your stack.

In the remote case, the Airflow orchestrator works differently than other ZenML orchestrators. Executing a python file
which runs a pipeline by calling `pipeline.run()` will not actually run the pipeline, but instead will create a `.zip`
file containing an Airflow representation of your ZenML pipeline. In one additional step, you need to make sure this zip
file ends up in
the [DAGs directory](https://airflow.apache.org/docs/apache-airflow/stable/concepts/overview.html#architecture-overview)
of your Airflow deployment.
{% endtab %}
{% endtabs %}

{% hint style="info" %}
ZenML will build a Docker image called `<CONTAINER_REGISTRY_URI>/zenml:<PIPELINE_NAME>` which includes your code and use
it to run your pipeline steps in Airflow. Check
out [this page](/docs/book/user-guide/advanced-guide/environment-management/containerize-your-pipeline.md) if you want to learn
more about how ZenML builds these images and how you can customize them.
{% endhint %}

#### Scheduling

You can [schedule pipeline runs](../../advanced-guide/pipelining-features/schedule-pipeline-runs.md)
on Airflow similarly to other orchestrators. However, note that 
**Airflow schedules always need to be set in the past**, e.g.,:

```python
from datetime import datetime, timedelta

from zenml.pipelines import Schedule

scheduled_pipeline = fashion_mnist_pipeline.with_options(
    schedule=Schedule(
        start_time=datetime.now() - timedelta(hours=1),  # start in the past
        end_time=datetime.now() + timedelta(hours=1),
        interval_second=timedelta(minutes=15),  # run every 15 minutes
        catchup=False,
    )
)
scheduled_pipeline()
```

#### Airflow UI

Airflow comes with its own UI that you can use to find further details about your pipeline runs, such as the logs of
your steps. For local Airflow, you can find the Airflow UI at [http://localhost:8080](http://localhost:8080) by default.
Alternatively, you can get the orchestrator UI URL in Python using the following code snippet:

```python
from zenml.client import Client

pipeline_run = Client().get_pipeline_run("<PIPELINE_RUN_NAME>")
orchestrator_url = pipeline_run.metadata["orchestrator_url"].value
```

{% hint style="info" %}
If you cannot see the Airflow UI credentials in the console, you can find the
password in
`<GLOBAL_CONFIG_DIR>/airflow/<ORCHESTRATOR_UUID>/standalone_admin_password.txt`.
- `GLOBAL_CONFIG_DIR` depends on your OS.
  Run `python -c "from zenml.config.global_config import GlobalConfiguration; print(GlobalConfiguration().config_directory)"`
  to get the path for your machine.
- `ORCHESTRATOR_UUID` is the unique ID of the Airflow orchestrator, but there
  should be only one folder here, so you can just navigate into that one.

The username will always be `admin`.
{% endhint %}

#### Additional configuration

For additional configuration of the Airflow orchestrator, you can pass `AirflowOrchestratorSettings` when defining or
running your pipeline. Check out
the [SDK docs](https://sdkdocs.zenml.io/latest/integration\_code\_docs/integrations-airflow/#zenml.integrations.airflow.flavors.airflow\_orchestrator\_flavor.AirflowOrchestratorSettings)
for a full list of available attributes and [this docs page](/docs/book/user-guide/advanced-guide/pipelining-features/configure-steps-pipelines.md) for
more information on how to specify settings.

#### Enabling CUDA for GPU-backed hardware

Note that if you wish to use this orchestrator to run steps on a GPU, you will need to
follow [the instructions on this page](/docs/book/user-guide/advanced-guide/environment-management/scale-compute-to-the-cloud.md) to ensure that it
works. It requires adding some extra settings customization and is essential to enable CUDA for the GPU to give its full
acceleration.

#### Using different Airflow operators

Airflow operators specify how a step in your pipeline gets executed. As ZenML relies on Docker images to run pipeline
steps, only operators that support executing a Docker image work in combination with ZenML. Airflow comes with two
operators that support this:

* the `DockerOperator` runs the Docker images for executing your pipeline steps on the same machine that your Airflow
  server is running on. For this to work, the server environment needs to have the `apache-airflow-providers-docker`
  package installed.
* the `KubernetesPodOperator` runs the Docker image on a pod in the Kubernetes cluster that the Airflow server is
  deployed to. For this to work, the server environment needs to have the `apache-airflow-providers-cncf-kubernetes`
  package installed.

You can specify which operator to use and additional arguments to it as follows:

```python
from zenml import pipeline, step
from zenml.integrations.airflow.flavors.airflow_orchestrator_flavor import AirflowOrchestratorSettings

airflow_settings = AirflowOrchestratorSettings(
    operator="docker",  # or "kubernetes_pod"
    # Dictionary of arguments to pass to the operator __init__ method
    operator_args={}
)

# Using the operator for a single step
@step(settings={"orchestrator.airflow": airflow_settings})
def my_step(...):


# Using the operator for all steps in your pipeline
@pipeline(settings={"orchestrator.airflow": airflow_settings})
def my_pipeline(...):
```

**Custom operators**

If you want to use any other operator to run your steps, you can specify the `operator` in your `AirflowSettings` as a
path to the python operator class:

```python
from zenml.integrations.airflow.flavors.airflow_orchestrator_flavor import AirflowOrchestratorSettings

airflow_settings = AirflowOrchestratorSettings(
    # This could also be a reference to one of your custom classes.
    # e.g. `my_module.MyCustomOperatorClass` as long as the class
    # is importable in your Airflow server environment
    operator="airflow.providers.docker.operators.docker.DockerOperator",
    # Dictionary of arguments to pass to the operator __init__ method
    operator_args={}
)
```

**Custom DAG generator file**

To run a pipeline in Airflow, ZenML creates a Zip archive that contains two files:

* A JSON configuration file that the orchestrator creates. This file contains all the information required to create the
  Airflow DAG to run the pipeline.
* A Python file that reads this configuration file and actually creates the Airflow DAG. We call this file
  the `DAG generator` and you can find the
  implementation [here](https://github.com/zenml-io/zenml/blob/main/src/zenml/integrations/airflow/orchestrators/dag\_generator.py)
  .

If you need more control over how the Airflow DAG is generated, you can provide a custom DAG generator file using the
setting `custom_dag_generator`. This setting will need to reference a Python module that can be imported into your
active Python environment. It will additionally need to contain the same classes (`DagConfiguration`
and `TaskConfiguration`) and constants (`ENV_ZENML_AIRFLOW_RUN_ID`, `ENV_ZENML_LOCAL_STORES_PATH` and `CONFIG_FILENAME`)
as
the [original module](https://github.com/zenml-io/zenml/blob/main/src/zenml/integrations/airflow/orchestrators/dag\_generator.py)
. For this reason, we suggest starting by copying the original and modifying it according to your needs.

Check out our docs on how to apply settings to your
pipelines [here](/docs/book/user-guide/advanced-guide/pipelining-features/configure-steps-pipelines.md).

For more information and a full list of configurable attributes of the Airflow orchestrator, check out
the [API Docs](https://sdkdocs.zenml.io/latest/api\_docs/integration\_code\_docs/integrations-airflow/#zenml.integrations.airflow.orchestrators.airflow\_orchestrator.AirflowOrchestrator)
.

<!-- For scarf -->
<figure><img alt="ZenML Scarf" referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=f0b4f458-0a54-4fcd-aa95-d5ee424815bc" /></figure>
