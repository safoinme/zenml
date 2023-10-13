#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.


import sys

import pytest

from tests.integration.examples.utils import run_example


@pytest.mark.skipif(
    sys.version_info > (3, 10),
    reason="Kubeflow integration not installed in Python 3.11",
)
def test_example(request: pytest.FixtureRequest) -> None:
    """Runs the kubeflow_pipelines_orchestration example.

    Args:
        tmp_path_factory: Factory to generate temporary test paths.
    """
    name = "tensorflow"
    with run_example(
        request=request,
        name=name,
        pipelines={"mnist_pipeline": (1, 4)},
    ):
        pass
