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
"""Implementation of Deepchecks dataset materializer."""

from typing import Any, Type

from deepchecks.tabular import Dataset

from zenml.artifacts import DataArtifact
from zenml.materializers.base_materializer import BaseMaterializer
from zenml.materializers.pandas_materializer import PandasMaterializer

DEFAULT_FILENAME = "data.binary"


class DeepchecksDatasetMaterializer(BaseMaterializer):
    """Materializer to read data to and from Deepchecks dataset."""

    ASSOCIATED_TYPES = (Dataset,)
    ASSOCIATED_ARTIFACT_TYPES = (DataArtifact,)

    def handle_input(self, data_type: Type[Any]) -> Dataset:
        """Reads pandas dataframes and creates deepchecks.Dataset from it.

        Args:
            data_type: The type of the data to read.

        Returns:
            A Deepchecks Dataset.
        """
        super().handle_input(data_type)

        # Outsource to pandas
        pandas_materializer = PandasMaterializer(self.artifact)
        df = pandas_materializer.handle_input(data_type)

        # Recreate from pandas dataframe
        return Dataset(df)

    def handle_return(self, df: Dataset) -> None:
        """Serializes pandas dataframe within a Dataset object.

        Args:
            df: A deepchecks.Dataset object.
        """
        super().handle_return(df)

        # Outsource to pandas
        pandas_materializer = PandasMaterializer(self.artifact)
        pandas_materializer.handle_return(df.data)
