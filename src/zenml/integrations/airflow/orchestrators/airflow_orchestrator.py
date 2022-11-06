# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

# Minor parts of the  `prepare_or_run_pipeline()` method of this file are
# inspired by the airflow dag runner implementation of tfx
"""Implementation of Airflow orchestrator integration."""

import datetime
import functools
import os
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from zenml.constants import ENV_ZENML_SKIP_PIPELINE_REGISTRATION
from zenml.environment import Environment
from zenml.io import fileio
from zenml.logger import get_logger
from zenml.orchestrators import BaseOrchestrator
from zenml.pipelines import Schedule
from zenml.utils import daemon, io_utils
from zenml.utils.source_utils import get_source_root_path

logger = get_logger(__name__)

if TYPE_CHECKING:
    from zenml.config.pipeline_deployment import PipelineDeployment
    from zenml.config.step_configurations import Step
    from zenml.stack import Stack

AIRFLOW_ROOT_DIR = "airflow"
DAG_FILEPATH_OPTION_KEY = "dag_filepath"


@contextmanager
def set_environment_variable(key: str, value: str) -> Iterator[None]:
    """Temporarily sets an environment variable.

    The value will only be set while this context manager is active and will
    be reset to the previous value afterward.

    Args:
        key: The environment variable key.
        value: The environment variable value.

    Yields:
        None.
    """
    old_value = os.environ.get(key, None)
    try:
        os.environ[key] = value
        yield
    finally:
        if old_value:
            os.environ[key] = old_value
        else:
            del os.environ[key]


class AirflowOrchestrator(BaseOrchestrator):
    """Orchestrator responsible for running pipelines using Airflow."""

    _orchestrator_run_id: Optional[str] = None

    def __init__(self, **values: Any):
        """Sets environment variables to configure airflow.

        Args:
            **values: Values to set in the orchestrator.
        """
        super().__init__(**values)
        self.airflow_home = os.path.join(
            io_utils.get_global_config_directory(),
            AIRFLOW_ROOT_DIR,
            str(self.id),
        )
        self._set_env()

    @staticmethod
    def _translate_schedule(
        schedule: Optional[Schedule] = None,
    ) -> Dict[str, Any]:
        """Convert ZenML schedule into Airflow schedule.

        The Airflow schedule uses slightly different naming and needs some
        default entries for execution without a schedule.

        Args:
            schedule: Containing the interval, start and end date and
                a boolean flag that defines if past runs should be caught up
                on

        Returns:
            Airflow configuration dict.
        """
        if schedule:
            if schedule.cron_expression:
                start_time = schedule.start_time or (
                    datetime.datetime.now() - datetime.timedelta(1)
                )
                return {
                    "schedule_interval": schedule.cron_expression,
                    "start_date": start_time,
                    "end_date": schedule.end_time,
                    "catchup": schedule.catchup,
                }
            else:
                return {
                    "schedule_interval": schedule.interval_second,
                    "start_date": schedule.start_time,
                    "end_date": schedule.end_time,
                    "catchup": schedule.catchup,
                }

        return {
            "schedule_interval": "@once",
            # set the a start time in the past and disable catchup so airflow runs the dag immediately
            "start_date": datetime.datetime.now() - datetime.timedelta(7),
            "catchup": False,
        }

    def get_orchestrator_run_id(self) -> str:
        """Returns the active orchestrator run id.

        Raises:
            RuntimeError: If no run id exists. This happens when this method
                gets called while the orchestrator is not running a pipeline.

        Returns:
            The orchestrator run id.
        """
        if not self._orchestrator_run_id:
            raise RuntimeError("No run id set.")

        return self._orchestrator_run_id

    def prepare_or_run_pipeline(
        self,
        deployment: "PipelineDeployment",
        stack: "Stack",
    ) -> Any:
        """Creates an Airflow DAG as the intermediate representation for the pipeline.

        This DAG will be loaded by airflow in the target environment
        and used for orchestration of the pipeline.

        How it works:
        -------------
        A new airflow_dag is instantiated with the pipeline name and among
        others things the run schedule.

        For each step of the pipeline a callable is created. This callable
        uses the run_step() method to execute the step. The parameters of
        this callable are pre-filled and an airflow step_operator is created
        within the dag. The dependencies to upstream steps are then
        configured.

        Finally, the dag is fully complete and can be returned.

        Args:
            deployment: The pipeline deployment to prepare or run.
            stack: The stack the pipeline will run on.

        Returns:
            The Airflow DAG.
        """
        import airflow
        from airflow.operators import python as airflow_python

        # Instantiate and configure airflow Dag with name and schedule
        airflow_dag = airflow.DAG(
            dag_id=deployment.pipeline.name,
            is_paused_upon_creation=False,
            **self._translate_schedule(deployment.schedule),
        )

        # Dictionary mapping step names to airflow_operators. This will be needed
        # to configure airflow operator dependencies
        step_name_to_airflow_operator = {}

        for step in deployment.steps.values():
            # Create callable that will be used by airflow to execute the step
            # within the orchestrated environment
            def _step_callable(step_instance: "Step", **kwargs):
                if self.requires_resources_in_orchestration_environment(step):
                    logger.warning(
                        "Specifying step resources is not yet supported for "
                        "the Airflow orchestrator, ignoring resource "
                        "configuration for step %s.",
                        step.name,
                    )
                self._orchestrator_run_id = kwargs["ti"].get_dagrun().run_id
                self._prepare_run(deployment=deployment)
                self.run_step(step=step_instance)
                self._cleanup_run()
                self._orchestrator_run_id = None

            # Create airflow python operator that contains the step callable
            airflow_operator = airflow_python.PythonOperator(
                dag=airflow_dag,
                task_id=step.config.name,
                provide_context=True,
                python_callable=functools.partial(
                    _step_callable, step_instance=step
                ),
            )

            # Configure the current airflow operator to run after all upstream
            # operators finished executing
            step_name_to_airflow_operator[step.config.name] = airflow_operator
            for upstream_step_name in step.spec.upstream_steps:
                airflow_operator.set_upstream(
                    step_name_to_airflow_operator[upstream_step_name]
                )

        # Return the finished airflow dag
        return airflow_dag

    @property
    def dags_directory(self) -> str:
        """Returns path to the airflow dags directory.

        Returns:
            Path to the airflow dags directory.
        """
        return os.path.join(self.airflow_home, "dags")

    @property
    def pid_file(self) -> str:
        """Returns path to the daemon PID file.

        Returns:
            Path to the daemon PID file.
        """
        return os.path.join(self.airflow_home, "airflow_daemon.pid")

    @property
    def log_file(self) -> str:
        """Returns path to the airflow log file.

        Returns:
            str: Path to the airflow log file.
        """
        return os.path.join(self.airflow_home, "airflow_orchestrator.log")

    @property
    def password_file(self) -> str:
        """Returns path to the webserver password file.

        Returns:
            Path to the webserver password file.
        """
        return os.path.join(self.airflow_home, "standalone_admin_password.txt")

    def _set_env(self) -> None:
        """Sets environment variables to configure airflow."""
        os.environ["AIRFLOW_HOME"] = self.airflow_home
        os.environ["AIRFLOW__CORE__DAGS_FOLDER"] = self.dags_directory
        os.environ["AIRFLOW__CORE__DAG_DISCOVERY_SAFE_MODE"] = "false"
        os.environ["AIRFLOW__CORE__LOAD_EXAMPLES"] = "false"
        # check the DAG folder every 10 seconds for new files
        os.environ["AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL"] = "10"

    def _copy_to_dag_directory_if_necessary(self, dag_filepath: str) -> None:
        """Copies DAG module to the Airflow DAGs directory if not already present.

        Args:
            dag_filepath: Path to the file in which the DAG is defined.
        """
        dags_directory = io_utils.resolve_relative_path(self.dags_directory)

        if dags_directory == os.path.dirname(dag_filepath):
            logger.debug("File is already in airflow DAGs directory.")
        else:
            logger.debug(
                "Copying dag file '%s' to DAGs directory.", dag_filepath
            )
            destination_path = os.path.join(
                dags_directory, os.path.basename(dag_filepath)
            )
            if fileio.exists(destination_path):
                logger.info(
                    "File '%s' already exists, overwriting with new DAG file",
                    destination_path,
                )
            fileio.copy(dag_filepath, destination_path, overwrite=True)

    def _log_webserver_credentials(self) -> None:
        """Logs URL and credentials to log in to the airflow webserver.

        Raises:
            FileNotFoundError: If the password file does not exist.
        """
        if fileio.exists(self.password_file):
            with open(self.password_file) as file:
                password = file.read().strip()
        else:
            raise FileNotFoundError(
                f"Can't find password file '{self.password_file}'"
            )
        logger.info(
            "To inspect your DAGs, login to http://localhost:8080 "
            "with username: admin password: %s",
            password,
        )

    def prepare_pipeline_deployment(
        self,
        deployment: "PipelineDeployment",
        stack: "Stack",
    ) -> None:
        """Checks Airflow is running and copies DAG file to the DAGs directory.

        Args:
            deployment: The pipeline deployment configuration.
            stack: The stack on which the pipeline will be deployed.

        Raises:
            RuntimeError: If Airflow is not running or no DAG filepath runtime
                          option is provided.
        """
        if not self.is_running:
            raise RuntimeError(
                "Airflow orchestrator is currently not running. Run `zenml "
                "stack up` to provision resources for the active stack."
            )

        if Environment.in_notebook():
            raise RuntimeError(
                "Unable to run the Airflow orchestrator from within a "
                "notebook. Airflow requires a python file which contains a "
                "global Airflow DAG object and therefore does not work with "
                "notebooks. Please copy your ZenML pipeline code in a python "
                "file and try again."
            )

        try:
            dag_filepath = deployment.pipeline.extra[DAG_FILEPATH_OPTION_KEY]
        except KeyError:
            raise RuntimeError(
                f"No DAG filepath found in runtime configuration. Make sure "
                f"to add the filepath to your airflow DAG file as a runtime "
                f"option (key: '{DAG_FILEPATH_OPTION_KEY}')."
            )

        self._copy_to_dag_directory_if_necessary(dag_filepath=dag_filepath)

    @property
    def is_running(self) -> bool:
        """Returns whether the airflow daemon is currently running.

        Returns:
            True if the daemon is running, False otherwise.

        Raises:
            RuntimeError: If port 8080 is occupied.
        """
        from airflow.cli.commands.standalone_command import StandaloneCommand
        from airflow.jobs.triggerer_job import TriggererJob

        daemon_running = daemon.check_if_daemon_is_running(self.pid_file)

        command = StandaloneCommand()
        webserver_port_open = command.port_open(8080)

        if not daemon_running:
            if webserver_port_open:
                raise RuntimeError(
                    "The airflow daemon does not seem to be running but "
                    "local port 8080 is occupied. Make sure the port is "
                    "available and try again."
                )

            # exit early so we don't check non-existing airflow databases
            return False

        # we can't use StandaloneCommand().is_ready() here as the
        # Airflow SequentialExecutor apparently does not send a heartbeat
        # while running a task which would result in this returning `False`
        # even if Airflow is running.
        airflow_running = webserver_port_open and command.job_running(
            TriggererJob
        )
        return airflow_running

    @property
    def is_provisioned(self) -> bool:
        """Returns whether the airflow daemon is currently running.

        Returns:
            True if the airflow daemon is running, False otherwise.
        """
        return self.is_running

    def provision(self) -> None:
        """Ensures that Airflow is running."""
        if self.is_running:
            logger.info("Airflow is already running.")
            self._log_webserver_credentials()
            return

        if not fileio.exists(self.dags_directory):
            io_utils.create_dir_recursive_if_not_exists(self.dags_directory)

        from airflow.cli.commands.standalone_command import StandaloneCommand

        try:
            command = StandaloneCommand()
            # Skip pipeline registration inside the airflow server process.
            # When searching for DAGs, airflow imports the runner file in a
            # randomly generated module. If we don't skip pipeline registration,
            # it would fail by trying to register a pipeline with an existing
            # name but different module sources for the steps.
            with set_environment_variable(
                key=ENV_ZENML_SKIP_PIPELINE_REGISTRATION, value="True"
            ):
                # Run the daemon with a working directory inside the current
                # zenml repo so the same repo will be used to run the DAGs
                daemon.run_as_daemon(
                    command.run,
                    pid_file=self.pid_file,
                    log_file=self.log_file,
                    working_directory=get_source_root_path(),
                )
            while not self.is_running:
                # Wait until the daemon started all the relevant airflow
                # processes
                time.sleep(0.1)
            self._log_webserver_credentials()
        except Exception as e:
            logger.error(e)
            logger.error(
                "An error occurred while starting the Airflow daemon. If you "
                "want to start it manually, use the commands described in the "
                "official Airflow quickstart guide for running Airflow locally."
            )
            self.deprovision()

    def deprovision(self) -> None:
        """Stops the airflow daemon if necessary and tears down resources."""
        if self.is_running:
            daemon.stop_daemon(self.pid_file)

        fileio.rmtree(self.airflow_home)
        logger.info("Airflow spun down.")
