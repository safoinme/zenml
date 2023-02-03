# 📊 Visualize statistics
This examples show-cases the built-in `FacetStatisticsVisualizer` using the 
[Facets Overview](https://pypi.org/project/facets-overview/) integration. 
[Facets](https://pair-code.github.io/facets/) is an awesome project that 
helps users visualize large amounts of data in a coherent way.

## 🗺 Overview
Here, we are using the [Boston Housing Price Regression](https://keras.io/api/datasets/boston_housing/) 
dataset. We create a simple pipeline that returns two pd.DataFrames, one for 
the training data and one for the test data. In the post-execution workflow 
we then plug in the visualization class that visualizes the statistics of these 
DataFrames for us. 

This visualization is produced with the following code:

```python
from zenml.post_execution import get_pipelines
from zenml.integrations.facets.visualizers.facet_statistics_visualizer import (
    FacetStatisticsVisualizer,
)

def visualize_statistics():
    pipe = get_pipelines()[-1]
    importer_outputs = pipe.runs[-1].get_step(step="importer")
    FacetStatisticsVisualizer().visualize(importer_outputs)

visualize_statistics()
```

It produces the following visualization:

![Statistics for Boston housing dataset](assets/statistics-boston-housing.png)


# 🖥 Run it locally

## ⏩ SuperQuick `statistics` run

If you're really in a hurry and just want to see this example pipeline run
without wanting to fiddle around with all the individual installation and
configuration steps, just run the following:

```shell
zenml example run facets_visualize_statistics
```

## 👣 Step-by-Step
### 📄 Prerequisites 
In order to run this example, you need to install and initialize ZenML:

```shell
# install CLI
pip install "zenml[server]"

# install ZenML integrations
zenml integration install tensorflow facets

# pull example
zenml example pull facets_visualize_statistics
cd zenml_examples/facets_visualize_statistics

# Initialize ZenML repo
zenml init

# Start the ZenServer to enable dashboard access
zenml up
```

### ▶️ Run the Code
Now we're ready. Execute:

```bash
python run.py
```
Alternatively, if you want to run based on the config.yaml you can run with:

```bash
zenml pipeline run pipelines/facets_pipeline/facets_pipeline.py -c config.yaml
```

### 🧽 Clean up
In order to clean up, delete the remaining ZenML references.

```shell
rm -rf zenml_examples
```
