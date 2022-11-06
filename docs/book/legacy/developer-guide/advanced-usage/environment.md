---
description: How to access run names and other global data from within a step
---

In addition to [Step Fixtures](./step-fixtures.md), ZenML provides another
interface where ZenML data can be accessed from within a step, the
`Environment`, which can be used to get further information about the
environment where the step is executed, such as the system it is running on,
the Python version, the name of the current step, pipeline, and run, and more.

As an example, this is how you could use the `Environment` to find out the name of the current step, pipeline, and run:
```
from zenml.environment import Environment


@step
def my_step(...)
    env = Environment().step_environment
    step_name = env.step_name
    pipeline_name = env.pipeline_name
    run_id = env.pipeline_run_id
```

{% hint style="info" %}
To explore all possible operations that can be performed via the
`Environment`, please consult the API docs section on
[Environment](https://apidocs.zenml.io/latest/core_code_docs/core-environment/#zenml.environment.Environment).
{% endhint %}