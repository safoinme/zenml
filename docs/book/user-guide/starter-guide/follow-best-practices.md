---
description: Recommended repository structure and best practices.
---

# Follow best practices

Until now, you probably have kept all your code in one single file. In production, it is recommended to split up your steps and pipelines into separate files.

```markdown
.
├── .dockerignore
├── Dockerfile
├── steps
│   ├── loader_step
│   │   ├── .dockerignore (optional)
│   │   ├── Dockerfile (optional)
│   │   ├── loader_step.py
│   │   └── requirements.txt (optional)
│   └── training_step
│       └── ...
├── pipelines
│   ├── training_pipeline
│   │   ├── .dockerignore (optional)
│   │   ├── config.yaml (optional)
│   │   ├── Dockerfile (optional)
│   │   ├── training_pipeline.py
│   │   └── requirements.txt (optional)
│   └── deployment_pipeline
│       └── ...
├── notebooks
│   └── *.ipynb
├── requirements.txt
├── .zen
└── run.py
```

Check out how to initialize your project from a template following best practices in the [Project templates](./using-project-templates.md#generating-project-from-a-project-template) section.

#### Steps

Keep your steps in separate Python files. This allows you to optionally keep their utils, dependencies, and Dockerfiles separate.


#### Logging

ZenML records the root python logging handler's output into the artifact store as a side-effect of running a step. Therefore, when writing steps, use the `logging` module to record logs, to ensure that these logs then show up in the ZenML dashboard.

```python
# Use ZenML handler
from zenml.logger import get_logger

logger = get_logger(__name__)
...

@step
def training_data_loader():
    # This will show up in the dashboard
    logger.info("My logs")
```

#### Pipelines

Just like steps, keep your pipelines in separate Python files. This allows you to optionally keep their utils, dependencies, and Dockerfiles separate.

It is recommended that you separate the pipeline execution from the pipeline definition so that importing the pipeline does not immediately run it. See [run.py](follow-best-practices.md) for more details.

{% hint style="warning" %}
Do not give pipelines or pipeline instances the name "pipeline". Doing this will overwrite the imported `pipeline` and decorator and lead to failures at later stages if more pipelines are decorated there.
{% endhint %}

{% hint style="info" %}
Pipeline names are their unique identifiers, so using the same name for different pipelines will create a mixed history where two versions of a pipeline are two very different entities.
{% endhint %}

#### .dockerignore

Containerized orchestrators and step operators load your complete project files into a Docker image for execution. To speed up the process and reduce Docker image sizes, exclude all unnecessary files (like data, virtual environments, git repos, etc.) within the `.dockerignore`.

#### Dockerfile (optional)

By default, ZenML uses the official[ zenml docker image](https://hub.docker.com/r/zenmldocker/zenml) as a base for all pipeline and step builds. You can use your own Dockerfile to overwrite this behavior. Learn more [here](../advanced-guide/environment-management/containerize-your-pipeline.md).

#### Notebooks

Collect all your notebooks in one place.

#### .zen

By running `zenml init` at the root of your project, you define the project scope for ZenML. In ZenML terms, this will be called your "source's root". This will be used to resolve import paths and store configurations.

Although this is optional, it is recommended that you do this for all of your projects.

{% hint style="warning" %}
All of your import paths should be relative to the source's root.
{% endhint %}

#### run.py

Putting your pipeline runners in the root of the repository ensures that all imports that are defined relative to the project root resolve for the pipeline runner. In case there is no `.zen` defined this also defines the implicit source's root.

<!-- For scarf -->
<figure><img alt="ZenML Scarf" referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=f0b4f458-0a54-4fcd-aa95-d5ee424815bc" /></figure>
