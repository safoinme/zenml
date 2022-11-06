# 🛤️ Track experiments with MLflow Tracking

[MLflow Tracking](https://www.mlflow.org/docs/latest/tracking.html) is a popular
tool that tracks and visualizes experiment runs with their many parameters,
metrics and output files.

## 🗺 Overview
This example showcases how easily mlflow tracking can be integrated into a ZenML pipeline with just a few simple lines
of code.

We'll be using the
[MNIST-digits](https://keras.io/api/datasets/mnist/) dataset and
will train a classifier using [Tensorflow (Keras)](https://www.tensorflow.org/).
We will run two experiments with different parameters (epochs and learning rate)
and log these experiments into a local mlflow backend.

This example uses an mlflow setup that is based on the local filesystem for
things like the artifact store. See the [mlflow
documentation](https://www.mlflow.org/docs/latest/tracking.html#scenario-1-mlflow-on-localhost) 
for details.

In the example script the [mlflow autologger for
Keras](https://www.mlflow.org/docs/latest/tracking.html#tensorflow-and-keras) is
used within the training step to directly hook into the TensorFlow training and
it will log out all relevant parameters, metrics and output files. Additionally,
we explicitly log the test accuracy within the evaluation step.

This example uses an mlflow setup that is based on the local filesystem as
orchestrator and artifact store. See the [mlflow
documentation](https://www.mlflow.org/docs/latest/tracking.html#scenario-1-mlflow-on-localhost)
for details.

## 🧰 How the example is implemented
Adding MLflow tracking to a step is a enabling the experiment tracker for a step. Now you're free to log anything from within 
the step to mlflow. 

ZenML ties all the logs from all steps within a pipeline run together into one mlflow run so that you can see everything
in one place.

 ```python
@step(experiment_tracker="<NAME_OF_EXPERIMENT_TRACKER>")
def tf_trainer(
    x_train: np.ndarray,
    y_train: np.ndarray,
) -> tf.keras.Model:
    """Train a neural net from scratch to recognize MNIST digits return our
    model or the learner"""
    
    # compile model

    mlflow.tensorflow.autolog()
    
    # train model
    
    return model
```
You can also log parameters, metrics and artifacts into nested runs, which 
will be children of the pipeline run. To do so, enable it in the settings like this:

```python
from zenml.integrations.mlflow.flavors.mlflow_experiment_tracker_flavor import MLFlowExperimentTrackerSettings

@step(
    experiment_tracker="<NAME_OF_EXPERIMENT_TRACKER>",
    settings={
        "experiment_tracker.mlflow": MLFlowExperimentTrackerSettings(
            nested=True
        )
    }
)
def tf_trainer(
    x_train: np.ndarray,
    y_train: np.ndarray,
) -> tf.keras.Model:
    """Train a neural net from scratch to recognize MNIST digits return our
    model or the learner"""
    
    # compile model

    mlflow.tensorflow.autolog()
    
    # train model
    
    return model
```
If you want to enable MLflow tracking when using the class-based API, simply configure your step as follows:

```python
class TFTrainer(BaseStep):
    def entrypoint(
        self,
        x_train: np.ndarray,
        y_train: np.ndarray,
    ) -> tf.keras.Model:
        mlflow.tensorflow.autolog()
        ...

step_instance = TFTrainer()
step_instance.configure(experiment_tracker="<NAME_OF_EXPERIMENT_TRACKER>")
```
# 🖥 Run it locally

## ⏩ SuperQuick `mlflow_tracking` run
If you're really in a hurry and just want to see this example pipeline run
without wanting to fiddle around with all the individual installation and
configuration steps, just run the following:

```shell
zenml example run mlflow_tracking
```

## 👣 Step-by-Step
### 📄 Prerequisites 
In order to run this example, you need to install and initialize ZenML:

```shell
# install CLI
pip install "zenml[server]"

# install ZenML integrations
zenml integration install mlflow tensorflow

# pull example
zenml example pull mlflow_tracking
cd zenml_examples/mlflow_tracking

# Initialize ZenML repo
zenml init

# Start the ZenServer to enable dashboard access
zenml up

# Create and activate the stack with the mlflow experiment tracker component
zenml experiment-tracker register mlflow_tracker --flavor=mlflow
zenml stack register mlflow_stack \
    -a default \
    -o default \
    -e mlflow_tracker
    --set
```

### ▶️ Run the Code
Now we're ready. Execute:

```bash
python run.py
```

Alternatively, if you want to run based on the config.yaml you can run with:

```bash
zenml pipeline run pipelines/training_pipeline/training_pipeline.py -c config.yaml
```

### 🔮 See results
Now we just need to start the mlflow UI to have a look at our two pipeline runs.
To do this we need to run:

```shell
mlflow ui --backend-store-uri <SPECIFIC_MLRUNS_PATH_GOES_HERE>
```

Check the terminal output of the pipeline run to see the exact path appropriate
in your specific case. This will start mlflow at `localhost:5000`. If this port
is already in use on your machine you may have to specify another port:

```shell
 mlflow ui --backend-store-uri <SPECIFIC_MLRUNS_PATH_GOES_HERE> -p 5001
 ```

### 🧽 Clean up
In order to clean up, delete the remaining ZenML references.

```shell
rm -rf zenml_examples
rm -rf <SPECIFIC_MLRUNS_PATH_GOES_HERE>
```

# 📜 Learn more

Our docs regarding the MLflow experiment tracker integration can be found [here](https://docs.zenml.io/component-gallery/experiment-trackers/mlflow).


If you want to learn more about experiment trackers in general or about how to build your own experiment trackers in ZenML
check out our [docs](https://docs.zenml.io/component-gallery/experiment-trackers/custom).
