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
import os
from contextlib import ExitStack as does_not_raise
from unittest.mock import ANY

import pytest
from pytest_mock import MockFixture

from zenml.client import Client
from zenml.config.compiler import Compiler
from zenml.config.pipeline_configurations import PipelineRunConfiguration
from zenml.config.pipeline_deployment import PipelineDeployment
from zenml.exceptions import (
    PipelineConfigurationError,
    PipelineInterfaceError,
    StackValidationError,
)
from zenml.pipelines import BasePipeline, pipeline
from zenml.steps import BaseParameters, step
from zenml.utils.yaml_utils import write_yaml


def create_pipeline_with_param_value(param_value: int):
    """Creates pipeline instance with a step named 'step' which has a parameter named 'value'."""

    class Params(BaseParameters):
        value: int

    @step
    def step_with_params(params: Params) -> None:
        pass

    @pipeline
    def some_pipeline(step_):
        step_()

    pipeline_instance = some_pipeline(
        step_=step_with_params(params=Params(value=param_value))
    )
    return pipeline_instance


def test_initialize_pipeline_with_args(
    unconnected_two_step_pipeline, generate_empty_steps
):
    """Test that a pipeline can be initialized with args."""
    with does_not_raise():
        empty_step_1, empty_step_2 = generate_empty_steps(2)
        unconnected_two_step_pipeline(empty_step_1(), empty_step_2())


def test_initialize_pipeline_with_kwargs(
    unconnected_two_step_pipeline, generate_empty_steps
):
    """Test that a pipeline can be initialized with kwargs."""
    with does_not_raise():
        empty_step_1, empty_step_2 = generate_empty_steps(2)
        unconnected_two_step_pipeline(
            step_1=empty_step_1(), step_2=empty_step_2()
        )


def test_initialize_pipeline_with_args_and_kwargs(
    unconnected_two_step_pipeline, generate_empty_steps
):
    """Test that a pipeline can be initialized with a mix of args and kwargs."""
    with does_not_raise():
        empty_step_1, empty_step_2 = generate_empty_steps(2)
        unconnected_two_step_pipeline(empty_step_1(), step_2=empty_step_2())


def test_initialize_pipeline_with_too_many_args(
    unconnected_two_step_pipeline, generate_empty_steps
):
    """Test that pipeline initialization fails when too many args are passed."""
    with pytest.raises(PipelineInterfaceError):
        empty_step_1, empty_step_2, empty_step_3 = generate_empty_steps(3)
        unconnected_two_step_pipeline(
            empty_step_1(), empty_step_2(), empty_step_3()
        )


def test_initialize_pipeline_with_too_many_args_and_kwargs(
    unconnected_two_step_pipeline, generate_empty_steps
):
    """Test that pipeline initialization fails when too many args and kwargs are passed."""
    with pytest.raises(PipelineInterfaceError):
        empty_step_1, empty_step_2, empty_step_3 = generate_empty_steps(3)
        unconnected_two_step_pipeline(
            empty_step_3(), step_1=empty_step_1(), step_2=empty_step_2()
        )


def test_initialize_pipeline_with_missing_key(
    unconnected_two_step_pipeline, empty_step
):
    """Test that pipeline initialization fails when an argument is missing."""
    with pytest.raises(PipelineInterfaceError):
        unconnected_two_step_pipeline(step_1=empty_step())


def test_initialize_pipeline_with_unexpected_key(
    unconnected_two_step_pipeline, generate_empty_steps
):
    """Test that pipeline initialization fails when an argument has an unexpected key."""
    with pytest.raises(PipelineInterfaceError):
        empty_step_1, empty_step_2, empty_step_3 = generate_empty_steps(3)
        unconnected_two_step_pipeline(
            step_1=empty_step_1(), step_2=empty_step_2(), step_3=empty_step_3()
        )


def test_initialize_pipeline_with_repeated_args(
    unconnected_two_step_pipeline, empty_step
):
    """Test that pipeline initialization fails when same step object is used."""
    step_instance = empty_step()
    with pytest.raises(PipelineInterfaceError):
        unconnected_two_step_pipeline(step_instance, step_instance)


def test_initialize_pipeline_with_repeated_kwargs(
    unconnected_two_step_pipeline, empty_step
):
    """Test that pipeline initialization fails when same step object is used."""
    step_instance = empty_step()
    with pytest.raises(PipelineInterfaceError):
        unconnected_two_step_pipeline(
            step_1=step_instance, step_2=step_instance
        )


def test_initialize_pipeline_with_repeated_args_and_kwargs(
    unconnected_two_step_pipeline, empty_step
):
    """Test that pipeline initialization fails when same step object is used."""
    step_instance = empty_step()
    with pytest.raises(PipelineInterfaceError):
        unconnected_two_step_pipeline(step_instance, step_2=step_instance)


def test_initialize_pipeline_with_wrong_arg_type(
    unconnected_two_step_pipeline, empty_step
):
    """Test that pipeline initialization fails when an arg has a wrong type."""
    with pytest.raises(PipelineInterfaceError):
        unconnected_two_step_pipeline(1, empty_step())


def test_initialize_pipeline_with_wrong_kwarg_type(
    unconnected_two_step_pipeline, empty_step
):
    """Test that pipeline initialization fails when a kwarg has a wrong type."""
    with pytest.raises(PipelineInterfaceError):
        unconnected_two_step_pipeline(step_1=1, step_2=empty_step())


def test_initialize_pipeline_with_missing_arg_step_brackets(
    unconnected_two_step_pipeline, generate_empty_steps
):
    """Test that pipeline initialization fails with missing arg brackets."""
    with pytest.raises(PipelineInterfaceError):
        empty_step_1, empty_step_2 = generate_empty_steps(2)
        unconnected_two_step_pipeline(empty_step_1, empty_step_2)


def test_initialize_pipeline_with_missing_kwarg_step_brackets(
    unconnected_two_step_pipeline, generate_empty_steps
):
    """Test that pipeline initialization fails with missing kwarg brackets."""
    with pytest.raises(PipelineInterfaceError):
        empty_step_1, empty_step_2 = generate_empty_steps(2)
        unconnected_two_step_pipeline(step_1=empty_step_1, step_2=empty_step_2)


def test_setting_step_parameter_with_config_object():
    """Test whether step parameters can be set using a config object."""
    config_value = 0
    pipeline_instance = create_pipeline_with_param_value(config_value)
    step_instance = pipeline_instance.steps["step_"]

    assert step_instance.configuration.parameters["value"] == config_value


def test_overwrite_step_parameter_with_config_yaml(tmp_path):
    """Test whether step parameters can be overwritten using a config yaml."""
    config_value = 0
    pipeline_instance = create_pipeline_with_param_value(config_value)

    yaml_path = os.path.join(tmp_path, "config.yaml")
    yaml_config_value = 1
    write_yaml(
        yaml_path,
        {"steps": {"step_": {"parameters": {"value": yaml_config_value}}}},
    )
    pipeline_instance = pipeline_instance.with_config(
        yaml_path, overwrite_step_parameters=True
    )
    step_instance = pipeline_instance.steps["step_"]
    assert step_instance.configuration.parameters["value"] == yaml_config_value


def test_dont_overwrite_step_parameter_with_config_yaml(tmp_path):
    """Test that step parameters don't get overwritten by yaml file if not forced."""
    config_value = 0
    pipeline_instance = create_pipeline_with_param_value(config_value)

    yaml_path = os.path.join(tmp_path, "config.yaml")
    yaml_config_value = 1
    write_yaml(
        yaml_path,
        {"steps": {"step_": {"parameters": {"value": yaml_config_value}}}},
    )
    pipeline_instance = pipeline_instance.with_config(yaml_path)
    step_instance = pipeline_instance.steps["step_"]
    assert step_instance.configuration.parameters["value"] == config_value


def test_yaml_configuration_with_invalid_step_name(tmp_path):
    """Test that a config yaml with an invalid step name raises an exception."""
    pipeline_instance = create_pipeline_with_param_value(0)

    yaml_path = os.path.join(tmp_path, "config.yaml")
    write_yaml(
        yaml_path,
        {"steps": {"WRONG_STEP_NAME": {"parameters": {"value": 0}}}},
    )
    with pytest.raises(PipelineConfigurationError):
        _ = pipeline_instance.with_config(yaml_path)


def test_yaml_configuration_allows_enabling_cache(tmp_path):
    """Test that a config yaml allows you to disable the cache for a step."""
    pipeline_instance = create_pipeline_with_param_value(13)

    yaml_path = os.path.join(tmp_path, "config.yaml")
    cache_value = False
    write_yaml(
        yaml_path,
        {"steps": {"step_": {"parameters": {"enable_cache": cache_value}}}},
    )
    pipeline_instance = pipeline_instance.with_config(yaml_path)
    step_instance = pipeline_instance.steps["step_"]
    assert step_instance.enable_cache == cache_value


def test_setting_pipeline_parameter_name_when_initializing_pipeline(
    one_step_pipeline, empty_step
):
    """Tests that initializing a pipeline with a step sets the attribute `pipeline_parameter_name` of the step."""
    step_instance = empty_step()
    assert step_instance.pipeline_parameter_name is None
    one_step_pipeline(step_instance)
    assert step_instance.pipeline_parameter_name == "step_"


def test_calling_a_pipeline_twice_raises_no_exception(
    one_step_pipeline, empty_step
):
    """Tests that calling one pipeline instance twice does not raise any exception."""
    pipeline_instance = one_step_pipeline(empty_step())

    with does_not_raise():
        pipeline_instance.run(unlisted=True)
        pipeline_instance.run(unlisted=True)


def test_pipeline_run_fails_when_required_step_operator_is_missing(
    one_step_pipeline,
):
    """Tests that running a pipeline with a step that requires a custom step operator fails if the active stack does not contain this step operator."""

    @step(step_operator="azureml")
    def step_that_requires_step_operator() -> None:
        pass

    assert not Client().active_stack.step_operator
    with pytest.raises(StackValidationError):
        one_step_pipeline(step_that_requires_step_operator()).run(
            unlisted=True
        )


def test_pipeline_decorator_configuration_gets_applied_during_initialization(
    mocker,
):
    """Tests that the configuration passed to the pipeline decorator gets
    applied when creating an instance of the pipeline."""
    config = {
        "extra": {"key": "value"},
        "settings": {"docker": {"target_repository": "custom_repo"}},
    }

    @pipeline(**config)
    def p():
        pass

    mock_configure = mocker.patch.object(BasePipeline, "configure")
    p()
    mock_configure.assert_called_with(**config)


def test_pipeline_configuration(empty_pipeline):
    """Tests the pipeline configuration and overwriting/merging with existing
    configurations."""
    pipeline_instance = empty_pipeline()

    pipeline_instance.configure(
        enable_cache=False,
        extra={"key": "value"},
    )

    assert pipeline_instance.configuration.enable_cache is False
    assert pipeline_instance.configuration.extra == {"key": "value"}

    # No merging
    pipeline_instance.configure(
        enable_cache=True,
        extra={"key2": "value2"},
        merge=False,
    )
    assert pipeline_instance.configuration.enable_cache is True
    assert pipeline_instance.configuration.extra == {"key2": "value2"}

    # With merging
    pipeline_instance.configure(
        enable_cache=False,
        extra={"key3": "value3"},
        merge=True,
    )
    assert pipeline_instance.configuration.enable_cache is False
    assert pipeline_instance.configuration.extra == {
        "key2": "value2",
        "key3": "value3",
    }


def test_configure_pipeline_with_invalid_settings_key(empty_pipeline):
    """Tests that configuring a pipeline with an invalid settings key raises an
    error."""
    with pytest.raises(ValueError):
        empty_pipeline().configure(settings={"invalid_settings_key": {}})


def test_run_configuration_in_code(
    mocker, clean_project, one_step_pipeline, empty_step
):
    """Tests configuring a pipeline run in code."""
    mock_compile = mocker.patch.object(
        Compiler, "compile", wraps=Compiler().compile
    )
    pipeline_instance = one_step_pipeline(empty_step())

    pipeline_instance.run(
        run_name="run_name", enable_cache=False, extra={"key": "value"}
    )

    expected_run_config = PipelineRunConfiguration(
        run_name="run_name", enable_cache=False, extra={"key": "value"}
    )
    mock_compile.assert_called_once_with(
        pipeline=ANY, stack=ANY, run_configuration=expected_run_config
    )


def test_run_configuration_from_file(
    mocker, clean_project, one_step_pipeline, empty_step, tmp_path
):
    """Tests configuring a pipeline run from a file."""
    mock_compile = mocker.patch.object(
        Compiler, "compile", wraps=Compiler().compile
    )
    pipeline_instance = one_step_pipeline(empty_step())

    config_path = tmp_path / "config.yaml"
    expected_run_config = PipelineRunConfiguration(
        run_name="run_name", enable_cache=False, extra={"key": "value"}
    )
    config_path.write_text(expected_run_config.yaml())

    pipeline_instance.run(config_path=str(config_path))
    mock_compile.assert_called_once_with(
        pipeline=ANY, stack=ANY, run_configuration=expected_run_config
    )


def test_run_configuration_from_code_and_file(
    mocker, clean_project, one_step_pipeline, empty_step, tmp_path
):
    """Tests merging the configuration of a pipeline run from a file and within
    code."""
    mock_compile = mocker.patch.object(
        Compiler, "compile", wraps=Compiler().compile
    )
    pipeline_instance = one_step_pipeline(empty_step())

    config_path = tmp_path / "config.yaml"
    file_config = PipelineRunConfiguration(
        run_name="run_name_in_file", enable_cache=False, extra={"key": "value"}
    )
    config_path.write_text(file_config.yaml())

    pipeline_instance.run(
        config_path=str(config_path),
        run_name="run_name_in_code",
        extra={"new_key": "new_value"},
    )

    expected_run_config = PipelineRunConfiguration(
        run_name="run_name_in_code",
        enable_cache=False,
        extra={"key": "value", "new_key": "new_value"},
    )
    mock_compile.assert_called_once_with(
        pipeline=ANY, stack=ANY, run_configuration=expected_run_config
    )


@step(enable_cache=True)
def step_with_cache_enabled() -> None:
    pass


@step(enable_cache=False)
def step_with_cache_disabled() -> None:
    pass


@pipeline(enable_cache=True)
def pipeline_with_cache_enabled(step_1, step_2) -> None:
    step_1()
    step_2()


@pipeline(enable_cache=False)
def pipeline_with_cache_disabled(
    step_1,
    step_2,
) -> None:
    step_1()
    step_2()


def test_setting_enable_cache_at_run_level_overrides_all_decorator_values(
    mocker: MockFixture,
):
    """Test that `pipeline.run(enable_cache=...)` overrides decorator values."""

    def assert_cache_enabled(pipeline_deployment: PipelineDeployment):
        assert pipeline_deployment.pipeline.enable_cache is True
        for step_ in pipeline_deployment.steps.values():
            assert step_.config.enable_cache is True

    def assert_cache_disabled(pipeline_deployment: PipelineDeployment):
        assert pipeline_deployment.pipeline.enable_cache is False
        for step_ in pipeline_deployment.steps.values():
            assert step_.config.enable_cache is False

    cache_enabled_mock = mocker.MagicMock(side_effect=assert_cache_enabled)
    cache_disabled_mock = mocker.MagicMock(side_effect=assert_cache_disabled)

    # Test that `enable_cache=True` overrides all decorator values
    mocker.patch(
        "zenml.stack.stack.Stack.deploy_pipeline", new=cache_enabled_mock
    )
    pipeline_instance = pipeline_with_cache_disabled(
        step_1=step_with_cache_enabled(),
        step_2=step_with_cache_disabled(),
    )
    pipeline_instance.run(unlisted=True, enable_cache=True)
    assert cache_enabled_mock.call_count == 1

    # Test that `enable_cache=False` overrides all decorator values
    mocker.patch(
        "zenml.stack.stack.Stack.deploy_pipeline", new=cache_disabled_mock
    )
    pipeline_instance = pipeline_with_cache_enabled(
        step_1=step_with_cache_enabled(),
        step_2=step_with_cache_disabled(),
    )
    pipeline_instance.run(unlisted=True, enable_cache=False)
    assert cache_disabled_mock.call_count == 1
