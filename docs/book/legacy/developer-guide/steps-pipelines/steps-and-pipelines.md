---
description: How to create ML pipelines in ZenML
---

# Steps & Pipelines

ZenML helps you standardize your ML workflows as ML **Pipelines** consisting of
decoupled, modular **Steps**. This enables you to write portable code that can be
moved from experimentation to production in seconds.

{% hint style="info" %}
If you are new to MLOps and would like to learn more about ML pipelines in 
general, checkout [ZenBytes](https://github.com/zenml-io/zenbytes), our lesson
series on practical MLOps, where we introduce ML pipelines in more detail in
[ZenBytes lesson 1.1](https://github.com/zenml-io/zenbytes/blob/main/1-1_Pipelines.ipynb).
{% endhint %}

## Step

Steps are the atomic components of a ZenML pipeline. Each step is defined by its
inputs, the logic it applies and its outputs. Here is a very basic example of
such a step, which uses a utility function to load the Digits dataset:

```python
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

from zenml.steps import Output, step


@step
def digits_data_loader() -> Output(
    X_train=np.ndarray, X_test=np.ndarray, y_train=np.ndarray, y_test=np.ndarray
):
    """Loads the digits dataset as a tuple of flattened numpy arrays."""
    digits = load_digits()
    data = digits.images.reshape((len(digits.images), -1))
    X_train, X_test, y_train, y_test = train_test_split(
        data, digits.target, test_size=0.2, shuffle=False
    )
    return X_train, X_test, y_train, y_test
```

As this step has multiple outputs, we need to use the
`zenml.steps.step_output.Output` class to indicate the names of each output. 
These names can be used to directly access the outputs of steps after running
a pipeline, as we will see [in a later chapter](./inspecting-pipeline-runs.md).

Let's come up with a second step that consumes the output of our first step and
performs some sort of transformation on it. In this case, let's train a support
vector machine classifier on the training data using sklearn:

```python
import numpy as np
from sklearn.base import ClassifierMixin
from sklearn.svm import SVC

from zenml.steps import step


@step
def svc_trainer(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> ClassifierMixin:
    """Train a sklearn SVC classifier."""
    model = SVC(gamma=0.001)
    model.fit(X_train, y_train)
    return model
```

Next, we will combine our two steps into our first ML pipeline.

{% hint style="info" %}
In case you want to run the step function outside the context of a ZenML 
pipeline, all you need to do is call the `.entrypoint()` method with the same
input signature. For example:

```python
svc_trainer.entrypoint(X_train=..., y_train=...)
```
{% endhint %}

## Pipeline

Let us now define our first ML pipeline. This is agnostic of the implementation and can be
done by routing outputs through the steps within the pipeline. You can think of
this as a recipe for how we want data to flow through our steps.

```python
from zenml.pipelines import pipeline


@pipeline
def first_pipeline(step_1, step_2):
    X_train, X_test, y_train, y_test = step_1()
    step_2(X_train, y_train)
```

### Instantiate and run your Pipeline

With your pipeline recipe in hand you can now specify which concrete step
implementations to use when instantiating the pipeline:

```python
first_pipeline_instance = first_pipeline(
    step_1=digits_data_loader(),
    step_2=svc_trainer(),
)
```

You can then execute your pipeline instance with the `.run()` method:

```python
first_pipeline_instance.run()
```

You should see the following output in your terminal:

```shell
Creating run for pipeline: `first_pipeline`
Cache disabled for pipeline `first_pipeline`
Using stack `default` to run pipeline `first_pipeline`
Step `digits_data_loader` has started.
Step `digits_data_loader` has finished in 0.049s.
Step `svc_trainer` has started.
Step `svc_trainer` has finished in 0.067s.
Pipeline run `first_pipeline-06_Jul_22-16_10_46_255748` has finished in 0.128s.
```

We will dive deeper into how to inspect the finished run within the chapter on
[Accessing Pipeline Runs](./inspecting-pipeline-runs.md).

### Give each pipeline run a name

When running a pipeline by calling `my_pipeline.run()`, ZenML uses the current
date and time as the name for the pipeline run. In order to change the name
for a run, pass `run_name` as a parameter to the `run()` function:

```python
first_pipeline_instance.run(run_name="custom_pipeline_run_name")
```

{% hint style="warning" %}
Pipeline run names must be unique, so make sure to compute it dynamically if you
plan to run your pipeline multiple times.
{% endhint %}

## Code Summary

<details>
    <summary>Code Example for this Section</summary>

```python
import numpy as np
from sklearn.base import ClassifierMixin
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

from zenml.steps import Output, step
from zenml.pipelines import pipeline


@step
def digits_data_loader() -> Output(
    X_train=np.ndarray, X_test=np.ndarray, y_train=np.ndarray, y_test=np.ndarray
):
    """Loads the digits dataset as a tuple of flattened numpy arrays."""
    digits = load_digits()
    data = digits.images.reshape((len(digits.images), -1))
    X_train, X_test, y_train, y_test = train_test_split(
        data, digits.target, test_size=0.2, shuffle=False
    )
    return X_train, X_test, y_train, y_test


@step
def svc_trainer(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> ClassifierMixin:
    """Train a sklearn SVC classifier."""
    model = SVC(gamma=0.001)
    model.fit(X_train, y_train)
    return model


@pipeline
def first_pipeline(step_1, step_2):
    X_train, X_test, y_train, y_test = step_1()
    step_2(X_train, y_train)


first_pipeline_instance = first_pipeline(
    step_1=digits_data_loader(),
    step_2=svc_trainer(),
)

first_pipeline_instance.run()
```

</details>
