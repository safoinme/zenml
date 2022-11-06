---
description: How to log and visualize ML experiments
---

Experiment trackers let you track your ML experiments by logging extended
information about your models, datasets, metrics and other parameters and
allowing you to browse them, visualize them and compare them between runs.
In the ZenML world, every pipeline run is considered an experiment, and ZenML
facilitates the storage of experiment results through Experiment Tracker stack
components. This establishes a clear link between pipeline runs and experiments.

Related concepts:

* the Experiment Tracker is an optional type of Stack Component that needs to be
registered as part of your ZenML [Stack](../../starter-guide/stacks/stacks.md).
* ZenML already provides versioning and tracking for the pipeline artifacts by
storing artifacts in the [Artifact Store](../artifact-stores/artifact-stores.md).

## When to use it

ZenML already records information about the artifacts circulated through your
pipelines by means of the mandatory [Artifact Store](../artifact-stores/artifact-stores.md). 

<!-- markdown-link-check-disable -->

<!---
Similar to
Experiment Trackers, the ZenML pipeline artifacts can be extracted using
[the post-execution workflow API](../../developer-guide/post-execution-workflow.md)
and visualized using the ZenML [Visualizers](../../developer-guide/visualizer.md).
-->

<!-- markdown-link-check-enable -->

However, these ZenML mechanisms are meant to be used programmatically and can be
more difficult to work with without a visual interface.

Experiment Trackers on the other hand are tools designed with usability in mind.
They include extensive UI's providing users with an interactive and intuitive
interface that allows them to browse and visualize the information logged during
the ML pipeline runs.

You should add an Experiment Tracker to your ZenML stack and use it when you
want to augment ZenML with the visual features provided by experiment tracking
tools.

### Experiment Tracker Flavors

Experiment Trackers are optional stack components provided by integrations:

| Experiment Tracker                   | Flavor   | Integration   | Notes                                                                                           |
|--------------------------------------|----------|---------------|-------------------------------------------------------------------------------------------------|
| [MLflow](./mlflow.md)                | `mlflow` | `mlflow`      | Add MLflow experiment tracking and visualization capabilities to your ZenML pipelines           |
| [Weights & Biases](./wandb.md)       | `wandb`  | `wandb`       | Add Weights & Biases experiment tracking and visualization capabilities to your ZenML pipelines |
| [Custom Implementation](./custom.md) | _custom_ |               | _custom_                                                                                        | Extend the Experiment Tracker abstraction and provide your own implementation |

If you would like to see the available flavors of Experiment Tracker, you can 
use the command:

```shell
zenml experiment-tracker flavor list
```
## How to use it

Every Experiment Tracker has different capabilities and uses a different
way of logging information from your pipeline steps, but it generally works
as follows:

* first, you have to configure and add an Experiment Tracker to your ZenML stack
* next, you have to explicitly enable the Experiment Tracker for individual
steps in your pipeline by decorating them with the included decorator
* in your steps, you have to explicitly log information (e.g. models, metrics,
data) to the Experiment Tracker same as you would if you were using the tool
independently of ZenML
* finally, you can access the Experiment Tracker UI to browse and visualize the
information logged during your pipeline runs

Consult the documentation for the particular [Experiment Tracker flavor](#experiment-tracker-flavors)
that you plan on using or are using in your stack for detailed information about
how to use it in your ZenML pipelines.
