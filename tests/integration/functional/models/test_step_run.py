#  Copyright (c) ZenML GmbH 2023. All Rights Reserved.
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
"""Integration tests for step run models."""

import inspect
import random
import string
from typing import TYPE_CHECKING

from tests.integration.functional.conftest import step_with_logs
from tests.integration.functional.zen_stores.utils import (
    constant_int_output_test_step,
    int_plus_one_test_step,
)
from zenml.enums import ExecutionStatus

if TYPE_CHECKING:
    from zenml.client import Client
    from zenml.models.step_run_models import StepRunResponseModel
    from zenml.pipelines.base_pipeline import BasePipeline


def test_step_run_linkage(clean_client: "Client", one_step_pipeline):
    """Integration test for `step.run` property."""
    step_ = constant_int_output_test_step()
    pipe: "BasePipeline" = one_step_pipeline(step_)
    pipe.run()

    # Non-cached run
    pipeline_run = pipe.model.last_run
    step_run = pipeline_run.steps["step_"]
    assert step_run.run == pipeline_run

    # Cached run
    pipe.run()
    pipeline_run_2 = pipe.model.last_run
    step_run_2 = pipeline_run_2.steps["step_"]
    assert step_run_2.status == ExecutionStatus.CACHED


def test_step_run_parent_steps_linkage(
    clean_client: "Client", connected_two_step_pipeline
):
    """Integration test for `step.parent_steps` property."""
    pipeline_instance = connected_two_step_pipeline(
        step_1=constant_int_output_test_step(),
        step_2=int_plus_one_test_step(),
    )
    pipeline_instance.run()
    pipeline_run = pipeline_instance.model.last_run
    step_1 = pipeline_run.steps["step_1"]
    step_2 = pipeline_run.steps["step_2"]
    assert step_1.parent_steps == []
    assert step_2.parent_steps == [step_1]


def test_step_run_has_source_code(clean_client, connected_two_step_pipeline):
    """Test that the step run has correct source code."""
    pipeline_instance = connected_two_step_pipeline(
        step_1=constant_int_output_test_step(),
        step_2=int_plus_one_test_step(),
    )
    pipeline_instance.run()
    pipeline_run = clean_client.get_pipeline(
        "connected_two_step_pipeline"
    ).runs[0]
    step_1 = pipeline_run.steps["step_1"]
    step_2 = pipeline_run.steps["step_2"]
    assert step_1.source_code == inspect.getsource(
        constant_int_output_test_step.entrypoint
    )
    assert step_2.source_code == inspect.getsource(
        int_plus_one_test_step.entrypoint
    )


def test_step_run_with_too_long_source_code_is_truncated(
    clean_client, connected_two_step_pipeline, mocker
):
    """Test that the step source code gets truncated if it is too long."""

    random_source = "".join(random.choices(string.ascii_uppercase, k=1000000))
    mocker.patch("zenml.steps.base_step.BaseStep.source_code", random_source)
    pipeline_instance = connected_two_step_pipeline(
        step_1=constant_int_output_test_step(),
        step_2=int_plus_one_test_step(),
    )
    pipeline_instance.run()
    pipeline_run = clean_client.get_pipeline(
        "connected_two_step_pipeline"
    ).runs[0]
    step_1 = pipeline_run.steps["step_1"]
    step_2 = pipeline_run.steps["step_2"]
    assert step_1.source_code == random_source[:1000] + "..."
    assert step_2.source_code == random_source[:1000] + "..."


def test_step_run_has_docstring(clean_client, connected_two_step_pipeline):
    """Test that the step run has correct docstring."""
    pipeline_instance = connected_two_step_pipeline(
        step_1=constant_int_output_test_step(),
        step_2=int_plus_one_test_step(),
    )
    pipeline_instance.run()
    pipeline_run = clean_client.get_pipeline(
        "connected_two_step_pipeline"
    ).runs[0]
    step_1 = pipeline_run.steps["step_1"]
    step_2 = pipeline_run.steps["step_2"]
    assert step_1.docstring == constant_int_output_test_step.entrypoint.__doc__
    assert step_2.docstring == int_plus_one_test_step.entrypoint.__doc__


def test_step_run_with_too_long_docstring_is_truncated(
    clean_client, connected_two_step_pipeline, mocker
):
    """Test that the step docstring gets truncated if it is too long."""
    random_docstring = "".join(
        random.choices(string.ascii_uppercase, k=1000000)
    )
    mocker.patch("zenml.steps.base_step.BaseStep.docstring", random_docstring)
    pipeline_instance = connected_two_step_pipeline(
        step_1=constant_int_output_test_step(),
        step_2=int_plus_one_test_step(),
    )
    pipeline_instance.run()
    pipeline_run = clean_client.get_pipeline(
        "connected_two_step_pipeline"
    ).runs[0]
    step_1 = pipeline_run.steps["step_1"]
    step_2 = pipeline_run.steps["step_2"]
    assert step_1.docstring == random_docstring[:1000] + "..."
    assert step_2.docstring == random_docstring[:1000] + "..."


def test_disabling_step_logs(clean_client: "Client", one_step_pipeline):
    """Test that disabling step logs works."""

    # By default, step logs should be enabled
    step_ = step_with_logs()
    pipe: "BasePipeline" = one_step_pipeline(step_)
    pipe.configure(enable_cache=False)
    pipe.run()
    _assert_step_logs_enabled(pipe)

    # Test disabling step logs on pipeline level
    pipe.configure(enable_step_logs=False)
    pipe.run()
    _assert_step_logs_disabled(pipe)

    pipe.configure(enable_step_logs=True)
    pipe.run()
    _assert_step_logs_enabled(pipe)

    # Test disabling step logs on step level
    # This should override the pipeline level setting
    step_.configure(enable_step_logs=False)
    pipe.run()
    _assert_step_logs_disabled(pipe)

    step_.configure(enable_step_logs=True)
    pipe.run()
    _assert_step_logs_enabled(pipe)

    # Test disabling step logs on run level
    # This should override both the pipeline and step level setting
    pipe.run(enable_step_logs=False)
    _assert_step_logs_disabled(pipe)

    pipe.configure(enable_step_logs=False)
    step_.configure(enable_step_logs=False)
    pipe.run(enable_step_logs=True)
    _assert_step_logs_enabled(pipe)


def _assert_step_logs_enabled(pipe: "BasePipeline"):
    """Assert that step logs were enabled in the last run."""
    assert _get_first_step_of_last_run(pipe).logs


def _assert_step_logs_disabled(pipe: "BasePipeline"):
    """Assert that step logs were disabled in the last run."""
    assert not _get_first_step_of_last_run(pipe).logs


def _get_first_step_of_last_run(
    pipe: "BasePipeline",
) -> "StepRunResponseModel":
    """Get the output of the last run."""
    return pipe.model.last_run.steps["step_"]
