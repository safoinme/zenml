#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
from rich import print

from zenml.steps import StepContext, step

SECRET_NAME = "example_secret"
AZURE_SECRET_NAME = "examplesecret"
SECRET_KEY = "example_secret_key"


@step
def secret_loader(
    context: StepContext,
) -> None:
    """Load the example secret from the secret manager."""
    # Load Secret from active secret manager. This will fail if no secret
    #  manager is active or if that secret does not exist
    if context.stack.secrets_manager.flavor == "azure":
        retrieved_secret = context.stack.secrets_manager.get_secret(
            AZURE_SECRET_NAME
        )
    else:
        retrieved_secret = context.stack.secrets_manager.get_secret(SECRET_NAME)

    # Load specific secret value from the secret using the secret key
    print(
        f"The secret `{SECRET_NAME}` contains the following key-value pair "
        f"{{{SECRET_KEY}: {retrieved_secret.content[SECRET_KEY]}}}"
    )
    return
