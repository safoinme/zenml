---
description: Orchestrating your pipelines to run on Kubeflow.
---

# Kubeflow Orchestrator

The Kubeflow orchestrator is an [orchestrator](orchestrators.md) flavor provided by the ZenML `kubeflow` integration
that uses [Kubeflow Pipelines](https://www.kubeflow.org/docs/components/pipelines/introduction/) to run your pipelines.

{% hint style="warning" %}
This component is only meant to be used within the context of
a [remote ZenML deployment scenario](/docs/book/deploying-zenml/zenml-self-hosted/zenml-self-hosted.md).
Usage with a local ZenML deployment may lead to unexpected behavior!
{% endhint %}

### When to use it

You should use the Kubeflow orchestrator if:

* you're looking for a proven production-grade orchestrator.
* you're looking for a UI in which you can track your pipeline runs.
* you're already using Kubernetes or are not afraid of setting up and maintaining a Kubernetes cluster.
* you're willing to deploy and maintain Kubeflow Pipelines on your cluster.

### How to deploy it

The Kubeflow orchestrator supports two different modes: `Local` and `remote`. In case you want to run the orchestrator
on a local Kubernetes cluster running on your machine, there is no additional infrastructure setup necessary.

If you want to run your pipelines on a remote cluster instead, you'll need to set up a Kubernetes cluster and deploy
Kubeflow Pipelines:

{% tabs %}
{% tab title="AWS" %}

* Have an existing AWS [EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/create-cluster.html) set up.
* Make sure you have the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) set
  up.
* Download and [install](https://kubernetes.io/docs/tasks/tools/) `kubectl`
  and [configure](https://aws.amazon.com/premiumsupport/knowledge-center/eks-cluster-connection/) it to talk to your EKS
  cluster using the following command:

  ```powershell
  aws eks --region REGION update-kubeconfig --name CLUSTER_NAME
  ```
* [Install](https://www.kubeflow.org/docs/components/pipelines/installation/standalone-deployment/#deploying-kubeflow-pipelines)
  Kubeflow Pipelines onto your cluster.
* (
  optional) [set up an AWS Service Connector](../../auth-management/aws-service-connector.md)
  to grant ZenML Stack Components easy and secure access to the remote EKS cluster.
  {% endtab %}

{% tab title="GCP" %}

* Have an existing GCP [GKE cluster](https://cloud.google.com/kubernetes-engine/docs/quickstart) set up.
* Make sure you have the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install-sdk) set up first.
* Download and [install](https://kubernetes.io/docs/tasks/tools/) `kubectl`
  and [configure](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl) it to talk to your
  GKE cluster using the following command:

  ```powershell
  gcloud container clusters get-credentials CLUSTER_NAME
  ```
* [Install](https://www.kubeflow.org/docs/distributions/gke/deploy/overview/) Kubeflow Pipelines onto your cluster.
* (
  optional) [set up a GCP Service Connector](../../auth-management/gcp-service-connector.md)
  to grant ZenML Stack Components easy and secure access to the remote GKE cluster.
  {% endtab %}

{% tab title="Azure" %}

* Have an existing [AKS cluster](https://azure.microsoft.com/en-in/services/kubernetes-service/#documentation) set up.
* Make sure you have the [`az` CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) set up first.
* Download and [install](https://kubernetes.io/docs/tasks/tools/) `kubectl` and ensure that it talks to your AKS cluster
  using the following command:

  ```powershell
  az aks get-credentials --resource-group RESOURCE_GROUP --name CLUSTER_NAME
  ```
* [Install](https://www.kubeflow.org/docs/components/pipelines/installation/standalone-deployment/#deploying-kubeflow-pipelines)
  Kubeflow Pipelines onto your cluster.

> Since Kubernetes v1.19, AKS has shifted

to [`containerd`](https://docs.microsoft.com/en-us/azure/aks/cluster-configuration#container-settings)

> . However, the workflow controller installed with the Kubeflow installation has `Docker` set as the default runtime.
In order to make your pipelines work, you have to change the value to one of the options

listed [here](https://argoproj.github.io/argo-workflows/workflow-executors/#workflow-executors)

> , preferably `k8sapi`.
>
> This change has to be made by editing the `containerRuntimeExecutor` property of the `ConfigMap` corresponding to the
workflow controller. Run the following commands to first know what config map to change and then to edit it to reflect
your new value.
>
> ```
> kubectl get configmap -n kubeflow
> kubectl edit configmap CONFIGMAP_NAME -n kubeflow
> # This opens up an editor that can be used to make the change.
> ```
{% endtab %}
{% endtabs %}

{% hint style="info" %}
If one or more of the deployments are not in the `Running` state, try increasing the number of nodes in your cluster.
{% endhint %}

{% hint style="warning" %}
If you're installing Kubeflow Pipelines manually, make sure the Kubernetes service is called exactly `ml-pipeline`. This
is a requirement for ZenML to connect to your Kubeflow Pipelines deployment.
{% endhint %}

#### Infrastructure Deployment

A Kubeflow orchestrator can be deployed directly from the ZenML CLI:

```shell
zenml orchestrator deploy kubeflow_orchestrator --flavor=kubeflow --provider=<YOUR_PROVIDER> ...
```

You can pass other configurations specific to the stack components as key-value arguments. If you don't provide a name,
a random one is generated for you. For more information about how to work use the CLI for this, please refer to the
dedicated documentation section.

### How to use it

To use the Kubeflow orchestrator, we need:

* The ZenML `kubeflow` integration installed. If you haven't done so, run

  ```shell
  zenml integration install kubeflow
  ```
* [Docker](https://www.docker.com) installed and running.
* [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl) installed (optional, see below)

{% hint style="info" %}
If you are using a single-tenant Kubeflow installed in a Kubernetes cluster managed by a cloud provider like AWS, GCP or
Azure, it is recommended that you set
up [a Service Connector](../../auth-management/service-connectors-guide.md)
and use it to connect ZenML Stack Components to the remote Kubernetes cluster. This guarantees that your Stack is fully
portable on other environments and your pipelines are fully reproducible.
{% endhint %}

{% tabs %}
{% tab title="Local" %}
When using the Kubeflow orchestrator locally, you'll additionally need:

* [K3D](https://k3d.io/v5.2.1/#installation) installed to spin up a local Kubernetes cluster.
* [Terraform](https://www.terraform.io/downloads.html) installed to set up the Kubernetes cluster with various
  deployments.
* [MLStacks](https://mlstacks.zenml.io) installed to handle the deployment

To run the pipeline on a local Kubeflow Pipelines deployment, you can use the
ZenML `mlstacks` package to spin up a local
Kubernetes cluster and install Kubeflow Pipelines on it.

To deploy the stack, run the following commands:

```shell
# Deploy the stack using the ZenML CLI:
zenml stack deploy k3d-modular -o kubeflow -a minio --provider k3d
zenml stack set k3d-modular
```

```shell
# Get the Kubeflow Pipelines UI endpoint
kubectl get ingress -n kubeflow  -o jsonpath='{.items[0].spec.rules[0].host}'
```

You can read more about `mlstacks` on [our dedicated documentation page here](https://mlstacks.zenml.io).

{% hint style="warning" %}
The local Kubeflow Pipelines deployment requires more than 4 GB of RAM, and 30 GB of disk space, so if you are using
Docker Desktop make sure to update the resource limits in the preferences.
{% endhint %}
{% endtab %}

{% tab title="Remote" %}
When using the Kubeflow orchestrator with a remote cluster, you'll additionally need:

* A remote ZenML server deployed to the cloud. See
  the [deployment guide](/docs/book/deploying-zenml/zenml-self-hosted/zenml-self-hosted.md) for more information.
* Kubeflow pipelines deployed on a remote cluster. See the [deployment section](kubeflow.md#how-to-deploy-it) for more
  information.
* The name of your Kubernetes context which points to your remote cluster. Run `kubectl config get-contexts` to see a
  list of available contexts. **NOTE**: this is no longer required if you are
  using [a Service Connector ](../../auth-management/service-connectors-guide.md)
  to connect your Kubeflow Orchestrator Stack Component to the remote Kubernetes cluster.
* A [remote artifact store](../artifact-stores/artifact-stores.md) as part of your stack.
* A [remote container registry](../container-registries/container-registries.md) as part of your stack.

We can then register the orchestrator and use it in our active stack. This can be done in two ways:

1. If you
   have [a Service Connector](../../auth-management/service-connectors-guide.md)
   configured to access the remote Kubernetes cluster, you no longer need to set the `kubernetes_context` attribute to a
   local `kubectl` context. In fact, you don't need the local Kubernetes CLI at all. You
   can [connect the stack component to the Service Connector](../../auth-management/service-connectors-guide.md#connect-stack-components-to-resources)
   instead:

    ```
    $ zenml orchestrator register <ORCHESTRATOR_NAME> --flavor kubeflow
    Running with active workspace: 'default' (repository)
    Running with active stack: 'default' (repository)
    Successfully registered orchestrator `<ORCHESTRATOR_NAME>`.
    
    $ zenml service-connector list-resources --resource-type kubernetes-cluster -e
    The following 'kubernetes-cluster' resources can be accessed by service connectors configured in your workspace:
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━┓
    ┃             CONNECTOR ID             │ CONNECTOR NAME        │ CONNECTOR TYPE │ RESOURCE TYPE         │ RESOURCE NAMES      ┃
    ┠──────────────────────────────────────┼───────────────────────┼────────────────┼───────────────────────┼─────────────────────┨
    ┃ e33c9fac-5daa-48b2-87bb-0187d3782cde │ aws-iam-multi-eu      │ 🔶 aws         │ 🌀 kubernetes-cluster │ kubeflowmultitenant ┃
    ┃                                      │                       │                │                       │ zenbox              ┃
    ┠──────────────────────────────────────┼───────────────────────┼────────────────┼───────────────────────┼─────────────────────┨
    ┃ ed528d5a-d6cb-4fc4-bc52-c3d2d01643e5 │ aws-iam-multi-us      │ 🔶 aws         │ 🌀 kubernetes-cluster │ zenhacks-cluster    ┃
    ┠──────────────────────────────────────┼───────────────────────┼────────────────┼───────────────────────┼─────────────────────┨
    ┃ 1c54b32a-4889-4417-abbd-42d3ace3d03a │ gcp-sa-multi          │ 🔵 gcp         │ 🌀 kubernetes-cluster │ zenml-test-cluster  ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━┛
    
    $ zenml orchestrator connect <ORCHESTRATOR_NAME> --connector aws-iam-multi-us
    Running with active workspace: 'default' (repository)
    Running with active stack: 'default' (repository)
    Successfully connected orchestrator `<ORCHESTRATOR_NAME>` to the following resources:
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━┓
    ┃             CONNECTOR ID             │ CONNECTOR NAME   │ CONNECTOR TYPE │ RESOURCE TYPE         │ RESOURCE NAMES   ┃
    ┠──────────────────────────────────────┼──────────────────┼────────────────┼───────────────────────┼──────────────────┨
    ┃ ed528d5a-d6cb-4fc4-bc52-c3d2d01643e5 │ aws-iam-multi-us │ 🔶 aws         │ 🌀 kubernetes-cluster │ zenhacks-cluster ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━┛
    
    # Add the orchestrator to the active stack
    $ zenml stack update -o <ORCHESTRATOR_NAME>
    ```

2. if you don't have a Service Connector on hand and you don't want
   to [register one](../../auth-management/service-connectors-guide.md#register-service-connectors)
   , the local Kubernetes `kubectl` client needs to be configured with a configuration context pointing to the remote
   cluster. The `kubernetes_context` stack component must also be configured with the value of that context:

    ```shell
    zenml orchestrator register <ORCHESTRATOR_NAME> \
        --flavor=kubeflow \
        --kubernetes_context=<KUBERNETES_CONTEXT>
    
    # Add the orchestrator to the active stack
    zenml stack update -o <ORCHESTRATOR_NAME>
    ```

{% endtab %}
{% endtabs %}

{% hint style="info" %}
ZenML will build a Docker image called `<CONTAINER_REGISTRY_URI>/zenml:<PIPELINE_NAME>` which includes your code and use
it to run your pipeline steps in Kubeflow. Check
out [this page](/docs/book/user-guide/advanced-guide/environment-management/containerize-your-pipeline.md) if you want to learn
more about how ZenML builds these images and how you can customize them.
{% endhint %}

You can now run any ZenML pipeline using the Kubeflow orchestrator:

```shell
python file_that_runs_a_zenml_pipeline.py
```

#### Kubeflow UI

Kubeflow comes with its own UI that you can use to find further details about your pipeline runs, such as the logs of
your steps. For any runs executed on Kubeflow, you can get the URL to the Kubeflow UI in Python using the following code
snippet:

```python
from zenml.client import Client

pipeline_run = Client().get_pipeline_run("<PIPELINE_RUN_NAME>")
orchestrator_url = pipeline_run.metadata["orchestrator_url"].value
```

#### Additional configuration

For additional configuration of the Kubeflow orchestrator, you can pass `KubeflowOrchestratorSettings` which allows you
to configure (among others) the following attributes:

* `client_args`: Arguments to pass when initializing the KFP client.
* `user_namespace`: The user namespace to use when creating experiments and runs.
* `pod_settings`: Node selectors, affinity, and tolerations to apply to the Kubernetes Pods running your pipeline. These
  can be either specified using the Kubernetes model objects or as dictionaries.

```python
from zenml.integrations.kubeflow.flavors.kubeflow_orchestrator_flavor import KubeflowOrchestratorSettings
from kubernetes.client.models import V1Toleration

kubeflow_settings = KubeflowOrchestratorSettings(
    client_args={},
    user_namespace="my_namespace",
    pod_settings={
        "affinity": {
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [
                        {
                            "matchExpressions": [
                                {
                                    "key": "node.kubernetes.io/name",
                                    "operator": "In",
                                    "values": ["my_powerful_node_group"],
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "tolerations": [
            V1Toleration(
                key="node.kubernetes.io/name",
                operator="Equal",
                value="",
                effect="NoSchedule"
            )
        ]
    }
)


@pipeline(
    settings={
        "orchestrator.kubeflow": kubeflow_settings
    }
)


...
```

Check out
the [SDK docs](https://sdkdocs.zenml.io/latest/integration\_code\_docs/integrations-kubeflow/#zenml.integrations.kubeflow.flavors.kubeflow\_orchestrator\_flavor.KubeflowOrchestratorSettings)
for a full list of available attributes and [this docs page](/docs/book/user-guide/advanced-guide/pipelining-features/configure-steps-pipelines.md) for more
information on how to specify settings.

#### Enabling CUDA for GPU-backed hardware

Note that if you wish to use this orchestrator to run steps on a GPU, you will need to
follow [the instructions on this page](/docs/book/user-guide/advanced-guide/environment-management/scale-compute-to-the-cloud.md) to ensure that it
works. It requires adding some extra settings customization and is essential to enable CUDA for the GPU to give its full
acceleration.

### Important Note for Multi-Tenancy Deployments

Kubeflow has a notion of [multi-tenancy](https://www.kubeflow.org/docs/components/multi-tenancy/overview/) built into
its deployment. Kubeflow's multi-user isolation simplifies user operations because each user only views and edited the
Kubeflow components and model artifacts defined in their configuration.

Using the ZenML Kubeflow orchestrator on a multi-tenant deployment without any settings will result in the following
error:

```shell
HTTP response body: {"error":"Invalid input error: Invalid resource references for experiment. ListExperiment requires filtering by namespace.","code":3,"message":"Invalid input error: Invalid resource references for experiment. ListExperiment requires filtering by 
namespace.","details":[{"@type":"type.googleapis.com/api.Error","error_message":"Invalid resource references for experiment. ListExperiment requires filtering by namespace.","error_details":"Invalid input error: Invalid resource references for experiment. ListExperiment requires filtering by namespace."}]}
```

In order to get it to work, we need to leverage the `KubeflowOrchestratorSettings` referenced above. By setting the
namespace option, and by passing in the right authentication credentials to the Kubeflow Pipelines Client, we can make
it work.

First, when registering your Kubeflow orchestrator, please make sure to include the `kubeflow_hostname` parameter.
The `kubeflow_hostname` **must end with the `/pipeline` post-fix**.

```shell
zenml orchestrator register <NAME> \
    --flavor=kubeflow \
    --kubeflow_hostname=<KUBEFLOW_HOSTNAME> # e.g. https://mykubeflow.example.com/pipeline
```

Then, ensure that you use the pass the right settings before triggering a pipeline run. The following snippet will prove
useful:

```python
import requests

from zenml.client import Client
from zenml.integrations.kubeflow.flavors.kubeflow_orchestrator_flavor import (
    KubeflowOrchestratorSettings,
)

NAMESPACE = "namespace_name"  # This is the user namespace for the profile you want to use
USERNAME = "admin"  # This is the username for the profile you want to use
PASSWORD = "abc123"  # This is the password for the profile you want to use

# Use client_username and client_password and ZenML will automatically fetch a session cookie
kubeflow_settings = KubeflowOrchestratorSettings(
    client_username=USERNAME,
    client_password=PASSWORD,
    user_namespace=NAMESPACE
)


# You can also pass the cookie in `client_args` directly
# kubeflow_settings = KubeflowOrchestratorSettings(
#     client_args={"cookies": session_cookie}, user_namespace=NAMESPACE
# )

@pipeline(
    settings={
        "orchestrator.kubeflow": kubeflow_settings
    }
)

:
...

if "__name__" == "__main__":
# Run the pipeline
```

Note that the above is also currently not tested on all Kubeflow versions, so there might be further bugs with older
Kubeflow versions. In this case, please reach out to us on [Slack](https://zenml.io/slack-invite).

#### Using secrets in settings

The above example encoded the username and password in plain text as settings. You can also set them as secrets.

```shell
zenml secret create kubeflow_secret \
    --username=admin \
    --password=abc123
```

And then you can use them in code:

```python
# Use client_username and client_password and ZenML will automatically fetch a session cookie
kubeflow_settings = KubeflowOrchestratorSettings(
    client_username="{{kubeflow_secret.username}}",  # secret reference
    client_password="{{kubeflow_secret.password}}",  # secret reference
    user_namespace="namespace_name"
)
```

See full documentation of using ZenML
secrets [here](/docs/book/user-guide/advanced-guide/secret-management/secret-management.md).

For more information and a full list of configurable attributes of the Kubeflow orchestrator, check out
the [API Docs](https://sdkdocs.zenml.io/latest/integration\_code\_docs/integrations-kubeflow/#zenml.integrations.kubeflow.orchestrators.kubeflow\_orchestrator.KubeflowOrchestrator)
.

<!-- For scarf -->
<figure><img alt="ZenML Scarf" referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=f0b4f458-0a54-4fcd-aa95-d5ee424815bc" /></figure>

