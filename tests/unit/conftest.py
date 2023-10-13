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
from datetime import datetime
from typing import Any, Callable, Dict, Generator, Optional
from uuid import uuid4

import pytest

from tests.harness.utils import clean_workspace_session
from zenml.artifact_stores.local_artifact_store import (
    LocalArtifactStore,
    LocalArtifactStoreConfig,
)
from zenml.client import Client
from zenml.config.pipeline_configurations import PipelineConfiguration
from zenml.config.pipeline_spec import PipelineSpec
from zenml.config.step_configurations import StepConfiguration, StepSpec
from zenml.config.step_run_info import StepRunInfo
from zenml.container_registries.base_container_registry import (
    BaseContainerRegistry,
    BaseContainerRegistryConfig,
)
from zenml.enums import ArtifactType, ExecutionStatus
from zenml.materializers.base_materializer import BaseMaterializer
from zenml.models import (
    ArtifactResponseModel,
    CodeRepositoryResponseModel,
    PipelineBuildResponseModel,
    PipelineDeploymentRequestModel,
    PipelineDeploymentResponseModel,
    PipelineResponseModel,
    PipelineRunResponseModel,
    StepRunResponseModel,
    UserResponseModel,
    WorkspaceResponseModel,
)
from zenml.models.artifact_models import ArtifactRequestModel
from zenml.models.hub_plugin_models import HubPluginResponseModel, PluginStatus
from zenml.models.pipeline_run_models import PipelineRunRequestModel
from zenml.models.step_run_models import StepRunRequestModel
from zenml.new.pipelines.pipeline import Pipeline
from zenml.orchestrators.base_orchestrator import BaseOrchestratorConfig
from zenml.orchestrators.local.local_orchestrator import LocalOrchestrator
from zenml.pipelines import pipeline
from zenml.stack.stack import Stack
from zenml.stack.stack_component import (
    StackComponentConfig,
    StackComponentType,
)
from zenml.step_operators import BaseStepOperator, BaseStepOperatorConfig
from zenml.steps import StepContext, step
from zenml.steps.entrypoint_function_utils import StepArtifact


@pytest.fixture(scope="module", autouse=True)
def module_auto_clean_workspace(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[Client, None, None]:
    """Fixture to automatically create, activate and use a separate ZenML
    workspace for an entire test module.

    Yields:
        A ZenML client configured to use the workspace.
    """
    with clean_workspace_session(
        tmp_path_factory=tmp_path_factory,
        clean_repo=True,
    ) as client:
        yield client


@pytest.fixture
def local_stack():
    """Returns a local stack with local orchestrator and artifact store."""
    orchestrator = LocalOrchestrator(
        name="",
        id=uuid4(),
        config=StackComponentConfig(),
        flavor="default",
        type=StackComponentType.ORCHESTRATOR,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )
    artifact_store = LocalArtifactStore(
        name="",
        id=uuid4(),
        config=LocalArtifactStoreConfig(),
        flavor="default",
        type=StackComponentType.ARTIFACT_STORE,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )
    return Stack(
        id=uuid4(),
        name="",
        orchestrator=orchestrator,
        artifact_store=artifact_store,
    )


@pytest.fixture
def local_orchestrator():
    """Returns a local orchestrator."""
    return LocalOrchestrator(
        name="",
        id=uuid4(),
        config=BaseOrchestratorConfig(),
        flavor="local",
        type=StackComponentType.ORCHESTRATOR,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def local_artifact_store():
    """Fixture that creates a local artifact store for testing."""
    return LocalArtifactStore(
        name="",
        id=uuid4(),
        config=LocalArtifactStoreConfig(),
        flavor="local",
        type=StackComponentType.ARTIFACT_STORE,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def gcp_artifact_store():
    """Fixture that creates a GCP artifact store for testing."""
    from zenml.integrations.gcp.artifact_stores.gcp_artifact_store import (
        GCPArtifactStore,
    )
    from zenml.integrations.gcp.flavors.gcp_artifact_store_flavor import (
        GCPArtifactStoreConfig,
    )

    return GCPArtifactStore(
        name="",
        id=uuid4(),
        config=GCPArtifactStoreConfig(path="gs://bucket"),
        flavor="gcp",
        type=StackComponentType.ARTIFACT_STORE,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def s3_artifact_store():
    """Fixture that creates an S3 artifact store for testing."""
    from zenml.integrations.s3.artifact_stores.s3_artifact_store import (
        S3ArtifactStore,
    )
    from zenml.integrations.s3.flavors.s3_artifact_store_flavor import (
        S3ArtifactStoreConfig,
    )

    return S3ArtifactStore(
        name="",
        id=uuid4(),
        config=S3ArtifactStoreConfig(path="s3://tmp"),
        flavor="s3",
        type=StackComponentType.ARTIFACT_STORE,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def local_container_registry():
    """Fixture that creates a local container registry for testing."""
    return BaseContainerRegistry(
        name="",
        id=uuid4(),
        config=BaseContainerRegistryConfig(uri="localhost:5000"),
        flavor="default",
        type=StackComponentType.CONTAINER_REGISTRY,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def remote_container_registry():
    """Fixture that creates a remote container registry for testing."""
    return BaseContainerRegistry(
        name="",
        id=uuid4(),
        config=BaseContainerRegistryConfig(uri="gcr.io/my-project"),
        flavor="gcp",
        type=StackComponentType.CONTAINER_REGISTRY,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def sample_step_operator() -> BaseStepOperator:
    """Fixture that creates a stub step operator for testing."""

    class StubStepOperator(BaseStepOperator):
        def launch(self, info, entrypoint_command) -> None:
            pass

    return StubStepOperator(
        name="",
        id=uuid4(),
        config=BaseStepOperatorConfig(),
        flavor="stub",
        type=StackComponentType.STEP_OPERATOR,
        user=uuid4(),
        workspace=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
    )


@step
def _empty_step() -> None:
    """Empty step for testing."""


@pytest.fixture
def empty_step():
    """Pytest fixture that returns an empty (no input, no output) step."""
    return _empty_step


@pytest.fixture
def generate_empty_steps():
    """Pytest fixture that returns a function that generates multiple empty steps."""

    def _generate_empty_steps(count: int):
        output = []

        for i in range(count):

            @step(name=f"step_{i}")
            def _step_function() -> None:
                pass

            output.append(_step_function)

        return output

    return _generate_empty_steps


@pytest.fixture
def one_step_pipeline():
    """Pytest fixture that returns a pipeline which takes a single step named `step_`."""

    @pipeline
    def _pipeline(step_):
        step_()

    return _pipeline


@pytest.fixture
def unconnected_two_step_pipeline():
    """Pytest fixture that returns a pipeline which takes two steps `step_1` and `step_2`. The steps are not connected to each other."""

    @pipeline
    def _pipeline(step_1, step_2):
        step_1()
        step_2()

    return _pipeline


@step
def _int_output_step() -> int:
    return 1


@pytest.fixture
def int_step_output():
    return StepArtifact(
        invocation_id="id",
        output_name="output_name",
        annotation=int,
        pipeline=Pipeline(name="test_pipeline", entrypoint=lambda: None),
    )


@pytest.fixture
def step_with_two_int_inputs():
    @step
    def _step(input_1: int, input_2: int) -> None:
        pass

    return _step


@pytest.fixture
def sample_step_run_info(
    sample_pipeline_run: PipelineRunResponseModel,
    sample_step_run: StepRunResponseModel,
) -> StepRunInfo:
    step_run_info = StepRunInfo(
        step_run_id=sample_step_run.id,
        run_id=sample_pipeline_run.id,
        run_name=sample_pipeline_run.name,
        pipeline_step_name=sample_step_run.name,
        config=sample_step_run.config,
        pipeline=sample_pipeline_run.config,
    )
    return step_run_info


@pytest.fixture
def step_context_with_no_output(
    sample_pipeline_run: PipelineRunResponseModel,
    sample_step_run: StepRunResponseModel,
    sample_step_run_info: StepRunInfo,
) -> StepContext:
    StepContext._clear()
    return StepContext(
        pipeline_run=sample_pipeline_run,
        step_run=sample_step_run,
        step_run_info=sample_step_run_info,
        cache_enabled=True,
        output_materializers={},
        output_artifact_uris={},
        output_artifact_configs={},
    )


@pytest.fixture
def step_context_with_single_output(
    sample_pipeline_run: PipelineRunResponseModel,
    sample_step_run: StepRunResponseModel,
    sample_step_run_info: StepRunInfo,
) -> StepContext:
    materializers = {"output_1": (BaseMaterializer,)}
    artifact_uris = {"output_1": ""}
    artifact_configs = {"output_1": None}
    StepContext._clear()
    return StepContext(
        pipeline_run=sample_pipeline_run,
        step_run=sample_step_run,
        step_run_info=sample_step_run_info,
        cache_enabled=True,
        output_materializers=materializers,
        output_artifact_uris=artifact_uris,
        output_artifact_configs=artifact_configs,
    )


@pytest.fixture
def step_context_with_two_outputs(
    sample_pipeline_run: PipelineRunResponseModel,
    sample_step_run: StepRunResponseModel,
    sample_step_run_info: StepRunInfo,
) -> StepContext:
    materializers = {
        "output_1": (BaseMaterializer,),
        "output_2": (BaseMaterializer,),
    }
    artifact_uris = {
        "output_1": "",
        "output_2": "",
    }
    artifact_configs = {"output_1": None, "output_2": None}

    StepContext._clear()
    return StepContext(
        pipeline_run=sample_pipeline_run,
        step_run=sample_step_run,
        step_run_info=sample_step_run_info,
        cache_enabled=True,
        output_materializers=materializers,
        output_artifact_uris=artifact_uris,
        output_artifact_configs=artifact_configs,
    )


@pytest.fixture
def sample_user_model() -> UserResponseModel:
    """Return a sample user model for testing purposes."""
    return UserResponseModel(
        id=uuid4(),
        name="axl",
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def sample_workspace_model() -> WorkspaceResponseModel:
    """Return a sample workspace model for testing purposes."""
    return WorkspaceResponseModel(
        id=uuid4(),
        name="axl",
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def sample_step_request_model() -> StepRunRequestModel:
    """Return a sample step model for testing purposes."""
    spec = StepSpec.parse_obj(
        {
            "source": "module.step_class",
            "upstream_steps": [],
            "inputs": {},
        }
    )
    config = StepConfiguration.parse_obj(
        {"name": "step_name", "enable_cache": True}
    )

    return StepRunRequestModel(
        name="sample_step",
        pipeline_run_id=uuid4(),
        status=ExecutionStatus.COMPLETED,
        spec=spec,
        config=config,
        workspace=uuid4(),
        user=uuid4(),
        deployment=uuid4(),
    )


@pytest.fixture
def sample_step_run(create_step_run) -> StepRunResponseModel:
    """Return a sample step response model for testing purposes."""
    return create_step_run()


@pytest.fixture
def sample_pipeline_run(
    sample_user_model: UserResponseModel,
    sample_workspace_model: WorkspaceResponseModel,
) -> PipelineRunResponseModel:
    """Return sample pipeline run view for testing purposes."""
    return PipelineRunResponseModel(
        id=uuid4(),
        name="sample_run_name",
        config=PipelineConfiguration(name="aria_pipeline"),
        num_steps=1,
        status=ExecutionStatus.COMPLETED,
        created=datetime.now(),
        updated=datetime.now(),
        user=sample_user_model,
        workspace=sample_workspace_model,
    )


@pytest.fixture
def sample_pipeline_deployment_request_model() -> (
    PipelineDeploymentRequestModel
):
    """Return sample pipeline deployment request for testing purposes."""
    return PipelineDeploymentRequestModel(
        user=uuid4(),
        workspace=uuid4(),
        run_name_template="aria-blupus",
        pipeline_configuration=PipelineConfiguration(name="axls-pipeline"),
        client_version="0.12.3",
        server_version="0.12.3",
        stack=uuid4(),
    )


@pytest.fixture
def sample_pipeline_run_request_model() -> PipelineRunRequestModel:
    """Return sample pipeline run view for testing purposes."""
    return PipelineRunRequestModel(
        id=uuid4(),
        name="sample_run_name",
        config=PipelineConfiguration(name="aria_pipeline"),
        num_steps=1,
        status=ExecutionStatus.COMPLETED,
        user=uuid4(),
        workspace=uuid4(),
        deployment=uuid4(),
        pipeline=uuid4(),
    )


@pytest.fixture
def sample_artifact_model(
    sample_workspace_model, sample_user_model
) -> ArtifactResponseModel:
    """Return a sample artifact model for testing purposes."""
    return ArtifactResponseModel(
        id=uuid4(),
        name="sample_artifact",
        uri="sample_uri",
        type=ArtifactType.DATA,
        materializer="sample_module.sample_materializer",
        data_type="sample_module.sample_data_type",
        parent_step_id=uuid4(),
        producer_step_id=uuid4(),
        is_cached=False,
        created=datetime.now(),
        updated=datetime.now(),
        workspace=sample_workspace_model,
        user=sample_user_model,
    )


@pytest.fixture
def sample_artifact_request_model() -> ArtifactRequestModel:
    """Return a sample artifact model for testing purposes."""
    return ArtifactRequestModel(
        name="sample_artifact",
        uri="sample_uri",
        type=ArtifactType.DATA,
        materializer="sample_materializer",
        data_type="sample_data_type",
        parent_step_id=uuid4(),
        producer_step_id=uuid4(),
        is_cached=False,
        workspace=uuid4(),
        user=uuid4(),
    )


@pytest.fixture
def create_step_run(
    sample_user_model: UserResponseModel,
    sample_workspace_model: WorkspaceResponseModel,
) -> Callable[..., StepRunResponseModel]:
    """Fixture that returns a function which can be used to create a
    customizable StepRunResponseModel."""

    def f(
        step_run_name: str = "step_run_name",
        step_name: str = "step_name",
        outputs: Optional[Dict[str, Any]] = None,
        output_artifacts: Optional[Dict[str, ArtifactResponseModel]] = None,
        **kwargs: Any,
    ) -> StepRunResponseModel:
        spec = StepSpec.parse_obj(
            {"source": "module.step_class", "upstream_steps": []}
        )
        config = StepConfiguration.parse_obj(
            {
                "name": step_name,
                "outputs": outputs or {},
            }
        )
        return StepRunResponseModel(
            id=uuid4(),
            name=step_run_name,
            pipeline_run_id=uuid4(),
            deployment_id=uuid4(),
            spec=spec,
            config=config,
            status=ExecutionStatus.COMPLETED,
            created=datetime.now(),
            updated=datetime.now(),
            workspace=sample_workspace_model,
            user=sample_user_model,
            outputs=output_artifacts or {},
            **kwargs,
        )

    return f


@pytest.fixture
def create_pipeline_model(
    sample_user_model: UserResponseModel,
    sample_workspace_model: WorkspaceResponseModel,
) -> Callable[..., PipelineResponseModel]:
    """Fixture that returns a function which can be used to create a
    customizable PipelineResponseModel."""

    def f(
        **kwargs: Any,
    ) -> PipelineResponseModel:
        model_args = {
            "id": uuid4(),
            "name": "sample_pipeline",
            "version": 1,
            "version_hash": "",
            "created": datetime.now(),
            "updated": datetime.now(),
            "workspace": sample_workspace_model,
            "user": sample_user_model,
            "spec": PipelineSpec(steps=[]),
            **kwargs,
        }
        return PipelineResponseModel(**model_args)

    return f


@pytest.fixture
def sample_deployment_response_model(
    sample_user_model: UserResponseModel,
    sample_workspace_model: WorkspaceResponseModel,
) -> PipelineDeploymentResponseModel:
    return PipelineDeploymentResponseModel(
        id=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
        user=sample_user_model,
        workspace=sample_workspace_model,
        run_name_template="",
        pipeline_configuration={"name": ""},
        client_version="0.12.3",
        server_version="0.12.3",
    )


@pytest.fixture
def sample_build_response_model(
    sample_user_model: UserResponseModel,
    sample_workspace_model: WorkspaceResponseModel,
) -> PipelineBuildResponseModel:
    return PipelineBuildResponseModel(
        id=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
        user=sample_user_model,
        workspace=sample_workspace_model,
        images={},
        is_local=False,
        contains_code=True,
    )


@pytest.fixture
def sample_code_repo_response_model(
    sample_user_model: UserResponseModel,
    sample_workspace_model: WorkspaceResponseModel,
) -> CodeRepositoryResponseModel:
    return CodeRepositoryResponseModel(
        id=uuid4(),
        created=datetime.now(),
        updated=datetime.now(),
        user=sample_user_model,
        workspace=sample_workspace_model,
        name="name",
        config={},
        source={"module": "zenml", "type": "internal"},
    )


@pytest.fixture
def sample_hub_plugin_response_model() -> HubPluginResponseModel:
    return HubPluginResponseModel(
        id=uuid4(),
        author="AlexejPenner",
        name="alexejs_ploogin",
        version="3.14",
        repository_url="https://github.com/zenml-io/zenml",
        index_url="https://test.pypi.org/simple/",
        package_name="ploogin",
        status=PluginStatus.AVAILABLE,
        created=datetime.now(),
        updated=datetime.now(),
        requirements=["ploogin==0.0.1", "zenml>=0.1.0"],
    )
