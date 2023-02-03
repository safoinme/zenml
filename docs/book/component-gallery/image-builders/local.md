---
description: How to build container images locally
---

The local image builder is an [image builder](./image-builders.md) flavor which 
comes built-in with ZenML and uses the local Docker installation on your client
machine to build container images.

{% hint style="info" %}
ZenML uses the official Docker Python library to build and push your images. This library
loads its authentication credentials to push images from the default config location: `$HOME/.docker/config.json`.
If your Docker configuration is stored in a different directory, you can use the environment
variable `DOCKER_CONFIG` to override this behavior:
```shell
export DOCKER_CONFIG=/path/to/config_dir
```
The directory that you specify here must contain your Docker configuration in a file called `config.json`.
{% endhint %}

## When to use it

You should use the local image builder if:
* you're able to install and use [Docker](https://www.docker.com) on your client machine.
* you want to use remote components that require containerization without
the additional hassle of configuring infrastructure for an additional component.

## How to deploy it

The local image builder comes with ZenML and works without any additional setup.

## How to use it

To use the Local image builder, we need:
* [Docker](https://www.docker.com) installed and running.
* The Docker client authenticated to push to the container registry that
you intend to use in the same stack.

We can then register the image builder and use it to create a new stack:
```shell
zenml image-builder register <NAME> --flavor=local

# Register and activate a stack with the new image builder
zenml stack register <STACK_NAME> -i <NAME> ... --set
```

For more information and a full list of configurable attributes of the local 
image builder, check out the [API Docs](https://apidocs.zenml.io/latest/core_code_docs/core-image_builders/#zenml.image_builders.local_image_builder.LocalImageBuilder).
