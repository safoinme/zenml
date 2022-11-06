---
description: How to develop a custom Data Validator
---

{% hint style="warning" %}
**Base abstraction in progress!**

We are actively working on the base abstraction for the Data Validators, which 
will be available soon. As a result, their extension is not recommended at the 
moment. When you are selecting a data validator for your stack, you can use 
one of [the existing flavors](./data-validators.md#data-validator-flavors).

If you need to implement your own Data Validator flavor, you can still do so,
but keep in mind that you may have to refactor it when the base abstraction
is updated. 
{% endhint %}

ZenML comes equipped with [Data Validator implementations](./data-validators.md#data-validator-flavors)
that integrate a variety of data logging and validation libraries, frameworks
and platforms. However, if you need to use a different library or service as a
backend for your ZenML Data Validator, you can extend ZenML to provide your own
custom Data Validator implementation.

## Build your own custom data validator

If you want to implement your own custom Data Validator, you can follow the
following steps:


1. Create a class which inherits from [the `BaseDataValidator` class](https://apidocs.zenml.io/latest/core_code_docs/core-data_validators/#zenml.data_validators.base_data_validator.BaseDataValidator)
and override one or more of the abstract methods, depending on the
capabilities of the underlying library/service that you want to integrate.
2. If you need any configuration, you can create a class which inherits 
from the `BaseDataValidatorConfig` class.
3. Bring both of these classes together by inheriting from the
`BaseDataValidatorFlavor`.
4. (Optional) You should also provide some standard steps that others can easily
insert into their pipelines for instant access to data validation features.

Once you are done with the implementation, you can register it through the CLI 
as:

```shell
zenml data-validator flavor register <THE-SOURCE-PATH-OF-YOUR-DATA-VALIDATOR-FLAVOR>
```

{% hint style="warning" %}
It is important to draw attention to when and how these base abstractions are 
coming into play in a ZenML workflow.

- The **CustomDataValidatorFlavor** class is imported and utilized upon the 
creation of the custom flavor through the CLI.
- The **CustomDataValidatorConfig** class is imported when someone tries to 
register/update a stack component with this custom flavor. Especially, 
during the registration process of the stack component, the config will be used 
to validate the values given by the user. As `Config` object are inherently 
`pydantic` objects, you can also add your own custom validators here.
- The **CustomDataValidator** only comes into play when the component is 
ultimately in use. 

The design behind this interaction lets us separate the configuration of the 
flavor from its implementation. This way we can register flavors and components 
even when the major dependencies behind their implementation are not installed
in our local setting (assuming the `CustomDataValidatorFlavor` and the 
`CustomDataValidatorConfig` are implemented in a different module/path than
the actual `CustomDataValidator`).
{% endhint %}
