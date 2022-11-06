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

from scipy.sparse import coo_matrix, spmatrix

from tests.unit.test_general import _test_materializer
from zenml.integrations.scipy.materializers.sparse_materializer import (
    SparseMaterializer,
)
from zenml.post_execution.pipeline import PipelineRunView


def test_scipy_sparse_matrix_materializer(clean_client):
    """Tests whether the steps work for the SciPy sparse matrix materializer."""
    with does_not_raise():
        _test_materializer(
            step_output=coo_matrix(
                ([1, 2, 3], ([0, 1, 2], [0, 1, 2])), shape=(3, 3)
            ),
            materializer=SparseMaterializer,
        )

    last_run = PipelineRunView(clean_client.zen_store.list_runs()[-1])
    sparse_matrix = last_run.steps[-1].output.read()
    assert isinstance(sparse_matrix, spmatrix)
    assert sparse_matrix.format == "coo"
    assert sparse_matrix.shape == (3, 3)
    assert sparse_matrix.nnz == 3
    assert sparse_matrix.data.tolist() == [1, 2, 3]
    assert sparse_matrix.row.tolist() == [0, 1, 2]
    assert sparse_matrix.col.tolist() == [0, 1, 2]
