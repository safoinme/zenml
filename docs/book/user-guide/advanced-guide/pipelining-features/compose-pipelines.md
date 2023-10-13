---
description: Composing your ZenML pipelines.
---

# Compose pipelines

Sometimes it can be useful to extract some common functionality into separate functions
in order to avoid code duplication. To facilitate this, ZenML allows you to compose your pipelines:

```python
from zenml import pipeline

@pipeline
def data_loading_pipeline(mode: str):
    if mode == "train":
        data = training_data_loader_step()
    else:
        data = test_data_loader_step()
    
    processed_data = preprocessing_step(data)
    return processed_data


@pipeline
def training_pipeline():
    training_data = data_loading_pipeline(mode="train")
    model = training_step(data=training_data)
    test_data = data_loading_pipeline(mode="test")
    evaluation_step(model=model, data=test_data)
```

{% hint style="info" %}
Calling a pipeline inside another pipeline does not actually trigger a separate run of the child pipeline
but instead invokes the steps of the child pipeline to the parent pipeline.
{% endhint %}


<!-- For scarf -->
<figure><img alt="ZenML Scarf" referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=f0b4f458-0a54-4fcd-aa95-d5ee424815bc" /></figure>
