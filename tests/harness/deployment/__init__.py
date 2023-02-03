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
"""ZenML test framework deployments."""

from tests.harness.deployment.base import BaseTestDeployment
from tests.harness.deployment.local_default import LocalDefaultTestDeployment
from tests.harness.deployment.local_docker import LocalDockerTestDeployment
from tests.harness.deployment.server_docker import ServerDockerTestDeployment
from tests.harness.deployment.server_docker_compose import (
    ServerDockerComposeTestDeployment,
)
from tests.harness.deployment.server_external import (
    ExternalServerTestDeployment,
)
from tests.harness.deployment.server_local import ServerLocalTestDeployment

__all__ = [
    "BaseTestDeployment",
    "LocalDefaultTestDeployment",
    "LocalDockerTestDeployment",
    "ServerLocalTestDeployment",
    "ServerDockerTestDeployment",
    "ServerDockerComposeTestDeployment",
    "ExternalServerTestDeployment",
]
