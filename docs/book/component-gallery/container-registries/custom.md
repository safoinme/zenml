---
description: How to develop a custom container registry
---

## Base Abstraction

In the current version of ZenML, container registries have a rather basic base 
abstraction. In essence, their base configuration only features a `uri` 
and their implementation features a non-abstract `prepare_image_push` method for 
validation.

```python
from abc import abstractmethod
from typing import Type

from zenml.enums import StackComponentType
from zenml.stack import Flavor
from zenml.stack.authentication_mixin import (
    AuthenticationConfigMixin,
    AuthenticationMixin,
)
from zenml.utils import docker_utils

class BaseContainerRegistryConfig(AuthenticationConfigMixin):
    """Base config for a container registry."""

    uri: str


class BaseContainerRegistry(AuthenticationMixin):
    """Base class for all ZenML container registries."""

    def prepare_image_push(self, image_name: str) -> None:
        """Conduct necessary checks/preparations before an image gets pushed."""

    def push_image(self, image_name: str) -> str:
        """Pushes a docker image."""
        if not image_name.startswith(self.config.uri):
            raise ValueError(
                f"Docker image `{image_name}` does not belong to container "
                f"registry `{self.config.uri}`."
            )

        self.prepare_image_push(image_name)
        return docker_utils.push_image(image_name)

    
class BaseContainerRegistryFlavor(Flavor):
    """Base flavor for container registries."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the flavor."""
        
    @property
    def type(self) -> StackComponentType:
        """Returns the flavor type."""
        return StackComponentType.CONTAINER_REGISTRY

    @property
    def config_class(self) -> Type[BaseContainerRegistryConfig]:
        """Config class for this flavor."""
        return BaseContainerRegistryConfig

    @property
    def implementation_class(self) -> Type[BaseContainerRegistry]:
        """Implementation class."""
        return BaseContainerRegistry
```

{% hint style="info" %}
This is a slimmed-down version of the base implementation which aims to 
highlight the abstraction layer. In order to see the full implementation 
and get the complete docstrings, please check the [API docs](https://apidocs.zenml.io/latest/core_code_docs/core-container_registries/#zenml.container_registries.base_container_registry.BaseContainerRegistry).
{% endhint %}

## Building your own container registry

If you want to create your own custom flavor for a container registry, you can 
follow the following steps:

1. Create a class which inherits from the `BaseContainerRegistry` class and if 
you need to execute any checks/validation before the image gets pushed, 
you can define these operations in the `prepare_image_push` method. As an 
example, you can check the `AWSContainerRegistry`.
2. If you need further configuration, you can create a class which inherits 
from the `BaseContainerRegistryConfig` class.
3. Bring both of the implementation and the configuration together by inheriting
from the `BaseContainerRegistryFlavor` class.

Once you are done with the implementation, you can register it through the CLI 
as:

```shell
zenml container-registry flavor register <THE-SOURCE-PATH-OF-YOUR-CONTAINER-REGISTRY-FLAVOR>
```

{% hint style="warning" %}
It is important to draw attention to when and how these base abstractions are 
coming into play in a ZenML workflow.

- The **CustomContainerRegistryFlavor** class is imported and utilized upon the 
creation of the custom flavor through the CLI.
- The **CustomContainerRegistryConfig** class is imported when someone tries to 
register/update a stack component with this custom flavor. Especially, 
during the registration process of the stack component, the config will be used 
to validate the values given by the user. As `Config` object are inherently 
`pydantic` objects, you can also add your own custom validators here.
- The **CustomContainerRegistry** only comes into play when the component is 
ultimately in use. 

The design behind this interaction lets us separate the configuration of the 
flavor from its implementation. This way we can register flavors and components 
even when the major dependencies behind their implementation are not installed
in our local setting (assuming the `CustomContainerRegistryFlavor` and the 
`CustomContainerRegistryConfig` are implemented in a different module/path than
the actual `CustomContainerRegistry`).
{% endhint %}