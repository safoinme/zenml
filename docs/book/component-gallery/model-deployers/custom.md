---
description: How to develop a custom model deployer
---

To deploy and manage your trained machine learning models, ZenML provides a
stack component called `Model Deployer`. This component is responsible for
interacting with the deployment tool, framework or platform.

When present in a stack, the model deployer can also act as a registry for 
models that are served with ZenML. You can use the model deployer to list all 
models that are currently deployed for online inference or filtered according 
to a particular pipeline run or step, or to suspend, resume or delete an 
external model server managed through ZenML.

## Base Abstraction

In ZenML, the base abstraction of the model deployer is built on top of three 
major criteria:

1. It needs to contain all the stack-related configuration attributes required 
   to interact with the remote model serving tool, service or platform (e.g.
   hostnames, URLs, references to credentials, other client-related
   configuration parameters).
    
2. It needs to implement the continuous deployment logic necessary to deploy 
   models in a way that updates an existing model server that is already serving 
   a previous version of the same model instead of creating a new model server
   for every new model version (see the `deploy_model` abstract method).
   This functionality can be consumed directly from ZenML pipeline steps, but
   it can also be used outside the pipeline to deploy ad-hoc models. It is
   also usually coupled with a standard model deployer step, implemented by
   each integration, that hides the details of the deployment process from
   the user.
    
3. It needs to act as a ZenML BaseService registry, where every BaseService 
   instance is used as an internal representation of a remote model server (see 
   the `find_model_server` abstract method). To achieve this, it must be able to
   re-create the configuration of a BaseService from information that is
   persisted externally, alongside or even as part of the remote model server
   configuration itself. For example, for model servers that are implemented as
   Kubernetes resources, the BaseService instances can be serialized and saved
   as Kubernetes resource annotations. This allows the model deployer to keep
   track of all externally running model servers and to re-create their
   corresponding BaseService instance representations at any given time.
   The model deployer also defines methods that implement basic life-cycle
   management on remote model servers outside the coverage of a pipeline
   (see `stop_model_server`, `start_model_server` and `delete_model_server`).

Putting all these considerations together, we end up with the following
interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type
from uuid import UUID

from zenml.enums import StackComponentType
from zenml.services import BaseService, ServiceConfig
from zenml.stack import StackComponent, StackComponentConfig, Flavor

DEFAULT_DEPLOYMENT_START_STOP_TIMEOUT = 300


class BaseModelDeployerConfig(StackComponentConfig):
    """Base class for all ZenML model deployer configurations."""


class BaseModelDeployer(StackComponent, ABC):
    """Base class for all ZenML model deployers."""

    @abstractmethod
    def deploy_model(
        self,
        config: ServiceConfig,
        replace: bool = False,
        timeout: int = DEFAULT_DEPLOYMENT_START_STOP_TIMEOUT,
    ) -> BaseService:
        """Abstract method to deploy a model."""

    @staticmethod
    @abstractmethod
    def get_model_server_info(
        service: BaseService,
    ) -> Dict[str, Optional[str]]:
        """Give implementation-specific way to extract relevant model server
        properties for the user."""

    @abstractmethod
    def find_model_server(
        self,
        running: bool = False,
        service_uuid: Optional[UUID] = None,
        pipeline_name: Optional[str] = None,
        pipeline_run_id: Optional[str] = None,
        pipeline_step_name: Optional[str] = None,
        model_name: Optional[str] = None,
        model_uri: Optional[str] = None,
        model_type: Optional[str] = None,
    ) -> List[BaseService]:
        """Abstract method to find one or more model servers that match the
        given criteria."""

    @abstractmethod
    def stop_model_server(
        self,
        uuid: UUID,
        timeout: int = DEFAULT_DEPLOYMENT_START_STOP_TIMEOUT,
        force: bool = False,
    ) -> None:
        """Abstract method to stop a model server."""

    @abstractmethod
    def start_model_server(
        self,
        uuid: UUID,
        timeout: int = DEFAULT_DEPLOYMENT_START_STOP_TIMEOUT,
    ) -> None:
        """Abstract method to start a model server."""

    @abstractmethod
    def delete_model_server(
        self,
        uuid: UUID,
        timeout: int = DEFAULT_DEPLOYMENT_START_STOP_TIMEOUT,
        force: bool = False,
    ) -> None:
        """Abstract method to delete a model server."""

        
class BaseModelDeployerFlavor(Flavor):
    """Base class for model deployer flavors."""
    
    @property
    @abstractmethod
    def name(self):
        """Returns the name of the flavor."""
        
    @property
    def type(self) -> StackComponentType:
        """Returns the flavor type.

        Returns:
            The flavor type.
        """
        return StackComponentType.MODEL_DEPLOYER

    @property
    def config_class(self) -> Type[BaseModelDeployerConfig]:
        """Returns `BaseModelDeployerConfig` config class.

        Returns:
                The config class.
        """
        return BaseModelDeployerConfig

    @property
    @abstractmethod
    def implementation_class(self) -> Type[BaseModelDeployer]:
        """The class that implements the model deployer."""
```

{% hint style="info" %}
This is a slimmed-down version of the base implementation which aims to 
highlight the abstraction layer. In order to see the full implementation 
and get the complete docstrings, please check the [API docs](https://apidocs.zenml.io/latest/core_code_docs/core-model_deployers/#zenml.model_deployers.base_model_deployer.BaseModelDeployer).
{% endhint %}

## Building your own model deployers

If you want to create your own custom flavor for a model deployer, you can 
follow the following steps:

1. Create a class which inherits from the `BaseModelDeployer` class and 
implement the abstract methods.
2. If you need to provide any configuration, create a class which inherits 
from the `BaseModelDeployerConfig` class add your configuration parameters.
3. Bring both of the implementation and the configuration together by inheriting
from the `BaseModelDeployerFlavor` class. Make sure that you give a `name`
to the flavor through its abstract property.

Once you are done with the implementation, you can register it through the CLI 
as:

```shell
zenml model-deployer flavor register <THE-SOURCE-PATH-OF-YOUR-MODEL_DEPLOYER-FLAVOR>
```

{% hint style="warning" %}
It is important to draw attention to when and how these base abstractions are 
coming into play in a ZenML workflow.

- The **CustomModelDeployerFlavor** class is imported and utilized upon the 
creation of the custom flavor through the CLI.
- The **CustomModelDeployerConfig** class is imported when someone tries to 
register/update a stack component with this custom flavor. Especially, 
during the registration process of the stack component, the config will be used 
to validate the values given by the user. As `Config` object are inherently 
`pydantic` objects, you can also add your own custom validators here.
- The **CustomModelDeployer** only comes into play when the component is 
ultimately in use. 

The design behind this interaction lets us separate the configuration of the 
flavor from its implementation. This way we can register flavors and components 
even when the major dependencies behind their implementation are not installed
in our local setting (assuming the `CustomModelDeployerFlavor` and the 
`CustomModelDeployerConfig` are implemented in a different module/path than
the actual `CustomModelDeployer`).
{% endhint %}
