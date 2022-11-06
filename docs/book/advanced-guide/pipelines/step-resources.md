---
description: How to specify per-step resources
---

Some steps of your machine learning pipeline might be more resource-intensive
and require special hardware to execute. In such cases, you can specify the 
required resources for steps as follows:

{% tabs %}
{% tab title="Functional API" %}

```python
from zenml.steps import step, ResourceSettings

@step(settings={"resources": ResourceSettings(cpu_count=8, gpu_count=2)})
def training_step(...) -> ...:
    # train a model
```
{% endtab %}
{% tab title="Class-based API" %}
```python
from zenml.steps import BaseStep, ResourceSettings

class TrainingStep(BaseStep):
    ...

step = TrainingStep(settings = {"resources": ResourceSettings(cpu_count=8, gpu_count=2)})
```
{% endtab %}
{% endtabs %}


{% hint style="info" %}
If you're using an orchestrator which does not support this feature or its 
underlying infrastructure doesn't cover your requirements, you can also take a 
look at [step operators](../../component-gallery/step-operators/step-operators.md) 
which allow you to execute individual steps of your pipeline in environments 
independent of your orchestrator. 
{% endhint %}
