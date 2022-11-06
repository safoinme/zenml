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
from contextlib import ExitStack as does_not_raise

from PIL import Image

from tests.unit.test_general import _test_materializer
from zenml.integrations.pillow.materializers.pillow_image_materializer import (
    PillowImageMaterializer,
)
from zenml.post_execution.pipeline import PipelineRunView


def test_materializer_works_for_pillow_image_objects(clean_client):
    """Check the materializer is able to handle PIL image objects."""
    with does_not_raise():
        _test_materializer(
            step_output=Image.new("RGB", (10, 10), color="red"),
            materializer=PillowImageMaterializer,
        )

    last_run = PipelineRunView(clean_client.zen_store.list_runs()[-1])
    image = last_run.steps[-1].output.read()
    assert isinstance(image, Image.Image)
