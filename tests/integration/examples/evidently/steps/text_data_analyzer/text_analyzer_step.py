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
import json
from typing import Tuple

from typing_extensions import Annotated

from zenml import step


@step
def text_analyzer(
    report: str,
) -> Tuple[
    Annotated[int, "ref_missing_values"],
    Annotated[int, "comp_missing_values"],
]:
    """Analyze the Evidently text Report and return the number of missing
    values in the reference and comparison datasets.
    """
    result = json.loads(report)["metrics"][0]["result"]
    return (
        result["current"]["number_of_missing_values"],
        result["reference"]["number_of_missing_values"],
    )
