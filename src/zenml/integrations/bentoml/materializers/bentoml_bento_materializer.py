#  Copyright (c) ZenML GmbH 2021. All Rights Reserved.
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
"""Materializer for BentoML Bento objects."""

import os
import tempfile
from typing import Type

from bentoml import export_bento, import_bento
from bentoml._internal.bento import Bento, bento
from bentoml.exceptions import BentoMLException

from zenml.artifacts import DataArtifact
from zenml.io import fileio
from zenml.logger import get_logger
from zenml.materializers.base_materializer import BaseMaterializer
from zenml.utils import io_utils

logger = get_logger(__name__)

DEFAULT_BENTO_FILENAME = "zenml_exported.bento"


class BentoMaterializer(BaseMaterializer):
    """Materializer for Bentoml Bento objects."""

    ASSOCIATED_TYPES = (bento.Bento,)
    ASSOCIATED_ARTIFACT_TYPES = (DataArtifact,)

    def handle_input(self, data_type: Type[bento.Bento]) -> bento.Bento:
        """Read from artifact store.

        Args:
            data_type: An bento.Bento type.

        Returns:
            An bento.Bento object.
        """
        super().handle_input(data_type)

        # Create a temporary directory to store the model
        temp_dir = tempfile.TemporaryDirectory()

        # Copy from artifact store to temporary directory
        io_utils.copy_dir(self.artifact.uri, temp_dir.name)

        # Load the Bento from the temporary directory
        imported_bento = Bento.import_from(
            os.path.join(temp_dir.name, DEFAULT_BENTO_FILENAME)
        )

        # Try save the Bento to the local BentoML store
        try:
            import_bento(os.path.join(temp_dir.name, DEFAULT_BENTO_FILENAME))
        except BentoMLException as e:
            logger.error(f"{e}")
        return imported_bento

    def handle_return(self, bento: bento.Bento) -> None:
        """Write to artifact store.

        Args:
            Bento: An bento.Bento object.
        """
        super().handle_return(bento)

        # Create a temporary directory to store the model
        temp_dir = tempfile.TemporaryDirectory(prefix="zenml-temp-")
        temp_bento_path = os.path.join(temp_dir.name, DEFAULT_BENTO_FILENAME)

        # save the image in a temporary directory
        export_bento(bento.tag, temp_bento_path)

        # copy the saved image to the artifact store
        io_utils.copy_dir(temp_dir.name, self.artifact.uri)

        # Remove the temporary directory
        fileio.rmtree(temp_dir.name)
