# 🏎 Validate your data with Great Expectations
In data-centric machine learning development, data quality is critical not only
to achieve good initial results but also to keep data drift and concept drift
at bay as your models are deployed to production and interact with live data.

Data validation tools can be employed early on in your machine learning
pipelines to generate data statistical profiles and infer validation rules
that can be used to continuously validate the data being ingested at various
points in the pipeline. For example, data validation rules can be inferred from
the training dataset and then used to validate the datasets used to perform
batch predictions. This is one good way of detecting training-serving skew.

## 🗺 Overview
This example uses the very popular [`Great Expectations`](https://greatexpectations.io/)
open-source library to run data quality tasks on [the Steel Plates Faults Data Set](https://www.openml.org/search?type=data&sort=runs&id=1504&status=active).
provided by Semeion, Research Center of Sciences of Communication, Via Sersale
117, 00128, Rome, Italy. The dataset consists of 27 features describing each
fault (location, size, ...) and 7 binary features indicating the type of fault
(on of 7: Pastry, Z_Scratch, K_Scatch, Stains, Dirtiness, Bumps, Other_Faults).
The latter is commonly used as a binary classification target ('common' or
'other' fault.)

Working with Great Expectations usually starts by configuring a Data Context,
which is the primary entry point for a Great Expectations deployment. All
aspects related to how Great Expectations manages and stores its information
(data sources, data validation rules, data validation results and generated
documentation) is controlled by this Data Context concept.

ZenML makes it really simple to integrate Great Expectations into the pipeline
workflows by automatically configuring Great Expectations to use the Artifact
Store in the active stack to store the Data Context and all its related data.

ZenML also includes materializers for Expectation Suites and Checkpoint Results
and two builtin pipeline steps:

 * a Great Expectations profiler that can be used to automatically generate
 Expectation Suites from input datasets
 * a Great Expectations validator that uses an existing Expectation Suite to
 validate an input dataset

Expectation Suites and Validation Results produced by ZenML can be visualized
locally with the use of a Great Expectation ZenML Visualizer.

## 🧰 How the example is implemented
In this example, we split the Steel Plates Faults dataset into training and
validation slices. We then use the training dataset to generate an Expectations
Suite that we later on use to check that the validation dataset is not skewed.

```python
from zenml.config import DockerSettings
from zenml.integrations.constants import GREAT_EXPECTATIONS, SKLEARN
from zenml.pipelines import pipeline

docker_settings = DockerSettings(
    required_integrations=[SKLEARN, GREAT_EXPECTATIONS]
)


@pipeline(settings={"docker": docker_settings})
def validation_pipeline(
    importer, splitter, profiler, prevalidator, train_validator, test_validator
):
    imported_data = importer()
    train, test = splitter(imported_data)
    suite = profiler(train)
    condition = prevalidator(suite)
    train_validator(train, condition)
    test_validator(test, condition)
```

The Expectation Suite inferred by Great Expectations from a dataset is
intentionally designed to be over-fitted to the data, so the validation
step is expected to fail on the validation dataset.

The post-execution workflow of this example uses the builtin visualizer to
open the Great Expectations generated Data Docs in the web browser to display
information about the generated Expectation Suite and the validation results.

![Expectation Suite visualization UI](assets/expectation_suite.png)
![Validation Result visualization UI](assets/validation_result.png)

# 🖥 Run it locally

## 👣 Step-by-Step
### 📄 Prerequisites 
In order to run this example, you need to install and initialize ZenML:

```shell
# install CLI
pip install "zenml[server]"

# install ZenML integrations
zenml integration install great_expectations sklearn

# pull example
zenml example pull great_expectations_data_validation
cd zenml_examples/great_expectations_data_validation

# Initialize ZenML repo
zenml init

# Start the ZenServer to enable dashboard access
zenml up
```

### 🥞 Set up your stack for Great Expectations

To configure Great Expectations automatically to use the ZenML Artifact Store
to store its persistent state, a data validator stack component of flavor
`great_expectations` must be registered and included in your active stack:  

```shell
zenml data-validator register great_expectations --flavor=great_expectations
zenml stack register ge_stack -o default -a default -dv great_expectations --set
```

### ▶️ Run the Code
Now we're ready. Execute:

```bash
python run.py
```

### 🧽 Clean up
In order to clean up, delete the remaining ZenML references.

```shell
rm -rf zenml_examples
```
