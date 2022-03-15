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
"""
The AWS integration submodule provides a way to run ZenML pipelines in a cloud
environment. Specifically, it allows the use of cloud artifact stores,
and an `io` module to handle file operations on S3 buckets.
"""

from zenml.integrations.constants import AWS
from zenml.integrations.integration import Integration


class AWSIntegration(Integration):
    """Definition of AWS integration for ZenML."""

    NAME = AWS
    REQUIREMENTS = ["s3fs==2022.2.0", "sagemaker==2.77.1"]

    @classmethod
    def activate(cls) -> None:
        """Activates the integration."""
        from zenml.integrations.aws import artifact_stores  # noqa
        from zenml.integrations.aws import io  # noqa
        from zenml.integrations.aws import step_operators  # noqa


AWSIntegration.check_installation()
