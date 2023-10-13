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
"""Test zenml pipeline CLI commands."""

from uuid import uuid4

import pytest
from click.testing import CliRunner

from zenml.cli.cli import cli
from zenml.client import Client
from zenml.config import DockerSettings
from zenml.config.build_configuration import BuildConfiguration
from zenml.config.pipeline_run_configuration import PipelineRunConfiguration
from zenml.models.pipeline_build_models import (
    PipelineBuildBaseModel,
    PipelineBuildRequestModel,
)
from zenml.pipelines import pipeline
from zenml.stack import Stack
from zenml.steps import step
from zenml.utils.pipeline_docker_image_builder import (
    PipelineDockerImageBuilder,
)


def test_pipeline_list(clean_workspace_with_run):
    """Test that zenml pipeline list does not fail."""
    runner = CliRunner()
    list_command = cli.commands["pipeline"].commands["list"]
    result = runner.invoke(list_command)
    assert result.exit_code == 0


def test_pipeline_delete(clean_workspace_with_run):
    """Test that zenml pipeline delete works as expected."""
    existing_pipelines = clean_workspace_with_run.list_pipelines()
    assert len(existing_pipelines) == 1
    pipeline_name = existing_pipelines[0].name
    runner = CliRunner()
    delete_command = cli.commands["pipeline"].commands["delete"]
    result = runner.invoke(delete_command, [pipeline_name, "-y"])
    assert result.exit_code == 0
    with pytest.raises(KeyError):
        clean_workspace_with_run.get_pipeline(name_id_or_prefix=pipeline_name)
    existing_pipelines = clean_workspace_with_run.list_pipelines()
    assert len(existing_pipelines) == 0


def test_pipeline_run_list(clean_workspace_with_run):
    """Test that zenml pipeline runs list does not fail."""
    runner = CliRunner()
    list_command = cli.commands["pipeline"].commands["runs"].commands["list"]
    result = runner.invoke(list_command)
    assert result.exit_code == 0


def test_pipeline_run_delete(clean_workspace_with_run):
    """Test that zenml pipeline runs delete works as expected."""
    existing_runs = clean_workspace_with_run.list_runs()
    assert len(existing_runs) == 1
    run_name = existing_runs[0].name
    runner = CliRunner()
    delete_command = (
        cli.commands["pipeline"].commands["runs"].commands["delete"]
    )
    result = runner.invoke(delete_command, [run_name, "-y"])
    assert result.exit_code == 0
    with pytest.raises(KeyError):
        clean_workspace_with_run.get_pipeline_run(run_name)
    existing_runs = clean_workspace_with_run.list_runs()
    assert len(existing_runs) == 0


def test_pipeline_schedule_list(clean_workspace_with_scheduled_run):
    """Test that `zenml pipeline schedules list` does not fail."""
    runner = CliRunner()
    list_command = (
        cli.commands["pipeline"].commands["schedule"].commands["list"]
    )
    result = runner.invoke(list_command)
    assert result.exit_code == 0


def test_pipeline_schedule_delete(clean_workspace_with_scheduled_run):
    """Test that `zenml pipeline schedules delete` works as expected."""
    existing_schedules = clean_workspace_with_scheduled_run.list_schedules()
    assert len(existing_schedules) == 1
    schedule_name = existing_schedules[0].name
    runner = CliRunner()
    delete_command = (
        cli.commands["pipeline"].commands["schedule"].commands["delete"]
    )
    result = runner.invoke(delete_command, [schedule_name, "-y"])
    assert result.exit_code == 0
    with pytest.raises(KeyError):
        clean_workspace_with_scheduled_run.get_schedule(schedule_name)
    existing_schedules = clean_workspace_with_scheduled_run.list_schedules()
    assert len(existing_schedules) == 0


@step
def s() -> None:
    pass


@pipeline
def p(s1):
    s1()


step_instance = s()
pipeline_instance = p(step_instance)


def test_pipeline_registration_without_repo(clean_client):
    """Tests that the register command outside of a repo works."""
    runner = CliRunner()
    register_command = cli.commands["pipeline"].commands["register"]

    result = runner.invoke(
        register_command, [f"{pipeline_instance.__module__}.pipeline_instance"]
    )
    assert result.exit_code == 0


def test_pipeline_registration_with_repo(clean_workspace):
    """Tests the register command inside a repo."""
    runner = CliRunner()
    register_command = cli.commands["pipeline"].commands["register"]

    # Invalid source string
    result = runner.invoke(register_command, ["INVALID_SOURCE"])
    assert result.exit_code == 1

    # Invalid module
    result = runner.invoke(
        register_command, ["invalid_module.pipeline_instance"]
    )
    assert result.exit_code == 1

    # Not a pipeline instance
    result = runner.invoke(
        register_command, [f"{pipeline_instance.__module__}.step_instace"]
    )
    assert result.exit_code == 1

    # Correct source
    result = runner.invoke(
        register_command, [f"{pipeline_instance.__module__}.pipeline_instance"]
    )
    assert result.exit_code == 0
    assert clean_workspace.list_pipelines(name="p").total == 1


def test_pipeline_build_without_repo(clean_client):
    """Tests that the build command outside of a repo works."""
    runner = CliRunner()
    build_command = cli.commands["pipeline"].commands["build"]

    pipeline_instance.register()

    result = runner.invoke(build_command, [pipeline_instance.name])
    assert result.exit_code == 0


def test_pipeline_build_with_nonexistent_name_fails(clean_workspace):
    """Tests that the build command fails if no pipeline with the given name
    exists."""
    runner = CliRunner()
    build_command = cli.commands["pipeline"].commands["build"]

    pipeline_instance.register()

    # name of unregistered pipeline
    assert (
        runner.invoke(build_command, ["not_a_registered_pipeline"]).exit_code
        == 1
    )


def test_pipeline_build_writes_output_file(clean_workspace, mocker, tmp_path):
    """Tests that the build command writes the build to the given output
    path if given."""
    build_config = BuildConfiguration(key="key", settings=DockerSettings())
    mocker.patch.object(
        Stack, "get_docker_builds", return_value=[build_config]
    )
    mocker.patch.object(
        PipelineDockerImageBuilder,
        "build_docker_image",
        return_value=("image_name", "", ""),
    )

    runner = CliRunner()
    build_command = cli.commands["pipeline"].commands["build"]

    pipeline_instance.register()

    output_path = str(tmp_path / "output.yaml")
    result = runner.invoke(
        build_command, [pipeline_instance.name, "--output", output_path]
    )
    assert result.exit_code == 0

    build_output = PipelineBuildBaseModel.from_yaml(output_path)
    assert build_output.is_local is True
    assert len(build_output.images) == 1
    assert build_output.images["key"].image == "image_name"


def test_pipeline_build_doesnt_write_output_file_if_no_build_needed(
    clean_workspace, mocker, tmp_path
):
    """Tests that the build command doesn't write to the given output path
    if no build was needed for the pipeline."""
    mocker.patch.object(Stack, "get_docker_builds", return_value=[])

    runner = CliRunner()
    build_command = cli.commands["pipeline"].commands["build"]

    pipeline_instance.register()

    output_path = tmp_path / "output.yaml"
    result = runner.invoke(
        build_command, [pipeline_instance.name, "--output", str(output_path)]
    )
    assert result.exit_code == 0
    assert not output_path.exists()


def test_pipeline_build_with_config_file(clean_workspace, mocker, tmp_path):
    """Tests that the build command works with a config file."""
    mock_get_docker_builds = mocker.patch.object(
        Stack, "get_docker_builds", return_value=[]
    )

    runner = CliRunner()
    build_command = cli.commands["pipeline"].commands["build"]

    pipeline_instance.register().id

    config_path = tmp_path / "config.yaml"
    config = PipelineRunConfiguration(
        settings={"docker": DockerSettings(parent_image="custom_parent_image")}
    )
    config_path.write_text(config.yaml())

    result = runner.invoke(
        build_command, [pipeline_instance.name, "--config", str(config_path)]
    )
    assert result.exit_code == 0

    _, call_kwargs = mock_get_docker_builds.call_args
    assert (
        call_kwargs["deployment"]
        .pipeline_configuration.settings["docker"]
        .parent_image
        == "custom_parent_image"
    )


def test_pipeline_build_with_different_stack(clean_workspace, mocker):
    """Tests that the build command works with a different stack."""
    build_config = BuildConfiguration(key="key", settings=DockerSettings())
    mocker.patch.object(
        Stack, "get_docker_builds", return_value=[build_config]
    )
    mocker.patch.object(
        PipelineDockerImageBuilder,
        "build_docker_image",
        return_value=("image_name", "", ""),
    )

    components = {
        key: components[0].id
        for key, components in Client().active_stack_model.components.items()
    }
    new_stack = Client().create_stack(name="new", components=components)

    runner = CliRunner()
    build_command = cli.commands["pipeline"].commands["build"]

    pipeline_id = pipeline_instance.register().id

    result = runner.invoke(
        build_command, [pipeline_instance.name, "--stack", str(new_stack.id)]
    )
    assert result.exit_code == 0

    builds = Client().list_builds(pipeline_id=pipeline_id)
    assert len(builds) == 1
    assert builds[0].stack.id == new_stack.id


def test_pipeline_run_without_repo(clean_client):
    """Tests that the run command outside of a repo works."""
    runner = CliRunner()
    run_command = cli.commands["pipeline"].commands["run"]

    pipeline_instance.register()

    result = runner.invoke(run_command, [pipeline_instance.name])
    assert result.exit_code == 0


def test_pipeline_run_with_nonexistent_name_fails(clean_workspace):
    """Tests that the run command fails if no pipeline with the given name
    exists."""
    runner = CliRunner()
    run_command = cli.commands["pipeline"].commands["run"]

    pipeline_instance.register()

    # name of unregistered pipeline
    assert (
        runner.invoke(run_command, ["not_a_registered_pipeline"]).exit_code
        == 1
    )


def test_pipeline_run_with_config_file(clean_workspace, tmp_path):
    """Tests that the run command works with a run config file."""
    runner = CliRunner()
    run_command = cli.commands["pipeline"].commands["run"]

    pipeline_id = pipeline_instance.register().id

    config_path = tmp_path / "config.yaml"
    run_config = PipelineRunConfiguration(run_name="custom_run_name")
    config_path.write_text(run_config.yaml())

    result = runner.invoke(
        run_command, [pipeline_instance.name, "--config", str(config_path)]
    )
    assert result.exit_code == 0

    runs = Client().list_pipeline_runs(pipeline_id=pipeline_id)
    assert len(runs) == 1
    assert runs[0].name == "custom_run_name"


def test_pipeline_run_with_different_stack(clean_workspace):
    """Tests that the run command works with a different stack."""
    runner = CliRunner()
    run_command = cli.commands["pipeline"].commands["run"]

    pipeline_id = pipeline_instance.register().id

    components = {
        key: components[0].id
        for key, components in Client().active_stack_model.components.items()
    }
    new_stack = Client().create_stack(name="new", components=components)

    result = runner.invoke(
        run_command, [pipeline_instance.name, "--stack", str(new_stack.id)]
    )
    assert result.exit_code == 0

    runs = Client().list_pipeline_runs(pipeline_id=pipeline_id)
    assert len(runs) == 1
    assert runs[0].stack.id == new_stack.id


def test_pipeline_run_with_invalid_build_id_fails(clean_workspace):
    """Tests that the run command with an invalid build id fails."""
    runner = CliRunner()
    run_command = cli.commands["pipeline"].commands["run"]

    pipeline_instance.register().id

    result = runner.invoke(
        run_command, [pipeline_instance.name, "--build", "not_a_build_id"]
    )
    assert result.exit_code == 1

    # not a registered build ID
    result = runner.invoke(
        run_command, [pipeline_instance.name, "--build", str(uuid4())]
    )
    assert result.exit_code == 1


def test_pipeline_run_with_custom_build_id(clean_workspace):
    """Tests that the run command works with a custom build id."""
    runner = CliRunner()
    run_command = cli.commands["pipeline"].commands["run"]

    pipeline_id = pipeline_instance.register().id

    request = PipelineBuildRequestModel(
        user=Client().active_user.id,
        workspace=Client().active_workspace.id,
        is_local=True,
        contains_code=True,
        images={},
    )
    build = Client().zen_store.create_build(request)

    result = runner.invoke(
        run_command, [pipeline_instance.name, "--build", str(build.id)]
    )
    assert result.exit_code == 0

    runs = Client().list_pipeline_runs(pipeline_id=pipeline_id)
    assert len(runs) == 1
    assert runs[0].build.id == build.id


def test_pipeline_run_with_custom_build_file(clean_workspace, tmp_path):
    """Tests that the run command works with a custom build file."""
    runner = CliRunner()
    run_command = cli.commands["pipeline"].commands["run"]

    pipeline_id = pipeline_instance.register().id

    build_path = tmp_path / "build.yaml"
    build = PipelineBuildBaseModel(
        is_local=True,
        contains_code=True,
        images={"my_key": {"image": "image_name"}},
    )
    build_path.write_text(build.yaml())

    result = runner.invoke(
        run_command, [pipeline_instance.name, "--build", str(build_path)]
    )
    assert result.exit_code == 0

    runs = Client().list_pipeline_runs(pipeline_id=pipeline_id)
    assert len(runs) == 1
    assert runs[0].build.images == build.images
    assert runs[0].build.is_local == build.is_local


def test_pipeline_build_list(clean_workspace):
    """Test that `zenml pipeline builds list` does not fail."""
    runner = CliRunner()
    list_command = cli.commands["pipeline"].commands["builds"].commands["list"]
    assert runner.invoke(list_command).exit_code == 0

    request = PipelineBuildRequestModel(
        user=clean_workspace.active_user.id,
        workspace=clean_workspace.active_workspace.id,
        images={},
        is_local=False,
        contains_code=True,
    )
    clean_workspace.zen_store.create_build(request)

    assert runner.invoke(list_command).exit_code == 0


def test_pipeline_build_delete(clean_workspace):
    """Test that `zenml pipeline builds delete` works as expected."""
    request = PipelineBuildRequestModel(
        user=clean_workspace.active_user.id,
        workspace=clean_workspace.active_workspace.id,
        images={},
        is_local=False,
        contains_code=True,
    )
    build_id = clean_workspace.zen_store.create_build(request).id

    runner = CliRunner()
    delete_command = (
        cli.commands["pipeline"].commands["builds"].commands["delete"]
    )
    result = runner.invoke(delete_command, [str(build_id), "-y"])
    assert result.exit_code == 0

    with pytest.raises(KeyError):
        clean_workspace.get_build(str(build_id))

    # this now fails because the build doesn't exist anymore
    assert runner.invoke(delete_command, [str(build_id), "-y"]).exit_code == 1
