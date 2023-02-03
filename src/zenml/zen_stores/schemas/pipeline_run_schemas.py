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
"""SQLModel implementation of pipeline run tables."""

import json
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import TEXT, Column
from sqlmodel import Field, Relationship

from zenml.enums import ExecutionStatus
from zenml.models import PipelineRunResponseModel
from zenml.models.pipeline_run_models import PipelineRunRequestModel
from zenml.zen_stores.schemas.base_schemas import NamedSchema
from zenml.zen_stores.schemas.pipeline_schemas import PipelineSchema
from zenml.zen_stores.schemas.project_schemas import ProjectSchema
from zenml.zen_stores.schemas.schedule_schema import ScheduleSchema
from zenml.zen_stores.schemas.schema_utils import build_foreign_key_field
from zenml.zen_stores.schemas.stack_schemas import StackSchema
from zenml.zen_stores.schemas.user_schemas import UserSchema

if TYPE_CHECKING:
    from zenml.models import PipelineRunUpdateModel
    from zenml.zen_stores.schemas.step_run_schemas import StepRunSchema


class PipelineRunSchema(NamedSchema, table=True):
    """SQL Model for pipeline runs."""

    __tablename__ = "pipeline_run"

    stack_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=StackSchema.__tablename__,
        source_column="stack_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    stack: "StackSchema" = Relationship(back_populates="runs")

    pipeline_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=PipelineSchema.__tablename__,
        source_column="pipeline_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    pipeline: "PipelineSchema" = Relationship(back_populates="runs")

    schedule_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=ScheduleSchema.__tablename__,
        source_column="schedule_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    schedule: ScheduleSchema = Relationship(back_populates="runs")

    user_id: Optional[UUID] = build_foreign_key_field(
        source=__tablename__,
        target=UserSchema.__tablename__,
        source_column="user_id",
        target_column="id",
        ondelete="SET NULL",
        nullable=True,
    )
    user: Optional["UserSchema"] = Relationship(back_populates="runs")

    project_id: UUID = build_foreign_key_field(
        source=__tablename__,
        target=ProjectSchema.__tablename__,
        source_column="project_id",
        target_column="id",
        ondelete="CASCADE",
        nullable=False,
    )
    project: "ProjectSchema" = Relationship(back_populates="runs")

    orchestrator_run_id: Optional[str] = Field(nullable=True)

    enable_cache: Optional[bool] = Field(nullable=True)
    start_time: Optional[datetime] = Field(nullable=True)
    end_time: Optional[datetime] = Field(nullable=True)
    status: ExecutionStatus
    pipeline_configuration: str = Field(sa_column=Column(TEXT, nullable=False))
    num_steps: Optional[int]
    zenml_version: str
    client_environment: Optional[str] = Field(
        sa_column=Column(TEXT, nullable=True)
    )
    orchestrator_environment: Optional[str] = Field(
        sa_column=Column(TEXT, nullable=True)
    )
    git_sha: Optional[str] = Field(nullable=True)

    step_runs: List["StepRunSchema"] = Relationship(
        back_populates="pipeline_run",
        sa_relationship_kwargs={"cascade": "delete"},
    )

    @classmethod
    def from_request(
        cls, request: PipelineRunRequestModel
    ) -> "PipelineRunSchema":
        """Convert a `PipelineRunRequestModel` to a `PipelineRunSchema`.

        Args:
            request: The request to convert.

        Returns:
            The created `PipelineRunSchema`.
        """
        configuration = json.dumps(request.pipeline_configuration)
        client_environment = json.dumps(request.client_environment)
        orchestrator_environment = json.dumps(request.orchestrator_environment)

        return cls(
            id=request.id,
            name=request.name,
            orchestrator_run_id=request.orchestrator_run_id,
            stack_id=request.stack,
            project_id=request.project,
            user_id=request.user,
            pipeline_id=request.pipeline,
            schedule_id=request.schedule_id,
            enable_cache=request.enable_cache,
            start_time=request.start_time,
            status=request.status,
            pipeline_configuration=configuration,
            num_steps=request.num_steps,
            git_sha=request.git_sha,
            zenml_version=request.zenml_version,
            client_environment=client_environment,
            orchestrator_environment=orchestrator_environment,
        )

    def to_model(
        self, _block_recursion: bool = False
    ) -> PipelineRunResponseModel:
        """Convert a `PipelineRunSchema` to a `PipelineRunResponseModel`.

        Args:
            _block_recursion: If other models should be recursively filled

        Returns:
            The created `PipelineRunResponseModel`.
        """
        client_environment = (
            json.loads(self.client_environment)
            if self.client_environment
            else {}
        )
        orchestrator_environment = (
            json.loads(self.orchestrator_environment)
            if self.orchestrator_environment
            else {}
        )

        if _block_recursion:
            return PipelineRunResponseModel(
                id=self.id,
                name=self.name,
                project=self.project.to_model(),
                user=self.user.to_model(True) if self.user else None,
                schedule_id=self.schedule_id,
                orchestrator_run_id=self.orchestrator_run_id,
                enable_cache=self.enable_cache,
                start_time=self.start_time,
                end_time=self.end_time,
                status=self.status,
                pipeline_configuration=json.loads(self.pipeline_configuration),
                num_steps=self.num_steps,
                git_sha=self.git_sha,
                zenml_version=self.zenml_version,
                client_environment=client_environment,
                orchestrator_environment=orchestrator_environment,
                created=self.created,
                updated=self.updated,
            )
        else:
            return PipelineRunResponseModel(
                id=self.id,
                name=self.name,
                stack=self.stack.to_model() if self.stack else None,
                project=self.project.to_model(),
                user=self.user.to_model(True) if self.user else None,
                orchestrator_run_id=self.orchestrator_run_id,
                enable_cache=self.enable_cache,
                start_time=self.start_time,
                end_time=self.end_time,
                status=self.status,
                pipeline=(
                    self.pipeline.to_model(False) if self.pipeline else None
                ),
                schedule_id=self.schedule_id,
                pipeline_configuration=json.loads(self.pipeline_configuration),
                num_steps=self.num_steps,
                git_sha=self.git_sha,
                zenml_version=self.zenml_version,
                client_environment=client_environment,
                orchestrator_environment=orchestrator_environment,
                created=self.created,
                updated=self.updated,
            )

    def update(
        self, run_update: "PipelineRunUpdateModel"
    ) -> "PipelineRunSchema":
        """Update a `PipelineRunSchema` with a `PipelineRunUpdateModel`.

        Args:
            run_update: The `PipelineRunUpdateModel` to update with.

        Returns:
            The updated `PipelineRunSchema`.
        """
        if run_update.status:
            self.status = run_update.status
            self.end_time = run_update.end_time

        self.updated = datetime.utcnow()
        return self
