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

from unittest import mock
from unittest.mock import ANY
from uuid import uuid4

import pytest

from zenml.config.compiler import Compiler
from zenml.config.step_configurations import Step
from zenml.enums import ExecutionStatus, SorterOps
from zenml.models.page_model import Page
from zenml.orchestrators import cache_utils
from zenml.steps import Output, step
from zenml.steps.base_step import BaseStep


def test_is_cache_enabled():
    """Unit test for `is_cache_enabled()`.

    Tests that:
    - caching is enabled by default (when neither step nor pipeline set it),
    - caching is always enabled if explicitly enabled for the step,
    - caching is always disabled if explicitly disabled for the step,
    - caching is set to the pipeline cache if not configured for the step.
    """
    # Caching is enabled by default
    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=None, pipeline_enable_cache=None
        )
        is True
    )

    # Caching is always enabled if explicitly enabled for the step
    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=True,
            pipeline_enable_cache=True,
        )
        is True
    )

    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=True,
            pipeline_enable_cache=False,
        )
        is True
    )

    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=True,
            pipeline_enable_cache=None,
        )
        is True
    )

    # Caching is always disabled if explicitly disabled for the step
    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=False,
            pipeline_enable_cache=True,
        )
        is False
    )

    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=False,
            pipeline_enable_cache=False,
        )
        is False
    )

    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=False,
            pipeline_enable_cache=None,
        )
        is False
    )

    # Caching is set to the pipeline cache if not configured for the step
    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=None,
            pipeline_enable_cache=True,
        )
        is True
    )

    assert (
        cache_utils.is_cache_enabled(
            step_enable_cache=None,
            pipeline_enable_cache=False,
        )
        is False
    )


def _compile_step(step: BaseStep) -> Step:
    # Call the step here to finalize the configuration
    step()

    compiler = Compiler()
    return compiler._compile_step(
        step=step,
        pipeline_settings={},
        pipeline_extra={},
        stack=None,
    )


@step
def _cache_test_step() -> Output(output_1=str, output_2=int):
    return "Hello World", 42


@pytest.fixture
def generate_cache_key_kwargs(local_artifact_store):
    """Returns a dictionary of inputs for the cache key generation."""
    return {
        "step": _compile_step(_cache_test_step()),
        "input_artifact_ids": {"input_1": uuid4()},
        "artifact_store": local_artifact_store,
        "project_id": uuid4(),
    }


def test_generate_cache_key_is_deterministic(generate_cache_key_kwargs):
    """Check that the cache key does not change if the inputs are the same."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 == key_2


def test_generate_cache_key_considers_project_id(generate_cache_key_kwargs):
    """Check that the cache key changes if the project ID changes."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    generate_cache_key_kwargs["project_id"] = uuid4()
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 != key_2


def test_generate_cache_key_considers_artifact_store_id(
    generate_cache_key_kwargs,
):
    """Check that the cache key changes if the artifact store ID changes."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    generate_cache_key_kwargs["artifact_store"].id = uuid4()
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 != key_2


def test_generate_cache_key_considers_artifact_store_path(
    generate_cache_key_kwargs, mocker
):
    """Check that the cache key changes if the artifact store path changes."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    mock_path = mock.PropertyMock(return_value="new/path")
    mocker.patch.object(
        type(generate_cache_key_kwargs["artifact_store"]),
        "path",
        new_callable=mock_path,
    )
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 != key_2


def test_generate_cache_key_considers_step_source(generate_cache_key_kwargs):
    """Check that the cache key changes if the step source changes."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    generate_cache_key_kwargs["step"].spec.__config__.allow_mutation = True
    generate_cache_key_kwargs["step"].spec.source = "Some.new.source"
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 != key_2


def test_generate_cache_key_considers_step_parameters(
    generate_cache_key_kwargs,
):
    """Check that the cache key changes if the step parameters change."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    generate_cache_key_kwargs["step"].config.__config__.allow_mutation = True
    generate_cache_key_kwargs["step"].config.parameters = {"new_param": 42}
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 != key_2


def test_generate_cache_key_considers_input_artifacts(
    generate_cache_key_kwargs,
):
    """Check that the cache key changes if the input artifacts change."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    generate_cache_key_kwargs["input_artifact_ids"] = {"input_1": uuid4()}
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 != key_2


def test_generate_cache_key_considers_output_artifacts(
    generate_cache_key_kwargs,
):
    """Check that the cache key changes if the output artifacts change."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    generate_cache_key_kwargs["step"].config.__config__.allow_mutation = True
    generate_cache_key_kwargs["step"].config.outputs.pop("output_1")
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 != key_2


def test_generate_cache_key_considers_caching_parameters(
    generate_cache_key_kwargs,
):
    """Check that the cache key changes if the caching parameters change."""
    key_1 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    generate_cache_key_kwargs["step"].config.__config__.allow_mutation = True
    generate_cache_key_kwargs["step"].config.caching_parameters = {
        "Aria hates caching": False
    }
    key_2 = cache_utils.generate_cache_key(**generate_cache_key_kwargs)
    assert key_1 != key_2


def test_fetching_cached_step_run_queries_cache_candidates(
    mocker, create_step_run
):
    """Tests fetching a cached step run."""
    mock_list_run_steps = mocker.patch(
        "zenml.client.Client.list_run_steps",
        return_value=Page(
            page=1,
            size=1,
            total_pages=1,
            total=0,
            items=[],
        ),
    )

    assert cache_utils.get_cached_step_run(cache_key="cache_key") is None

    cache_candidate = create_step_run()

    mock_list_run_steps = mocker.patch(
        "zenml.client.Client.list_run_steps",
        return_value=Page(
            page=1,
            size=1,
            total_pages=1,
            total=1,
            items=[cache_candidate],
        ),
    )

    cached_step = cache_utils.get_cached_step_run(cache_key="cache_key")
    assert cached_step == cache_candidate
    mock_list_run_steps.assert_called_with(
        project_id=ANY,
        cache_key="cache_key",
        status=ExecutionStatus.COMPLETED,
        sort_by=f"{SorterOps.DESCENDING}:created",
        size=1,
    )


def test_fetching_cached_step_run_uses_latest_candidate(
    clean_client, sample_pipeline_run_request_model, sample_step_request_model
):
    """Tests that the latest step run with the same cache key is used for
    caching."""
    sample_step_request_model.cache_key = "cache_key"
    sample_step_request_model.project = clean_client.active_project.id
    sample_pipeline_run_request_model.project = clean_client.active_project.id

    # Create a pipeline run and step run
    clean_client.zen_store.create_run(sample_pipeline_run_request_model)
    sample_step_request_model.pipeline_run_id = (
        sample_pipeline_run_request_model.id
    )
    response_1 = clean_client.zen_store.create_run_step(
        sample_step_request_model
    )

    # Create another pipeline run and step run, with the same cache key
    sample_pipeline_run_request_model.id = uuid4()
    sample_pipeline_run_request_model.name = "new_run_name"
    clean_client.zen_store.create_run(sample_pipeline_run_request_model)
    sample_step_request_model.pipeline_run_id = (
        sample_pipeline_run_request_model.id
    )
    response_2 = clean_client.zen_store.create_run_step(
        sample_step_request_model
    )

    # The second step run was created after the first one
    assert response_2.created > response_1.created

    cached_step = cache_utils.get_cached_step_run(cache_key="cache_key")
    assert cached_step == response_2
