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
"""ZenML Store interface."""
from abc import ABC, abstractmethod
from typing import Optional, Union
from uuid import UUID

from zenml.models import (
    ArtifactFilterModel,
    ArtifactRequestModel,
    ArtifactResponseModel,
    ComponentFilterModel,
    ComponentRequestModel,
    ComponentResponseModel,
    ComponentUpdateModel,
    FlavorFilterModel,
    FlavorRequestModel,
    FlavorResponseModel,
    PipelineFilterModel,
    PipelineRequestModel,
    PipelineResponseModel,
    PipelineRunFilterModel,
    PipelineRunRequestModel,
    PipelineRunResponseModel,
    PipelineRunUpdateModel,
    PipelineUpdateModel,
    ProjectFilterModel,
    ProjectRequestModel,
    ProjectResponseModel,
    ProjectUpdateModel,
    RoleFilterModel,
    RoleRequestModel,
    RoleResponseModel,
    RoleUpdateModel,
    ScheduleRequestModel,
    ScheduleResponseModel,
    StackFilterModel,
    StackRequestModel,
    StackResponseModel,
    StackUpdateModel,
    StepRunFilterModel,
    StepRunRequestModel,
    StepRunResponseModel,
    StepRunUpdateModel,
    TeamFilterModel,
    TeamRequestModel,
    TeamResponseModel,
    TeamRoleAssignmentFilterModel,
    TeamRoleAssignmentRequestModel,
    TeamRoleAssignmentResponseModel,
    TeamUpdateModel,
    UserAuthModel,
    UserFilterModel,
    UserRequestModel,
    UserResponseModel,
    UserRoleAssignmentFilterModel,
    UserRoleAssignmentRequestModel,
    UserRoleAssignmentResponseModel,
    UserUpdateModel,
)
from zenml.models.page_model import Page
from zenml.models.schedule_model import (
    ScheduleFilterModel,
    ScheduleUpdateModel,
)
from zenml.models.server_models import ServerModel


class ZenStoreInterface(ABC):
    """ZenML store interface.

    All ZenML stores must implement the methods in this interface.

    The methods in this interface are organized in the following way:

     * they are grouped into categories based on the type of resource
       that they operate on (e.g. stacks, stack components, etc.)

     * each category has a set of CRUD methods (create, read, update, delete)
       that operate on the resources in that category. The order of the methods
       in each category should be:

       * create methods - store a new resource. These methods
         should fill in generated fields (e.g. UUIDs, creation timestamps) in
         the resource and return the updated resource.
       * get methods - retrieve a single existing resource identified by a
         unique key or identifier from the store. These methods should always
         return a resource and raise an exception if the resource does not
         exist.
       * list methods - retrieve a list of resources from the store. These
         methods should accept a set of filter parameters that can be used to
         filter the list of resources retrieved from the store.
       * update methods - update an existing resource in the store. These
         methods should expect the updated resource to be correctly identified
         by its unique key or identifier and raise an exception if the resource
         does not exist.
       * delete methods - delete an existing resource from the store. These
         methods should expect the resource to be correctly identified by its
         unique key or identifier. If the resource does not exist,
         an exception should be raised.

    Best practices for implementing and keeping this interface clean and easy to
    maintain and extend:

      * keep methods organized by resource type and ordered by CRUD operation
      * for resources with multiple keys, don't implement multiple get or list
      methods here if the same functionality can be achieved by a single get or
      list method. Instead, implement them in the BaseZenStore class and have
      them call the generic get or list method in this interface.
      * keep the logic required to convert between ZenML domain Model classes
      and internal store representations outside the ZenML domain Model classes
      * methods for resources that have two or more unique keys (e.g. a Project
      is uniquely identified by its name as well as its UUID) should reflect
      that in the method variants and/or method arguments:
        * methods that take in a resource identifier as argument should accept
        all variants of the identifier (e.g. `project_name_or_uuid` for methods
        that get/list/update/delete Projects)
        * if a compound key is involved, separate get methods should be
        implemented (e.g. `get_pipeline` to get a pipeline by ID and
        `get_pipeline_in_project` to get a pipeline by its name and the ID of
        the project it belongs to)
      * methods for resources that are scoped as children of other resources
      (e.g. a Stack is always owned by a Project) should reflect the
      key(s) of the parent resource in the provided methods and method
      arguments:
        * create methods should take the parent resource UUID(s) as an argument
        (e.g. `create_stack` takes in the project ID)
        * get methods should be provided to retrieve a resource by the compound
        key that includes the parent resource key(s)
        * list methods should feature optional filter arguments that reflect
        the parent resource key(s)
    """

    # ---------------------------------
    # Initialization and configuration
    # ---------------------------------

    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the store.

        This method is called immediately after the store is created. It should
        be used to set up the backend (database, connection etc.).
        """

    @abstractmethod
    def get_store_info(self) -> ServerModel:
        """Get information about the store.

        Returns:
            Information about the store.
        """

    # ------
    # Stacks
    # ------

    @abstractmethod
    def create_stack(self, stack: StackRequestModel) -> StackResponseModel:
        """Create a new stack.

        Args:
            stack: The stack to create.

        Returns:
            The created stack.

        Raises:
            StackExistsError: If a stack with the same name is already owned
                by this user in this project.
        """

    @abstractmethod
    def get_stack(self, stack_id: UUID) -> StackResponseModel:
        """Get a stack by its unique ID.

        Args:
            stack_id: The ID of the stack to get.

        Returns:
            The stack with the given ID.

        Raises:
            KeyError: if the stack doesn't exist.
        """

    @abstractmethod
    def list_stacks(
        self, stack_filter_model: StackFilterModel
    ) -> Page[StackResponseModel]:
        """List all stacks matching the given filter criteria.

        Args:
            stack_filter_model: All filter parameters including pagination
                params

        Returns:
            A list of all stacks matching the filter criteria.
        """

    @abstractmethod
    def update_stack(
        self, stack_id: UUID, stack_update: StackUpdateModel
    ) -> StackResponseModel:
        """Update a stack.

        Args:
            stack_id: The ID of the stack update.
            stack_update: The update request on the stack.

        Returns:
            The updated stack.

        Raises:
            KeyError: if the stack doesn't exist.
        """

    @abstractmethod
    def delete_stack(self, stack_id: UUID) -> None:
        """Delete a stack.

        Args:
            stack_id: The ID of the stack to delete.

        Raises:
            KeyError: if the stack doesn't exist.
        """

    # ----------------
    # Stack components
    # ----------------

    @abstractmethod
    def create_stack_component(
        self, component: ComponentRequestModel
    ) -> ComponentResponseModel:
        """Create a stack component.

        Args:
            component: The stack component to create.

        Returns:
            The created stack component.

        Raises:
            StackComponentExistsError: If a stack component with the same name
                and type is already owned by this user in this project.
        """

    @abstractmethod
    def list_stack_components(
        self, component_filter_model: ComponentFilterModel
    ) -> Page[ComponentResponseModel]:
        """List all stack components matching the given filter criteria.

        Args:
            component_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all stack components matching the filter criteria.
        """

    @abstractmethod
    def get_stack_component(
        self, component_id: UUID
    ) -> ComponentResponseModel:
        """Get a stack component by ID.

        Args:
            component_id: The ID of the stack component to get.

        Returns:
            The stack component.

        Raises:
            KeyError: if the stack component doesn't exist.
        """

    @abstractmethod
    def update_stack_component(
        self,
        component_id: UUID,
        component_update: ComponentUpdateModel,
    ) -> ComponentResponseModel:
        """Update an existing stack component.

        Args:
            component_id: The ID of the stack component to update.
            component_update: The update to be applied to the stack component.

        Returns:
            The updated stack component.

        Raises:
            KeyError: if the stack component doesn't exist.
        """

    @abstractmethod
    def delete_stack_component(self, component_id: UUID) -> None:
        """Delete a stack component.

        Args:
            component_id: The ID of the stack component to delete.

        Raises:
            KeyError: if the stack component doesn't exist.
            ValueError: if the stack component is part of one or more stacks.
        """

    # -----------------------
    # Stack component flavors
    # -----------------------

    @abstractmethod
    def create_flavor(
        self,
        flavor: FlavorRequestModel,
    ) -> FlavorResponseModel:
        """Creates a new stack component flavor.

        Args:
            flavor: The stack component flavor to create.

        Returns:
            The newly created flavor.

        Raises:
            EntityExistsError: If a flavor with the same name and type
                is already owned by this user in this project.
        """

    @abstractmethod
    def get_flavor(self, flavor_id: UUID) -> FlavorResponseModel:
        """Get a stack component flavor by ID.

        Args:
            flavor_id: The ID of the flavor to get.

        Returns:
            The stack component flavor.

        Raises:
            KeyError: if the stack component flavor doesn't exist.
        """

    @abstractmethod
    def list_flavors(
        self, flavor_filter_model: FlavorFilterModel
    ) -> Page[FlavorResponseModel]:
        """List all stack component flavors matching the given filter criteria.

        Args:
            flavor_filter_model: All filter parameters including pagination
                params.

        Returns:
            List of all the stack component flavors matching the given criteria.
        """

    @abstractmethod
    def delete_flavor(self, flavor_id: UUID) -> None:
        """Delete a stack component flavor.

        Args:
            flavor_id: The ID of the stack component flavor to delete.

        Raises:
            KeyError: if the stack component flavor doesn't exist.
        """

    # -----
    # Users
    # -----

    @abstractmethod
    def create_user(self, user: UserRequestModel) -> UserResponseModel:
        """Creates a new user.

        Args:
            user: User to be created.

        Returns:
            The newly created user.

        Raises:
            EntityExistsError: If a user with the given name already exists.
        """

    @abstractmethod
    def get_user(
        self,
        user_name_or_id: Optional[Union[str, UUID]] = None,
        include_private: bool = False,
    ) -> UserResponseModel:
        """Gets a specific user, when no id is specified the active user is returned.

        Args:
            user_name_or_id: The name or ID of the user to get.
            include_private: Whether to include private user information

        Returns:
            The requested user, if it was found.

        Raises:
            KeyError: If no user with the given name or ID exists.
        """

    @abstractmethod
    def get_auth_user(
        self, user_name_or_id: Union[str, UUID]
    ) -> UserAuthModel:
        """Gets the auth model to a specific user.

        Args:
            user_name_or_id: The name or ID of the user to get.

        Returns:
            The requested user, if it was found.
        """

    @abstractmethod
    def list_users(
        self, user_filter_model: UserFilterModel
    ) -> Page[UserResponseModel]:
        """List all users.

        Args:
            user_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all users.
        """

    @abstractmethod
    def update_user(
        self, user_id: UUID, user_update: UserUpdateModel
    ) -> UserResponseModel:
        """Updates an existing user.

        Args:
            user_id: The id of the user to update.
            user_update: The update to be applied to the user.

        Returns:
            The updated user.

        Raises:
            KeyError: If no user with the given name exists.
        """

    @abstractmethod
    def delete_user(self, user_name_or_id: Union[str, UUID]) -> None:
        """Deletes a user.

        Args:
            user_name_or_id: The name or ID of the user to delete.

        Raises:
            KeyError: If no user with the given ID exists.
        """

    # -----
    # Teams
    # -----

    @abstractmethod
    def create_team(self, team: TeamRequestModel) -> TeamResponseModel:
        """Creates a new team.

        Args:
            team: The team model to create.

        Returns:
            The newly created team.
        """

    @abstractmethod
    def get_team(self, team_name_or_id: Union[str, UUID]) -> TeamResponseModel:
        """Gets a specific team.

        Args:
            team_name_or_id: Name or ID of the team to get.

        Returns:
            The requested team.

        Raises:
            KeyError: If no team with the given name or ID exists.
        """

    @abstractmethod
    def list_teams(
        self, team_filter_model: TeamFilterModel
    ) -> Page[TeamResponseModel]:
        """List all teams matching the given filter criteria.

        Args:
            team_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all teams matching the filter criteria.
        """

    @abstractmethod
    def update_team(
        self, team_id: UUID, team_update: TeamUpdateModel
    ) -> TeamResponseModel:
        """Update an existing team.

        Args:
            team_id: The ID of the team to be updated.
            team_update: The update to be applied to the team.

        Returns:
            The updated team.

        Raises:
            KeyError: if the team does not exist.
        """

    @abstractmethod
    def delete_team(self, team_name_or_id: Union[str, UUID]) -> None:
        """Deletes a team.

        Args:
            team_name_or_id: Name or ID of the team to delete.

        Raises:
            KeyError: If no team with the given ID exists.
        """

    # -----
    # Roles
    # -----

    @abstractmethod
    def create_role(self, role: RoleRequestModel) -> RoleResponseModel:
        """Creates a new role.

        Args:
            role: The role model to create.

        Returns:
            The newly created role.

        Raises:
            EntityExistsError: If a role with the given name already exists.
        """

    @abstractmethod
    def get_role(self, role_name_or_id: Union[str, UUID]) -> RoleResponseModel:
        """Gets a specific role.

        Args:
            role_name_or_id: Name or ID of the role to get.

        Returns:
            The requested role.

        Raises:
            KeyError: If no role with the given name exists.
        """

    @abstractmethod
    def list_roles(
        self, role_filter_model: RoleFilterModel
    ) -> Page[RoleResponseModel]:
        """List all roles matching the given filter criteria.

        Args:
            role_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all roles matching the filter criteria.
        """

    @abstractmethod
    def update_role(
        self, role_id: UUID, role_update: RoleUpdateModel
    ) -> RoleResponseModel:
        """Update an existing role.

        Args:
            role_id: The ID of the role to be updated.
            role_update: The update to be applied to the role.

        Returns:
            The updated role.

        Raises:
            KeyError: if the role does not exist.
        """

    @abstractmethod
    def delete_role(self, role_name_or_id: Union[str, UUID]) -> None:
        """Deletes a role.

        Args:
            role_name_or_id: Name or ID of the role to delete.

        Raises:
            KeyError: If no role with the given ID exists.
        """

    # ---------------------
    # User Role assignments
    # ---------------------
    @abstractmethod
    def create_user_role_assignment(
        self, user_role_assignment: UserRoleAssignmentRequestModel
    ) -> UserRoleAssignmentResponseModel:
        """Creates a new role assignment.

        Args:
            user_role_assignment: The role assignment model to create.

        Returns:
            The newly created role assignment.
        """

    @abstractmethod
    def get_user_role_assignment(
        self, user_role_assignment_id: UUID
    ) -> UserRoleAssignmentResponseModel:
        """Gets a specific role assignment.

        Args:
            user_role_assignment_id: ID of the role assignment to get.

        Returns:
            The requested role assignment.

        Raises:
            KeyError: If no role assignment with the given ID exists.
        """

    @abstractmethod
    def delete_user_role_assignment(
        self, user_role_assignment_id: UUID
    ) -> None:
        """Delete a specific role assignment.

        Args:
            user_role_assignment_id: The ID of the specific role assignment
        """

    @abstractmethod
    def list_user_role_assignments(
        self, user_role_assignment_filter_model: UserRoleAssignmentFilterModel
    ) -> Page[UserRoleAssignmentResponseModel]:
        """List all roles assignments matching the given filter criteria.

        Args:
            user_role_assignment_filter_model: All filter parameters including
                pagination params.

        Returns:
            A list of all roles assignments matching the filter criteria.
        """

    # ---------------------
    # Team Role assignments
    # ---------------------
    @abstractmethod
    def create_team_role_assignment(
        self, team_role_assignment: TeamRoleAssignmentRequestModel
    ) -> TeamRoleAssignmentResponseModel:
        """Creates a new team role assignment.

        Args:
            team_role_assignment: The role assignment model to create.

        Returns:
            The newly created role assignment.
        """

    @abstractmethod
    def get_team_role_assignment(
        self, team_role_assignment_id: UUID
    ) -> TeamRoleAssignmentResponseModel:
        """Gets a specific role assignment.

        Args:
            team_role_assignment_id: ID of the role assignment to get.

        Returns:
            The requested role assignment.

        Raises:
            KeyError: If no role assignment with the given ID exists.
        """

    @abstractmethod
    def delete_team_role_assignment(
        self, team_role_assignment_id: UUID
    ) -> None:
        """Delete a specific role assignment.

        Args:
            team_role_assignment_id: The ID of the specific role assignment
        """

    @abstractmethod
    def list_team_role_assignments(
        self, team_role_assignment_filter_model: TeamRoleAssignmentFilterModel
    ) -> Page[TeamRoleAssignmentResponseModel]:
        """List all roles assignments matching the given filter criteria.

        Args:
            team_role_assignment_filter_model: All filter parameters including
                pagination params.

        Returns:
            A list of all roles assignments matching the filter criteria.
        """

    # --------
    # Projects
    # --------

    @abstractmethod
    def create_project(
        self, project: ProjectRequestModel
    ) -> ProjectResponseModel:
        """Creates a new project.

        Args:
            project: The project to create.

        Returns:
            The newly created project.

        Raises:
            EntityExistsError: If a project with the given name already exists.
        """

    @abstractmethod
    def get_project(
        self, project_name_or_id: Union[UUID, str]
    ) -> ProjectResponseModel:
        """Get an existing project by name or ID.

        Args:
            project_name_or_id: Name or ID of the project to get.

        Returns:
            The requested project.

        Raises:
            KeyError: If there is no such project.
        """

    @abstractmethod
    def list_projects(
        self, project_filter_model: ProjectFilterModel
    ) -> Page[ProjectResponseModel]:
        """List all project matching the given filter criteria.

        Args:
            project_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all project matching the filter criteria.
        """

    @abstractmethod
    def update_project(
        self, project_id: UUID, project_update: ProjectUpdateModel
    ) -> ProjectResponseModel:
        """Update an existing project.

        Args:
            project_id: The ID of the project to be updated.
            project_update: The update to be applied to the project.

        Returns:
            The updated project.

        Raises:
            KeyError: if the project does not exist.
        """

    @abstractmethod
    def delete_project(self, project_name_or_id: Union[str, UUID]) -> None:
        """Deletes a project.

        Args:
            project_name_or_id: Name or ID of the project to delete.

        Raises:
            KeyError: If no project with the given name exists.
        """

    # ---------
    # Pipelines
    # ---------

    @abstractmethod
    def create_pipeline(
        self,
        pipeline: PipelineRequestModel,
    ) -> PipelineResponseModel:
        """Creates a new pipeline in a project.

        Args:
            pipeline: The pipeline to create.

        Returns:
            The newly created pipeline.

        Raises:
            KeyError: if the project does not exist.
            EntityExistsError: If an identical pipeline already exists.
        """

    @abstractmethod
    def get_pipeline(self, pipeline_id: UUID) -> PipelineResponseModel:
        """Get a pipeline with a given ID.

        Args:
            pipeline_id: ID of the pipeline.

        Returns:
            The pipeline.

        Raises:
            KeyError: if the pipeline does not exist.
        """

    @abstractmethod
    def list_pipelines(
        self, pipeline_filter_model: PipelineFilterModel
    ) -> Page[PipelineResponseModel]:
        """List all pipelines matching the given filter criteria.

        Args:
            pipeline_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all pipelines matching the filter criteria.
        """

    @abstractmethod
    def update_pipeline(
        self,
        pipeline_id: UUID,
        pipeline_update: PipelineUpdateModel,
    ) -> PipelineResponseModel:
        """Updates a pipeline.

        Args:
            pipeline_id: The ID of the pipeline to be updated.
            pipeline_update: The update to be applied.

        Returns:
            The updated pipeline.

        Raises:
            KeyError: if the pipeline doesn't exist.
        """

    @abstractmethod
    def delete_pipeline(self, pipeline_id: UUID) -> None:
        """Deletes a pipeline.

        Args:
            pipeline_id: The ID of the pipeline to delete.

        Raises:
            KeyError: if the pipeline doesn't exist.
        """

    # ---------
    # Schedules
    # ---------

    @abstractmethod
    def create_schedule(
        self, schedule: ScheduleRequestModel
    ) -> ScheduleResponseModel:
        """Creates a new schedule.

        Args:
            schedule: The schedule to create.

        Returns:
            The newly created schedule.
        """

    @abstractmethod
    def get_schedule(self, schedule_id: UUID) -> ScheduleResponseModel:
        """Get a schedule with a given ID.

        Args:
            schedule_id: ID of the schedule.

        Returns:
            The schedule.

        Raises:
            KeyError: if the schedule does not exist.
        """

    @abstractmethod
    def list_schedules(
        self, schedule_filter_model: ScheduleFilterModel
    ) -> Page[ScheduleResponseModel]:
        """List all schedules in the project.

        Args:
            schedule_filter_model: All filter parameters including pagination
                params

        Returns:
            A list of schedules.
        """

    @abstractmethod
    def update_schedule(
        self,
        schedule_id: UUID,
        schedule_update: ScheduleUpdateModel,
    ) -> ScheduleResponseModel:
        """Updates a schedule.

        Args:
            schedule_id: The ID of the schedule to be updated.
            schedule_update: The update to be applied.

        Returns:
            The updated schedule.

        Raises:
            KeyError: if the schedule doesn't exist.
        """

    @abstractmethod
    def delete_schedule(self, schedule_id: UUID) -> None:
        """Deletes a schedule.

        Args:
            schedule_id: The ID of the schedule to delete.

        Raises:
            KeyError: if the schedule doesn't exist.
        """

    # --------------
    # Pipeline runs
    # --------------

    @abstractmethod
    def create_run(
        self, pipeline_run: PipelineRunRequestModel
    ) -> PipelineRunResponseModel:
        """Creates a pipeline run.

        Args:
            pipeline_run: The pipeline run to create.

        Returns:
            The created pipeline run.

        Raises:
            EntityExistsError: If an identical pipeline run already exists.
            KeyError: If the pipeline does not exist.
        """

    @abstractmethod
    def get_run(
        self, run_name_or_id: Union[str, UUID]
    ) -> PipelineRunResponseModel:
        """Gets a pipeline run.

        Args:
            run_name_or_id: The name or ID of the pipeline run to get.

        Returns:
            The pipeline run.

        Raises:
            KeyError: if the pipeline run doesn't exist.
        """

    @abstractmethod
    def get_or_create_run(
        self, pipeline_run: PipelineRunRequestModel
    ) -> PipelineRunResponseModel:
        """Gets or creates a pipeline run.

        If a run with the same ID or name already exists, it is returned.
        Otherwise, a new run is created.

        Args:
            pipeline_run: The pipeline run to get or create.

        Returns:
            The pipeline run.
        """

    @abstractmethod
    def list_runs(
        self, runs_filter_model: PipelineRunFilterModel
    ) -> Page[PipelineRunResponseModel]:
        """List all pipeline runs matching the given filter criteria.

        Args:
            runs_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all pipeline runs matching the filter criteria.
        """

    @abstractmethod
    def update_run(
        self, run_id: UUID, run_update: PipelineRunUpdateModel
    ) -> PipelineRunResponseModel:
        """Updates a pipeline run.

        Args:
            run_id: The ID of the pipeline run to update.
            run_update: The update to be applied to the pipeline run.

        Returns:
            The updated pipeline run.

        Raises:
            KeyError: if the pipeline run doesn't exist.
        """

    @abstractmethod
    def delete_run(self, run_id: UUID) -> None:
        """Deletes a pipeline run.

        Args:
            run_id: The ID of the pipeline run to delete.

        Raises:
            KeyError: if the pipeline run doesn't exist.
        """

    # ------------------
    # Pipeline run steps
    # ------------------

    @abstractmethod
    def create_run_step(
        self, step_run: StepRunRequestModel
    ) -> StepRunResponseModel:
        """Creates a step run.

        Args:
            step_run: The step run to create.

        Returns:
            The created step run.

        Raises:
            EntityExistsError: if the step run already exists.
            KeyError: if the pipeline run doesn't exist.
        """

    @abstractmethod
    def get_run_step(self, step_run_id: UUID) -> StepRunResponseModel:
        """Get a step run by ID.

        Args:
            step_run_id: The ID of the step run to get.

        Returns:
            The step run.

        Raises:
            KeyError: if the step run doesn't exist.
        """

    @abstractmethod
    def list_run_steps(
        self, step_run_filter_model: StepRunFilterModel
    ) -> Page[StepRunResponseModel]:
        """List all step runs matching the given filter criteria.

        Args:
            step_run_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all step runs matching the filter criteria.
        """

    @abstractmethod
    def update_run_step(
        self,
        step_run_id: UUID,
        step_run_update: StepRunUpdateModel,
    ) -> StepRunResponseModel:
        """Updates a step run.

        Args:
            step_run_id: The ID of the step to update.
            step_run_update: The update to be applied to the step.

        Returns:
            The updated step run.

        Raises:
            KeyError: if the step run doesn't exist.
        """

    # ---------
    # Artifacts
    # ---------

    @abstractmethod
    def create_artifact(
        self, artifact: ArtifactRequestModel
    ) -> ArtifactResponseModel:
        """Creates an artifact.

        Args:
            artifact: The artifact to create.

        Returns:
            The created artifact.
        """

    @abstractmethod
    def get_artifact(self, artifact_id: UUID) -> ArtifactResponseModel:
        """Gets an artifact.

        Args:
            artifact_id: The ID of the artifact to get.

        Returns:
            The artifact.

        Raises:
            KeyError: if the artifact doesn't exist.
        """

    @abstractmethod
    def list_artifacts(
        self, artifact_filter_model: ArtifactFilterModel
    ) -> Page[ArtifactResponseModel]:
        """List all artifacts matching the given filter criteria.

        Args:
            artifact_filter_model: All filter parameters including pagination
                params.

        Returns:
            A list of all artifacts matching the filter criteria.
        """

    @abstractmethod
    def delete_artifact(self, artifact_id: UUID) -> None:
        """Deletes an artifact.

        Args:
            artifact_id: The ID of the artifact to delete.

        Raises:
            KeyError: if the artifact doesn't exist.
        """
