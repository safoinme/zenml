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
from zenml.integrations.evidently.steps import (
    EvidentlyColumnMapping,
    EvidentlyProfileParameters,
    evidently_profile_step,
)

drift_detector = evidently_profile_step(
    step_name="drift_detector",
    params=EvidentlyProfileParameters(
        column_mapping=EvidentlyColumnMapping(
            target="class", prediction="class"
        ),
        profile_sections=[
            "dataquality",
            "categoricaltargetdrift",
            "numericaltargetdrift",
            "datadrift",
        ],
        verbose_level=1,
    ),
)
