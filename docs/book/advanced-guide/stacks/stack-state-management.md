---
description: How to start, stop, provision, and deprovision stacks and stack components
---

# Managing Stack Component States

Some stack components come with built-in daemons for connecting to the
underlying remote infrastructure. These stack components expose 
functionality for provisioning, deprovisioning, starting, or stopping the 
corresponding daemons.

{% hint style="info" %}
See the advanced section on [Services](manage-external-services.md) for more 
information on daemons.
{% endhint %}

For such components, you can manage the daemon state using the 
`zenml <STACK_COMPONENT> up` and `zenml <STACK_COMPONENT> down` commands.
Alternatively, you can also use `zenml stack up` or `zenml stack down` to 
manage the state of your entire stack:

```shell
zenml stack up  # Provision and start all stack components
zenml orchestrator up  # Provision and start the orchestrator only

zenml stack down  # Stop all stack components
zenml orchestrator down  # Stop the orchestrator only

zenml stack down --force  # Stop and deprovision all stack components
zenml orchestrator down --force  # Stop and deprovision the orchestrator only
```

## Defining States of Custom Components

By default, each stack component is assumed to be in a provisioned and running
state right after creation. However, if you want to write a custom component 
and have fine-grained control over its state, you can overwrite the 
following properties and methods of the `StackComponent` base interface to
configure the component according to your needs:

```python
class StackComponent:
    """Abstract class for all components of a ZenML stack."""
    ...
    
    @property
    def is_provisioned(self) -> bool:
        """If the component provisioned resources to run."""
        return True

    @property
    def is_running(self) -> bool:
        """If the component is running."""
        return True

    def provision(self) -> None:
        """Provisions resources to run the component."""

    def deprovision(self) -> None:
        """Deprovisions all resources of the component."""
        
    def resume(self) -> None:
        """Resumes the provisioned resources of the component."""

    def suspend(self) -> None:
        """Suspends the provisioned resources of the component."""

    ...
```