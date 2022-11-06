---
description: How to develop a custom experiment tracker
---

{% hint style="warning" %}
**Base abstraction in progress!**

We are actively working on the base abstraction for the Experiment Tracker,
which  will be available soon. As a result, their extension is not recommended 
at the moment. When you are selecting an Experiment Tracker for your stack, 
you can use one of [the existing flavors](./experiment-trackers.md#experiment-tracker-flavors).

If you need to implement your own Experiment Tracker flavor, you can still do 
so, but keep in mind that you may have to refactor it when the base abstraction
is released.
{% endhint %}

## Build your own custom experiment tracker

If you want to create your own custom flavor for an experiment tracker, you can 
follow the following steps:

1. Create a class which inherits from the `BaseExperimentTracker` class and 
implement the abstract methods.
2. If you need any configuration, create a class which inherits from the 
`BaseExperimentTrackerConfig` class add your configuration parameters.
3. Bring both of the implementation and the configuration together by inheriting
from the `BaseExperimentTrackerFlavor` class.

Once you are done with the implementation, you can register it through the CLI 
as:

```shell
zenml experiment-tracker flavor register <THE-SOURCE-PATH-OF-YOUR-EXPERIMENT-TRACKER-FLAVOR>
```

{% hint style="warning" %}
It is important to draw attention to when and how these base abstractions are 
coming into play in a ZenML workflow.

- The **CustomExperimentTrackerFlavor** class is imported and utilized upon the 
creation of the custom flavor through the CLI.
- The **CustomExperimentTrackerConfig** class is imported when someone tries to 
register/update a stack component with this custom flavor. Especially, 
during the registration process of the stack component, the config will be used 
to validate the values given by the user. As `Config` object are inherently 
`pydantic` objects, you can also add your own custom validators here.
- The **CustomExperimentTracker** only comes into play when the component is 
ultimately in use. 

The design behind this interaction lets us separate the configuration of the 
flavor from its implementation. This way we can register flavors and components 
even when the major dependencies behind their implementation are not installed
in our local setting (assuming the `CustomExperimentTrackerFlavor` and the 
`CustomExperimentTrackerConfig` are implemented in a different module/path than
the actual `CustomExperimentTracker`).
{% endhint %}