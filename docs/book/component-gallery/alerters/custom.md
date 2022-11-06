---
description: How to develop a custom alerter
---

## Base Abstraction

The base abstraction for alerters is very basic, as it only defines two
abstract methods that subclasses should implement:
- `post()` takes a string, posts it to the desired chat service, and returns 
`True` if the operation succeeded, else `False`.
- `ask()` does the same as `post()`, but after sending the message, it waits
until someone approves or rejects the operation from within the chat service
(e.g., by sending "approve" / "reject" to the bot as response).
`ask()` then only returns `True` if the operation succeeded and was approved,
else `False`.

Then base abstraction looks something like this:

```python
class BaseAlerter(StackComponent, ABC):
    """Base class for all ZenML alerters."""

    def post(
        self, message: str, params: Optional[BaseAlerterStepParameters]
    ) -> bool:
        """Post a message to a chat service."""
        return True

    def ask(
        self, question: str, params: Optional[BaseAlerterStepParameters]
    ) -> bool:
        """Post a message to a chat service and wait for approval."""
        return True
```

{% hint style="info" %}
This is a slimmed-down version of the base implementation.
To see the full docstrings and imports, please check 
[the source code on GitHub](https://github.com/zenml-io/zenml/blob/main/src/zenml/alerter/base_alerter.py).
{% endhint %}

## Building your own custom alerter

Creating your own custom alerter can be done in three steps:

1. Create a class that inherits from the `BaseAlerter` and implement the 
`post()` and `ask()` methods.

```python
from typing import Optional

from zenml.alerter import BaseAlerter, BaseAlerterStepParameters

class MyAlerter(BaseAlerter):
    """My alerter class."""

    def post(
        self, message: str, config: Optional[BaseAlerterStepParameters]
    ) -> bool:
        """Post a message to a chat service."""
        ...
        return "Hey, I implemented an alerter."

    def ask(
        self, question: str, config: Optional[BaseAlerterStepParameters]
    ) -> bool:
        """Post a message to a chat service and wait for approval."""
        ...
        return True
```

2. If you need to configure your custom alerter, you can also implement a 
config object.

```python
from zenml.alerter.base_alerter import BaseAlerterConfig

class MyAlerterConfig(BaseAlerterConfig):
    my_param: str 
```

3. Finally, you can bring the implementation and the configuration together in 
a new flavor object.

```python
from typing import Type, TYPE_CHECKING

from zenml.alerter import BaseAlerterFlavor

if TYPE_CHECKING:
    from zenml.stack import StackComponent, StackComponentConfig
    

class MyAlerterFlavor(BaseAlerterFlavor):
    @property
    def name(self) -> str:
        return "my_alerter"

    @property
    def config_class(self) -> Type[StackComponentConfig]:
        from my_alerter_config import MyAlerterConfig

        return MyAlerterConfig

    @property
    def implementation_class(self) -> Type[StackComponent]:
        from my_alerter import MyAlerter

        return MyAlerter

```

Once you are done with the implementation, you can register your new flavor 
through the CLI as:

```shell
zenml alerter flavor register <THE-SOURCE-PATH-OF-YOUR-ALERTER-FLAVOR>
```

{% hint style="warning" %}
It is important to draw attention to when and how these abstractions are 
coming into play in a ZenML workflow.

- The **MyAlerterFlavor** class is imported and utilized upon the creation 
of the custom flavor through the CLI.
- The **MyAlerterConfig** class is imported when someone tries to 
register/update a stack component with the `my_alerter` flavor. Especially, 
during the registration process of the stack component, the config will be used 
to validate the values given by the user. As `Config` object are inherently 
`pydantic` objects, you can also add your own custom validators here.
- The **MyAlerter** only comes into play when the component is ultimately in 
use. 

The design behind this interaction lets us separate the configuration of the 
flavor from its implementation. This way we can register flavors and components 
even when the major dependencies behind their implementation are not installed
in our local setting (assuming the `MyAlerterFlavor` and the `MyAlerterConfig`
are implemented in a different module/path than the actual `MyAlerter`).
{% endhint %}

