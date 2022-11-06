#  Copyright (c) ZenML GmbH 2021. All Rights Reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

from pipelines.drift_detection_pipeline.drift_detection_pipeline import (
    drift_detection_pipeline,
)
from rich import print
from steps.data_loader.data_loader_step import data_loader
from steps.data_splitter.data_splitter_step import data_splitter
from steps.drift_analyzer.drift_analyzer_step import analyze_drift
from steps.drift_detector.drift_detector_step import drift_detector

from zenml.integrations.evidently.visualizers import EvidentlyVisualizer
from zenml.post_execution import get_pipeline


def visualize_statistics():
    pipeline = get_pipeline(pipeline="drift_detection_pipeline")
    evidently_outputs = pipeline.runs[-1].get_step(step="drift_detector")
    EvidentlyVisualizer().visualize(evidently_outputs)


if __name__ == "__main__":
    pipeline_instance = drift_detection_pipeline(
        data_loader=data_loader(),
        data_splitter=data_splitter(),
        drift_detector=drift_detector,
        drift_analyzer=analyze_drift(),
    )
    pipeline_instance.run()

    last_run = pipeline_instance.get_runs()[-1]
    drift_analysis_step = last_run.get_step(step="drift_analyzer")
    print(f"Data drift detected: {drift_analysis_step.output.read()}")

    visualize_statistics()
