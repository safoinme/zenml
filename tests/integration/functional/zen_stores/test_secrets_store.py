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

import time
from contextlib import ExitStack as does_not_raise
from datetime import timedelta

import pytest

from tests.integration.functional.utils import sample_name
from tests.integration.functional.zen_stores.utils import (
    SecretContext,
    UserContext,
    WorkspaceContext,
)
from zenml.client import Client
from zenml.enums import SecretScope, SecretsStoreType, StoreType
from zenml.exceptions import EntityExistsError, IllegalOperationError
from zenml.models.secret_models import SecretFilterModel, SecretUpdateModel
from zenml.utils.string_utils import random_str

# The AWS secrets store takes some time to reflect new and updated secrets in
# the `list_secrets` API. This is the number of seconds to wait before making
# `list_secrets` calls after creating/updating a secret to ensure that the
# latest secret information is returned.
AWS_SECRET_REFRESH_SLEEP = 10


def _get_secrets_store_type() -> SecretsStoreType:
    """Returns the secrets store back-end type that is used by the test
    ZenML deployment.

    Returns:
        The secrets store type that is used by the test ZenML deployment.
    """
    store = Client().zen_store
    return store.get_store_info().secrets_store_type


# .---------.
# | SECRETS |
# '---------'


def test_get_secret_returns_values():
    """Tests that `get_secret` returns secret values."""
    client = Client()
    store = client.zen_store

    values = dict(
        aria="space cat",
        axl="space dog",
    )
    with SecretContext(values=values) as secret:
        assert secret.secret_values == values
        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values


def test_list_secret_excludes_values():
    """Tests that `list_secret` does not return secret values."""
    client = Client()
    store = client.zen_store

    values = dict(
        aria="space cat",
        axl="space dog",
    )
    with SecretContext(values=values) as secret:
        assert secret.secret_values == values
        all_secrets = store.list_secrets(SecretFilterModel(id=secret.id)).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id
        assert len(all_secrets[0].values) == 0


def test_secret_empty_values():
    """Tests that secrets can hold empty values."""
    client = Client()
    store = client.zen_store

    values = dict(
        aria="space cat",
        axl="",
    )
    with SecretContext(values=values) as secret:
        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values

        values["axl"] = "also space cat"
        updated_secret = store.update_secret(
            secret_id=secret.id,
            secret_update=SecretUpdateModel(
                values=dict(
                    axl=values["axl"],
                ),
            ),
        )

        assert updated_secret.secret_values == values

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values


def test_update_secret_existing_values():
    """Tests that existing values a secret can be updated."""
    client = Client()
    store = client.zen_store

    values = dict(
        aria="space cat",
        axl="space dog",
    )
    with SecretContext(values=values) as secret:
        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values

        values["axl"] = "also space cat"
        updated_secret = store.update_secret(
            secret_id=secret.id,
            secret_update=SecretUpdateModel(
                values=dict(
                    axl=values["axl"],
                ),
            ),
        )

        assert updated_secret.secret_values == values

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values


def test_update_secret_add_new_values():
    """Tests that a secret can be updated with new values."""
    client = Client()
    store = client.zen_store

    values = dict(
        aria="space cat",
        axl="also space cat",
    )
    with SecretContext(values=values) as secret:
        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values

        values["blupus"] = "another space cat"
        updated_secret = store.update_secret(
            secret_id=secret.id,
            secret_update=SecretUpdateModel(
                values=dict(
                    blupus=values["blupus"],
                ),
            ),
        )

        assert updated_secret.secret_values == values

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values


def test_update_secret_remove_values():
    """Tests that a secret can be updated to remove values."""
    client = Client()
    store = client.zen_store

    values = dict(
        aria="space cat",
        axl="the only space cat",
    )
    with SecretContext(values=values) as secret:
        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values

        del values["aria"]
        updated_secret = store.update_secret(
            secret_id=secret.id,
            secret_update=SecretUpdateModel(
                values=dict(
                    aria=None,
                ),
            ),
        )

        assert updated_secret.secret_values == values

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values


def test_update_secret_remove_nonexisting_values():
    """Tests that a secret can be updated to remove non-existing values."""
    client = Client()
    store = client.zen_store

    values = dict(
        aria="space cat",
        axl="the only space cat",
    )
    with SecretContext(values=values) as secret:
        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values

        updated_secret = store.update_secret(
            secret_id=secret.id,
            secret_update=SecretUpdateModel(
                values=dict(
                    blupus=None,
                ),
            ),
        )

        assert updated_secret.secret_values == values

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values


def test_update_secret_values_sets_updated_date():
    """Tests that updating secret values sets the updated timestamp."""
    client = Client()
    store = client.zen_store

    values = dict(
        aria="space cat",
        axl="also space cat",
    )
    with SecretContext(values=values) as secret:
        assert secret.updated - secret.created < timedelta(seconds=1)

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values
        assert saved_secret.updated == secret.updated
        assert saved_secret.created == secret.created

        # Wait a second to ensure the updated timestamp is different.
        time.sleep(1)

        values["blupus"] = "another space cat"
        updated_secret = store.update_secret(
            secret_id=secret.id,
            secret_update=SecretUpdateModel(
                values=dict(
                    blupus=values["blupus"],
                ),
            ),
        )

        if _get_secrets_store_type() != SecretsStoreType.AWS:
            # The AWS secrets store returns before the secret is actually
            # updated in the backend.
            assert updated_secret.secret_values == values
            assert updated_secret.created == saved_secret.created
            assert (
                updated_secret.updated - updated_secret.created
                >= timedelta(seconds=1)
            )

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.secret_values == values
        assert saved_secret.updated == updated_secret.updated
        assert saved_secret.created == updated_secret.created


def test_update_secret_name_sets_updated_date():
    """Tests that updating the secret's name sets the updated timestamp."""
    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        assert secret.updated - secret.created < timedelta(seconds=1)

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.name == secret.name
        assert saved_secret.secret_values == secret.secret_values
        assert saved_secret.updated == secret.updated
        assert saved_secret.created == secret.created

        # Wait a second to ensure the updated timestamp is different.
        time.sleep(1)

        new_name = sample_name("arias-secrets")
        updated_secret = store.update_secret(
            secret_id=secret.id,
            secret_update=SecretUpdateModel(
                name=new_name,
            ),
        )

        if _get_secrets_store_type() != SecretsStoreType.AWS:
            # The AWS secrets store returns before the secret is actually
            # updated in the backend.
            assert updated_secret.name == new_name
            assert updated_secret.secret_values == secret.secret_values
            assert updated_secret.created == saved_secret.created
            assert (
                updated_secret.updated - updated_secret.created
                >= timedelta(seconds=1)
            )

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.name == new_name
        assert saved_secret.secret_values == secret.secret_values
        assert saved_secret.updated == updated_secret.updated
        assert saved_secret.created == updated_secret.created


def test_update_secret_name():
    """Tests that a secret name can be updated."""
    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.name == secret.name
        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        new_name = sample_name("arias-secrets")

        updated_secret = store.update_secret(
            secret_id=secret.id,
            secret_update=SecretUpdateModel(
                name=new_name,
            ),
        )

        assert updated_secret.name == new_name

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.name == new_name

        all_secrets = store.list_secrets(
            SecretFilterModel(name=new_name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id


def test_update_secret_name_fails_if_exists_in_workspace():
    """Tests that the name of a workspace scoped secret cannot be changed if
    another secret has the same name."""
    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        with SecretContext() as other_secret:
            saved_secret = store.get_secret(secret_id=secret.id)
            assert saved_secret.name == secret.name

            saved_secret = store.get_secret(secret_id=other_secret.id)
            assert saved_secret.name == other_secret.name

            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id

            with pytest.raises(EntityExistsError):
                store.update_secret(
                    secret_id=secret.id,
                    secret_update=SecretUpdateModel(
                        name=other_secret.name,
                    ),
                )

            saved_secret = store.get_secret(secret_id=secret.id)
            assert saved_secret.name == secret.name

            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id


def test_update_user_secret_name_succeeds_if_exists_in_workspace():
    """Tests that the name of a user scoped secret can be changed if
    another workspace secret has the same name."""
    client = Client()
    store = client.zen_store

    with SecretContext(scope=SecretScope.USER) as secret:
        with SecretContext() as other_secret:
            saved_secret = store.get_secret(secret_id=secret.id)
            assert saved_secret.name == secret.name

            saved_secret = store.get_secret(secret_id=other_secret.id)
            assert saved_secret.name == other_secret.name

            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id

            with does_not_raise():
                updated_secret = store.update_secret(
                    secret_id=secret.id,
                    secret_update=SecretUpdateModel(
                        name=other_secret.name,
                    ),
                )

            assert updated_secret.name == other_secret.name

            saved_secret = store.get_secret(secret_id=secret.id)
            assert saved_secret.name == other_secret.name

            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 0

            all_secrets = store.list_secrets(
                SecretFilterModel(name=other_secret.name)
            ).items
            assert len(all_secrets) == 2
            assert secret.id in [s.id for s in all_secrets]
            assert other_secret.id in [s.id for s in all_secrets]

            all_secrets = store.list_secrets(
                SecretFilterModel(
                    name=other_secret.name, scope=SecretScope.USER
                )
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id

            all_secrets = store.list_secrets(
                SecretFilterModel(
                    name=other_secret.name, scope=SecretScope.WORKSPACE
                )
            ).items
            assert len(all_secrets) == 1
            assert other_secret.id == all_secrets[0].id


def test_update_workspace_secret_name_succeeds_if_exists_for_a_user():
    """Tests that the name of a workspace scoped secret can be changed if
    another user scoped secret has the same name."""
    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        with SecretContext(scope=SecretScope.USER) as other_secret:
            saved_secret = store.get_secret(secret_id=secret.id)
            assert saved_secret.name == secret.name

            saved_secret = store.get_secret(secret_id=other_secret.id)
            assert saved_secret.name == other_secret.name

            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id

            with does_not_raise():
                updated_secret = store.update_secret(
                    secret_id=secret.id,
                    secret_update=SecretUpdateModel(
                        name=other_secret.name,
                    ),
                )

            assert updated_secret.name == other_secret.name

            saved_secret = store.get_secret(secret_id=secret.id)
            assert saved_secret.name == other_secret.name

            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 0

            all_secrets = store.list_secrets(
                SecretFilterModel(name=other_secret.name)
            ).items
            assert len(all_secrets) == 2
            assert secret.id in [s.id for s in all_secrets]
            assert other_secret.id in [s.id for s in all_secrets]

            all_secrets = store.list_secrets(
                SecretFilterModel(
                    name=other_secret.name, scope=SecretScope.WORKSPACE
                )
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id

            all_secrets = store.list_secrets(
                SecretFilterModel(
                    name=other_secret.name, scope=SecretScope.USER
                )
            ).items
            assert len(all_secrets) == 1
            assert other_secret.id == all_secrets[0].id


def test_reusing_user_secret_name_succeeds():
    """Tests that the name of a user secret can be reused for another user
    secret."""
    if Client().zen_store.type == StoreType.SQL:
        pytest.skip("SQL Zen Stores do not support user switching.")

    client = Client()
    store = client.zen_store

    with SecretContext(scope=SecretScope.USER) as secret:
        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        user_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.USER,
                user_id=client.active_user.id,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        with UserContext(login=True):
            #  Client() needs to be instantiated here with the new
            #  logged-in user
            other_client = Client()
            other_store = other_client.zen_store

            with SecretContext(
                secret_name=secret.name, scope=SecretScope.USER
            ) as other_secret:
                all_secrets = other_store.list_secrets(
                    SecretFilterModel(name=secret.name),
                ).items
                assert len(all_secrets) == 2
                assert secret.id in [s.id for s in all_secrets]
                assert other_secret.id in [s.id for s in all_secrets]

                workspace_secrets = other_store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.WORKSPACE,
                        workspace_id=other_client.active_workspace.id,
                    )
                ).items
                assert len(workspace_secrets) == 0

                user_secrets = other_store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.USER,
                        user_id=other_client.active_user.id,
                        workspace_id=other_client.active_workspace.id,
                    ),
                ).items
                assert len(user_secrets) == 1
                assert other_secret.id == user_secrets[0].id

                user_secrets = other_store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.USER,
                        user_id=client.active_user.id,
                        workspace_id=client.active_workspace.id,
                    ),
                ).items
                assert len(user_secrets) == 1
                assert secret.id == user_secrets[0].id


def test_update_scope_succeeds():
    """Tests that the scope of a secret can be changed."""
    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.name == secret.name
        assert saved_secret.scope == SecretScope.WORKSPACE

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name, scope=SecretScope.WORKSPACE)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name, scope=SecretScope.USER)
        ).items
        assert len(all_secrets) == 0

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.WORKSPACE)
        ).items
        assert len(all_secrets) >= 1
        assert secret.id in [s.id for s in all_secrets]

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.USER)
        ).items
        assert secret.id not in [s.id for s in all_secrets]

        with does_not_raise():
            updated_secret = store.update_secret(
                secret_id=secret.id,
                secret_update=SecretUpdateModel(
                    scope=SecretScope.USER,
                ),
            )

        if _get_secrets_store_type() == SecretsStoreType.AWS:
            # The AWS secrets store returns before the secret is actually
            # updated in the backend, so we need to wait a bit before
            # running `list_secrets`.
            time.sleep(AWS_SECRET_REFRESH_SLEEP)

        assert updated_secret.name == secret.name
        assert updated_secret.scope == SecretScope.USER

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.name == secret.name
        assert saved_secret.scope == SecretScope.USER

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name, scope=SecretScope.WORKSPACE)
        ).items
        assert len(all_secrets) == 0

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name, scope=SecretScope.USER)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.WORKSPACE)
        ).items
        assert secret.id not in [s.id for s in all_secrets]

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.USER)
        ).items
        assert len(all_secrets) >= 1
        assert secret.id in [s.id for s in all_secrets]

        with does_not_raise():
            updated_secret = store.update_secret(
                secret_id=secret.id,
                secret_update=SecretUpdateModel(
                    scope=SecretScope.WORKSPACE,
                ),
            )

        if _get_secrets_store_type() == SecretsStoreType.AWS:
            # The AWS secrets store returns before the secret is actually
            # updated in the backend, so we need to wait a bit before
            # running `list_secrets`.
            time.sleep(AWS_SECRET_REFRESH_SLEEP)

        assert updated_secret.name == secret.name
        assert updated_secret.scope == SecretScope.WORKSPACE

        saved_secret = store.get_secret(secret_id=secret.id)
        assert saved_secret.name == secret.name
        assert saved_secret.scope == SecretScope.WORKSPACE

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name, scope=SecretScope.WORKSPACE)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name, scope=SecretScope.USER)
        ).items
        assert len(all_secrets) == 0

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.WORKSPACE)
        ).items
        assert len(all_secrets) >= 1
        assert secret.id in [s.id for s in all_secrets]

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.USER)
        ).items
        assert secret.id not in [s.id for s in all_secrets]


def test_update_scope_fails_if_name_already_in_scope():
    """Tests that the scope of a secret cannot be changed if another secret
    with the same name already exists in the target scope."""
    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        with SecretContext(
            secret_name=secret.name, scope=SecretScope.USER
        ) as other_secret:
            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 2
            assert secret.id in [s.id for s in all_secrets]
            assert other_secret.id in [s.id for s in all_secrets]

            all_secrets = store.list_secrets(
                SecretFilterModel(
                    name=secret.name, scope=SecretScope.WORKSPACE
                )
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id

            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name, scope=SecretScope.USER)
            ).items
            assert len(all_secrets) == 1
            assert other_secret.id == all_secrets[0].id

            with pytest.raises(EntityExistsError):
                store.update_secret(
                    secret_id=secret.id,
                    secret_update=SecretUpdateModel(
                        scope=SecretScope.USER,
                    ),
                )

            saved_secret = store.get_secret(secret_id=secret.id)
            assert saved_secret.name == secret.name
            assert saved_secret.scope == SecretScope.WORKSPACE

            with pytest.raises(EntityExistsError):
                store.update_secret(
                    secret_id=other_secret.id,
                    secret_update=SecretUpdateModel(
                        scope=SecretScope.WORKSPACE,
                    ),
                )

            saved_secret = store.get_secret(secret_id=other_secret.id)
            assert saved_secret.name == secret.name
            assert saved_secret.scope == SecretScope.USER


def test_workspace_secret_is_visible_to_other_users():
    """Tests that a workspace scoped secret is visible to other users in the same workspace."""
    if Client().zen_store.type == StoreType.SQL:
        pytest.skip("SQL Zen Stores do not support user switching.")

    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id
        workspace_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.WORKSPACE,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(workspace_secrets) == 1
        assert secret.id == workspace_secrets[0].id
        user_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.USER,
                user_id=client.active_user.id,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(user_secrets) == 0

        with UserContext(login=True):
            #  Client() needs to be instantiated here with the new
            #  logged-in user
            other_client = Client()
            other_store = other_client.zen_store

            all_secrets = other_store.list_secrets(
                SecretFilterModel(name=secret.name),
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id
            workspace_secrets = other_store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.WORKSPACE,
                    workspace_id=other_client.active_workspace.id,
                )
            ).items
            assert len(workspace_secrets) == 1
            assert secret.id == workspace_secrets[0].id
            user_secrets = other_store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.USER,
                    user_id=other_client.active_user.id,
                    workspace_id=other_client.active_workspace.id,
                ),
            ).items
            assert len(user_secrets) == 0


def test_user_secret_is_not_visible_to_other_users():
    """Tests that a user scoped secret is not visible to other users in the same workspace."""
    if Client().zen_store.type == StoreType.SQL:
        pytest.skip("SQL Zen Stores do not support user switching.")

    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id
        workspace_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.WORKSPACE,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(workspace_secrets) == 1
        assert secret.id == workspace_secrets[0].id
        user_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.USER,
                user_id=client.active_user.id,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(user_secrets) == 0

        # Create a user-scoped secret
        with SecretContext(
            scope=SecretScope.USER, secret_name=secret.name
        ) as user_secret:
            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 2
            assert secret.id in [s.id for s in all_secrets]
            assert user_secret.id in [s.id for s in all_secrets]
            workspace_secrets = store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.WORKSPACE,
                    workspace_id=client.active_workspace.id,
                )
            ).items
            assert len(workspace_secrets) == 1
            assert secret.id == workspace_secrets[0].id
            assert user_secret.id not in [s.id for s in workspace_secrets]
            user_secrets = store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.USER,
                    user_id=client.active_user.id,
                    workspace_id=client.active_workspace.id,
                )
            ).items
            assert len(user_secrets) == 1
            assert user_secret.id == user_secrets[0].id

            # Switch to a different user
            with UserContext(login=True):
                #  Client() needs to be instantiated here with the new
                #  logged-in user
                other_client = Client()
                other_store = other_client.zen_store

                all_secrets = other_store.list_secrets(
                    SecretFilterModel(name=secret.name)
                ).items
                assert len(all_secrets) == 2
                assert secret.id in [s.id for s in all_secrets]
                assert user_secret.id in [s.id for s in all_secrets]
                workspace_secrets = other_store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.WORKSPACE,
                        workspace_id=other_client.active_workspace.id,
                    )
                ).items
                assert len(workspace_secrets) == 1
                assert secret.id == workspace_secrets[0].id
                assert user_secret.id not in [s.id for s in workspace_secrets]
                user_secrets = other_store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.USER,
                        user_id=other_client.active_user.id,
                        workspace_id=other_client.active_workspace.id,
                    )
                ).items
                assert len(user_secrets) == 0


def test_workspace_secret_is_not_visible_to_other_workspaces():
    """Tests that a workspace scoped secret is not visible to other workspaces."""
    if Client().zen_store.type == StoreType.SQL:
        pytest.skip("SQL Zen Stores do not support user switching.")

    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id
        workspace_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.WORKSPACE,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(workspace_secrets) == 1
        assert secret.id == workspace_secrets[0].id
        user_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.USER,
                user_id=client.active_user.id,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(user_secrets) == 0

        with WorkspaceContext(activate=True):
            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id
            workspace_secrets = store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.WORKSPACE,
                    workspace_id=client.active_workspace.id,
                )
            ).items
            assert len(workspace_secrets) == 0
            user_secrets = store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.USER,
                    user_id=client.active_user.id,
                    workspace_id=client.active_workspace.id,
                )
            ).items
            assert len(user_secrets) == 0

            with SecretContext(secret_name=secret.name) as other_secret:
                all_secrets = store.list_secrets(
                    SecretFilterModel(name=secret.name)
                ).items
                assert len(all_secrets) == 2
                assert secret.id in [s.id for s in all_secrets]
                assert other_secret.id in [s.id for s in all_secrets]
                workspace_secrets = store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.WORKSPACE,
                        workspace_id=client.active_workspace.id,
                    )
                ).items
                assert len(workspace_secrets) == 1
                assert other_secret.id == workspace_secrets[0].id
                user_secrets = store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.USER,
                        user_id=client.active_user.id,
                        workspace_id=client.active_workspace.id,
                    )
                ).items
                assert len(user_secrets) == 0


def test_user_secret_is_not_visible_to_other_workspaces():
    """Tests that a user scoped secret is not visible to other workspaces."""
    if Client().zen_store.type == StoreType.SQL:
        pytest.skip("SQL Zen Stores do not support user switching.")

    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id
        workspace_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.WORKSPACE,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(workspace_secrets) == 1
        assert secret.id == workspace_secrets[0].id
        user_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.USER,
                user_id=client.active_user.id,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(user_secrets) == 0

        # Create a user-scoped secret
        with SecretContext(
            scope=SecretScope.USER, secret_name=secret.name
        ) as user_secret:
            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 2
            assert secret.id in [s.id for s in all_secrets]
            assert user_secret.id in [s.id for s in all_secrets]
            workspace_secrets = store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.WORKSPACE,
                    workspace_id=client.active_workspace.id,
                )
            ).items
            assert len(workspace_secrets) == 1
            assert secret.id == workspace_secrets[0].id
            assert user_secret.id not in [s.id for s in workspace_secrets]
            user_secrets = store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.USER,
                    user_id=client.active_user.id,
                    workspace_id=client.active_workspace.id,
                )
            ).items
            assert len(user_secrets) == 1
            assert user_secret.id == user_secrets[0].id

            with WorkspaceContext(activate=True) as workspace:
                all_secrets = store.list_secrets(
                    SecretFilterModel(name=secret.name)
                ).items
                assert len(all_secrets) == 2
                assert secret.id in [s.id for s in all_secrets]
                assert user_secret.id in [s.id for s in all_secrets]
                workspace_secrets = store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.WORKSPACE,
                        workspace_id=client.active_workspace.id,
                    )
                ).items
                assert len(workspace_secrets) == 0
                user_secrets = store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.USER,
                        user_id=client.active_user.id,
                        workspace_id=client.active_workspace.id,
                    )
                ).items
                assert len(user_secrets) == 0

                # Switch to a different user and activate the same workspace
                with UserContext(login=True):
                    with WorkspaceContext(workspace.name, activate=True):
                        #  Client() needs to be instantiated here with the new
                        #  logged-in user
                        other_client = Client()
                        other_store = other_client.zen_store

                        all_secrets = other_store.list_secrets(
                            SecretFilterModel(name=secret.name)
                        ).items
                        assert len(all_secrets) == 2
                        assert secret.id in [s.id for s in all_secrets]
                        assert user_secret.id in [s.id for s in all_secrets]
                        workspace_secrets = other_store.list_secrets(
                            SecretFilterModel(
                                name=secret.name,
                                scope=SecretScope.WORKSPACE,
                                workspace_id=other_client.active_workspace.id,
                            )
                        ).items
                        assert len(workspace_secrets) == 0
                        user_secrets = other_store.list_secrets(
                            SecretFilterModel(
                                name=secret.name,
                                scope=SecretScope.USER,
                                user_id=other_client.active_user.id,
                                workspace_id=other_client.active_workspace.id,
                            )
                        ).items
                        assert len(user_secrets) == 0


def test_list_secrets_filter():
    """Tests that listing secrets with various filters works"""
    client = Client()
    store = client.zen_store

    aria_secret_name = sample_name("arias-whiskers")
    axl_secret_name = sample_name("axls-whiskers")

    with SecretContext(
        secret_name=aria_secret_name
    ) as secret_one, SecretContext(
        secret_name=aria_secret_name, scope=SecretScope.USER
    ) as secret_two, SecretContext(
        secret_name=axl_secret_name
    ) as secret_three, SecretContext(
        secret_name=axl_secret_name, scope=SecretScope.USER
    ) as secret_four:
        all_secrets = store.list_secrets(SecretFilterModel()).items
        assert len(all_secrets) >= 4
        assert set(
            [secret_one.id, secret_two.id, secret_three.id, secret_four.id]
        ) <= set(s.id for s in all_secrets)

        all_secrets = store.list_secrets(
            SecretFilterModel(name=aria_secret_name)
        ).items
        assert len(all_secrets) == 2
        assert set([secret_one.id, secret_two.id]) == set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(name=axl_secret_name)
        ).items
        assert len(all_secrets) == 2
        assert set([secret_three.id, secret_four.id]) == set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(name="startswith:aria")
        ).items
        assert len(all_secrets) >= 2
        assert set([secret_one.id, secret_two.id]) <= set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(name="startswith:axl")
        ).items
        assert len(all_secrets) >= 2
        assert set([secret_three.id, secret_four.id]) <= set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(name="contains:whiskers")
        ).items
        assert len(all_secrets) >= 4
        assert set(
            [secret_one.id, secret_two.id, secret_three.id, secret_four.id]
        ) <= set(s.id for s in all_secrets)

        all_secrets = store.list_secrets(
            SecretFilterModel(name=f"endswith:{aria_secret_name[-5:]}")
        ).items
        assert len(all_secrets) == 2
        assert set([secret_one.id, secret_two.id]) == set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(name=f"endswith:{axl_secret_name[-5:]}")
        ).items
        assert len(all_secrets) == 2
        assert set([secret_three.id, secret_four.id]) == set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.WORKSPACE)
        ).items
        assert len(all_secrets) >= 2
        assert set([secret_one.id, secret_three.id]) <= set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.USER)
        ).items
        assert len(all_secrets) >= 2
        assert set([secret_two.id, secret_four.id]) <= set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(scope=SecretScope.USER)
        ).items
        assert len(all_secrets) >= 2
        assert set([secret_two.id, secret_four.id]) <= set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(
                name=aria_secret_name,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(all_secrets) == 2
        assert set([secret_one.id, secret_two.id]) == set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(
                name=axl_secret_name,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(all_secrets) == 2
        assert set([secret_three.id, secret_four.id]) == set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(
                name=aria_secret_name,
                workspace_id=client.active_workspace.id,
                user_id=client.active_user.id,
            )
        ).items
        assert len(all_secrets) == 2
        assert set([secret_one.id, secret_two.id]) == set(
            s.id for s in all_secrets
        )

        all_secrets = store.list_secrets(
            SecretFilterModel(
                name=axl_secret_name,
                workspace_id=client.active_workspace.id,
                user_id=client.active_user.id,
            )
        ).items
        assert len(all_secrets) == 2
        assert set([secret_three.id, secret_four.id]) == set(
            s.id for s in all_secrets
        )


def test_list_secrets_pagination_and_sorting():
    """Tests that listing secrets with various pagination and sorting settings works"""
    client = Client()
    store = client.zen_store

    suffix = sample_name("")

    with SecretContext(
        secret_name=f"arias-whiskers-{suffix}"
    ) as secret_one, SecretContext(
        secret_name=f"arias-spots-{suffix}",
        scope=SecretScope.USER,
    ) as secret_two, SecretContext(
        secret_name=f"axls-whiskers-{suffix}",
    ) as secret_three, SecretContext(
        secret_name=f"axls-spots-{suffix}",
        scope=SecretScope.USER,
    ) as secret_four:
        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
            )
        )
        assert len(secrets.items) == 4
        assert secrets.index == 1
        assert secrets.total_pages == 1
        assert secrets.total == 4

        assert set(
            [secret_one.id, secret_two.id, secret_three.id, secret_four.id]
        ) == set(s.id for s in secrets.items)

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=1,
                size=2,
                sort_by="asc:name",
            )
        )
        assert len(secrets.items) == 2
        assert secrets.index == 1
        assert secrets.total_pages == 2
        assert secrets.total == 4

        assert [secret_two.id, secret_one.id] == [s.id for s in secrets.items]

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=2,
                size=2,
                sort_by="asc:name",
            )
        )
        assert len(secrets.items) == 2
        assert secrets.index == 2
        assert secrets.total_pages == 2
        assert secrets.total == 4

        assert [secret_four.id, secret_three.id] == [
            s.id for s in secrets.items
        ]

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=1,
                size=2,
                sort_by="desc:name",
            )
        )
        assert len(secrets.items) == 2
        assert secrets.index == 1
        assert secrets.total_pages == 2
        assert secrets.total == 4

        assert [secret_three.id, secret_four.id] == [
            s.id for s in secrets.items
        ]

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=2,
                size=2,
                sort_by="desc:name",
            )
        )
        assert len(secrets.items) == 2
        assert secrets.index == 2
        assert secrets.total_pages == 2
        assert secrets.total == 4

        assert [secret_one.id, secret_two.id] == [s.id for s in secrets.items]

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=1,
                size=2,
                sort_by="asc:scope",
            )
        )
        assert len(secrets.items) == 2
        assert secrets.index == 1
        assert secrets.total_pages == 2
        assert secrets.total == 4

        assert {secret_two.id, secret_four.id} == {s.id for s in secrets.items}

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=2,
                size=2,
                sort_by="asc:scope",
            )
        )
        assert len(secrets.items) == 2
        assert secrets.index == 2
        assert secrets.total_pages == 2
        assert secrets.total == 4

        assert {secret_one.id, secret_three.id} == {
            s.id for s in secrets.items
        }

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=1,
                size=3,
                sort_by="asc:created",
            )
        )
        assert len(secrets.items) == 3
        assert secrets.index == 1
        assert secrets.total_pages == 2
        assert secrets.total == 4

        # NOTE: it's impossible to tell for sure which order these will be in,
        # because they could be created in less than one second and the
        # granularity of the sorting algorithm is one second, but we can at
        # least assert that they're all there
        page_one = [s.id for s in secrets.items]

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=2,
                size=3,
                sort_by="asc:created",
            )
        )
        assert len(secrets.items) == 1
        assert secrets.index == 2
        assert secrets.total_pages == 2
        assert secrets.total == 4

        page_two = [s.id for s in secrets.items]
        assert set(page_one + page_two) == {
            secret_one.id,
            secret_two.id,
            secret_three.id,
            secret_four.id,
        }

        # To give the updated time a chance to change
        time.sleep(1)

        secret_one = store.update_secret(
            secret_one.id,
            SecretUpdateModel(
                values={
                    "food": "birds",
                }
            ),
        )

        # To give the updated time a chance to change
        time.sleep(1)

        secret_two = store.update_secret(
            secret_two.id,
            SecretUpdateModel(
                values={
                    "food": "fish",
                }
            ),
        )

        if _get_secrets_store_type() == SecretsStoreType.AWS:
            # The AWS secrets store returns before the secret is actually
            # updated in the backend, so we need to wait a bit before
            # running `list_secrets`.
            time.sleep(AWS_SECRET_REFRESH_SLEEP)
        else:
            assert secret_one.updated > secret_one.created
            assert secret_two.updated > secret_two.created

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=1,
                size=2,
                sort_by="desc:updated",
            )
        )
        assert len(secrets.items) == 2
        assert secrets.index == 1
        assert secrets.total_pages == 2
        assert secrets.total == 4

        assert [
            secret_two.id,
            secret_one.id,
        ] == [s.id for s in secrets.items]

        secrets = store.list_secrets(
            SecretFilterModel(
                name=f"endswith:{suffix}",
                page=2,
                size=2,
                sort_by="desc:updated",
            )
        )
        assert len(secrets.items) == 2
        assert secrets.index == 2
        assert secrets.total_pages == 2
        assert secrets.total == 4

        # NOTE: the second page of secrets were never updated, so they have
        # almost the same updated time (under one second difference). We can't
        # assert that they're in a specific order, but we can assert that they
        # are all there
        assert {
            secret_four.id,
            secret_three.id,
        } == {s.id for s in secrets.items}

        secrets = store.list_secrets(
            SecretFilterModel(
                updated=f"gte:{secret_one.updated.strftime('%Y-%m-%d %H:%M:%S')}",
                page=1,
                size=10,
                sort_by="desc:name",
            )
        )

        assert len(secrets.items) == 2
        assert secrets.index == 1
        assert secrets.total_pages == 1
        assert secrets.total == 2

        assert [
            secret_one.id,
            secret_two.id,
        ] == [s.id for s in secrets.items]

        secrets = store.list_secrets(
            SecretFilterModel(
                created=f"gte:{secret_one.updated.strftime('%Y-%m-%d %H:%M:%S')}",
                page=1,
                size=10,
                sort_by="desc:name",
            )
        )

        assert len(secrets.items) == 0


def test_secret_values_cannot_be_accessed_by_readonly_user():
    """Tests that secret values cannot be retrieved by read-only users."""
    if Client().zen_store.type == StoreType.SQL:
        pytest.skip("SQL Zen Stores do not support user switching.")

    # Switch to a different user with read-write access
    password = random_str(32)
    with UserContext(password=password, login=True) as user:
        client = Client()
        store = client.zen_store

        # Create a workspace-scoped and user-scoped secret
        with SecretContext() as secret, SecretContext(
            scope=SecretScope.USER
        ) as user_secret:
            all_secrets = store.list_secrets(SecretFilterModel()).items
            assert len(all_secrets) >= 2
            assert secret.id in [s.id for s in all_secrets]
            assert user_secret.id in [s.id for s in all_secrets]
            workspace_secrets = store.list_secrets(
                SecretFilterModel(
                    scope=SecretScope.WORKSPACE,
                    workspace_id=client.active_workspace.id,
                )
            ).items
            assert len(workspace_secrets) >= 1
            assert secret.id in [s.id for s in workspace_secrets]

            saved_secret = store.get_secret(secret.id)
            assert saved_secret.secret_values == secret.secret_values
            assert all(v is not None for v in saved_secret.values.values())

            user_secrets = store.list_secrets(
                SecretFilterModel(
                    scope=SecretScope.USER,
                    user_id=client.active_user.id,
                    workspace_id=client.active_workspace.id,
                )
            ).items
            assert len(user_secrets) == 1
            assert user_secret.id == user_secrets[0].id

            saved_secret = store.get_secret(user_secrets[0].id)
            assert saved_secret.secret_values == user_secret.secret_values
            assert all(v is not None for v in saved_secret.values.values())

            # Remove the user's write access
            client.create_user_role_assignment(
                role_name_or_id="guest", user_name_or_id=user.id
            )
            admin_role = client.get_role("admin")
            role_assignment = client.list_user_role_assignment(
                user_id=user.id,
                role_id=admin_role.id,
            )
            assert len(role_assignment) == 1
            client.delete_user_role_assignment(role_assignment[0].id)

            # Re-authenticate with the updated user
            with UserContext(
                user_name=user.name, password=password, existing_user=True
            ):
                all_secrets = store.list_secrets(SecretFilterModel()).items
                assert len(all_secrets) >= 2
                assert secret.id in [s.id for s in all_secrets]
                assert user_secret.id in [s.id for s in all_secrets]
                workspace_secrets = store.list_secrets(
                    SecretFilterModel(
                        scope=SecretScope.WORKSPACE,
                        workspace_id=client.active_workspace.id,
                    )
                ).items
                assert len(workspace_secrets) >= 1
                assert secret.id in [s.id for s in workspace_secrets]

                saved_secret = store.get_secret(secret.id)
                assert set(saved_secret.values.keys()) == set(
                    secret.values.keys()
                )
                assert set(saved_secret.values.values()) == {None}

                user_secrets = store.list_secrets(
                    SecretFilterModel(
                        scope=SecretScope.USER,
                        user_id=client.active_user.id,
                        workspace_id=client.active_workspace.id,
                    )
                ).items
                assert len(user_secrets) == 1
                assert user_secret.id == user_secrets[0].id

                saved_secret = store.get_secret(user_secrets[0].id)
                assert set(saved_secret.values.values()) == {None}
                assert set(saved_secret.values.keys()) == set(
                    user_secret.values.keys()
                )


def test_secrets_cannot_be_created_or_updated_by_readonly_user():
    """Tests that secret values cannot be created or updated by read-only users."""
    if Client().zen_store.type == StoreType.SQL:
        pytest.skip("SQL Zen Stores do not support user switching.")

    # Switch to a different user with read-write access
    password = random_str(32)
    with UserContext(password=password, login=True) as user:
        client = Client()
        store = client.zen_store

        # Create a workspace-scoped and user-scoped secret
        with SecretContext() as secret, SecretContext(
            scope=SecretScope.USER
        ) as user_secret:
            with does_not_raise():
                store.update_secret(
                    secret.id, SecretUpdateModel(name=f"{secret.name}-new")
                )

            if _get_secrets_store_type() == SecretsStoreType.AWS:
                # The AWS secrets store returns before the secret is actually
                # updated in the backend, so we need to wait a bit before
                # running `list_secrets`.
                time.sleep(AWS_SECRET_REFRESH_SLEEP)

            old_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(old_secrets) == 0

            new_secrets = store.list_secrets(
                SecretFilterModel(name=f"{secret.name}-new")
            ).items
            assert len(new_secrets) == 1
            assert new_secrets[0].id == secret.id

            with does_not_raise():
                store.update_secret(
                    user_secret.id,
                    SecretUpdateModel(name=f"{user_secret.name}-new"),
                )

            if _get_secrets_store_type() == SecretsStoreType.AWS:
                # The AWS secrets store returns before the secret is actually
                # updated in the backend, so we need to wait a bit before
                # running `list_secrets`.
                time.sleep(AWS_SECRET_REFRESH_SLEEP)

            old_secrets = store.list_secrets(
                SecretFilterModel(name=user_secret.name)
            ).items
            assert len(old_secrets) == 0

            new_secrets = store.list_secrets(
                SecretFilterModel(name=f"{user_secret.name}-new")
            ).items
            assert len(new_secrets) == 1
            assert new_secrets[0].id == user_secret.id

            # Remove the user's write access
            client.create_user_role_assignment(
                role_name_or_id="guest", user_name_or_id=user.id
            )
            admin_role = client.get_role("admin")
            role_assignment = client.list_user_role_assignment(
                user_id=user.id,
                role_id=admin_role.id,
            )
            assert len(role_assignment) == 1
            client.delete_user_role_assignment(role_assignment[0].id)

            # Re-authenticate with the updated user
            with UserContext(
                user_name=user.name, password=password, existing_user=True
            ):
                new_client = Client()
                new_store = new_client.zen_store

                with pytest.raises(IllegalOperationError):
                    new_store.update_secret(
                        secret.id, SecretUpdateModel(name=f"{secret.name}")
                    )

                old_secrets = new_store.list_secrets(
                    SecretFilterModel(name=secret.name)
                ).items
                assert len(old_secrets) == 0

                new_secrets = new_store.list_secrets(
                    SecretFilterModel(name=f"{secret.name}-new")
                ).items
                assert len(new_secrets) == 1
                assert new_secrets[0].id == secret.id

                with pytest.raises(IllegalOperationError):
                    new_store.update_secret(
                        user_secret.id,
                        SecretUpdateModel(name=f"{user_secret.name}-new"),
                    )

                old_secrets = new_store.list_secrets(
                    SecretFilterModel(name=user_secret.name)
                ).items
                assert len(old_secrets) == 0

                new_secrets = new_store.list_secrets(
                    SecretFilterModel(name=f"{user_secret.name}-new")
                ).items
                assert len(new_secrets) == 1
                assert new_secrets[0].id == user_secret.id


def test_secret_is_deleted_with_workspace():
    """Tests that deleting a workspace automatically deletes all its secrets."""
    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id
        workspace_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.WORKSPACE,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(workspace_secrets) == 1
        assert secret.id == workspace_secrets[0].id

        with WorkspaceContext(activate=True) as workspace:
            all_secrets = store.list_secrets(
                SecretFilterModel(name=secret.name)
            ).items
            assert len(all_secrets) == 1
            assert secret.id == all_secrets[0].id
            workspace_secrets = store.list_secrets(
                SecretFilterModel(
                    name=secret.name,
                    scope=SecretScope.WORKSPACE,
                    workspace_id=workspace.id,
                )
            ).items
            assert len(workspace_secrets) == 0

            with SecretContext(secret_name=secret.name) as other_secret:
                with does_not_raise():
                    store.get_secret(other_secret.id)

                all_secrets = store.list_secrets(
                    SecretFilterModel(name=secret.name)
                ).items
                assert len(all_secrets) == 2
                assert secret.id in [s.id for s in all_secrets]
                assert other_secret.id in [s.id for s in all_secrets]
                workspace_secrets = store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.WORKSPACE,
                        workspace_id=workspace.id,
                    )
                ).items
                assert len(workspace_secrets) == 1
                assert other_secret.id == workspace_secrets[0].id

                store.delete_workspace(workspace.id)

                with pytest.raises(KeyError):
                    store.get_secret(other_secret.id)

                all_secrets = store.list_secrets(
                    SecretFilterModel(name=secret.name)
                ).items
                assert len(all_secrets) == 1
                assert secret.id == all_secrets[0].id
                all_workspace_secrets = store.list_secrets(
                    SecretFilterModel(
                        workspace_id=workspace.id,
                    )
                ).items
                assert len(all_workspace_secrets) == 0


def test_secret_is_deleted_with_user():
    """Tests that deleting a user automatically deletes all its secrets."""
    if Client().zen_store.type == StoreType.SQL:
        pytest.skip("SQL Zen Stores do not support user switching.")

    client = Client()
    store = client.zen_store

    with SecretContext() as secret:
        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name)
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id
        workspace_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.WORKSPACE,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(workspace_secrets) == 1
        assert secret.id == workspace_secrets[0].id
        user_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.USER,
                user_id=client.active_user.id,
                workspace_id=client.active_workspace.id,
            )
        ).items
        assert len(user_secrets) == 0

        with UserContext(login=True) as user:
            #  Client() needs to be instantiated here with the new
            #  logged-in user
            other_client = Client()
            other_store = other_client.zen_store

            with SecretContext(
                secret_name=secret.name, scope=SecretScope.USER, delete=False
            ) as other_secret:
                with does_not_raise():
                    other_store.get_secret(other_secret.id)

                all_secrets = other_store.list_secrets(
                    SecretFilterModel(name=secret.name),
                ).items
                assert len(all_secrets) == 2
                assert secret.id in [s.id for s in all_secrets]
                assert other_secret.id in [s.id for s in all_secrets]

                user_secrets = other_store.list_secrets(
                    SecretFilterModel(
                        name=secret.name,
                        scope=SecretScope.USER,
                        user_id=user.id,
                        workspace_id=client.active_workspace.id,
                    ),
                ).items
                assert len(user_secrets) == 1
                assert other_secret.id == user_secrets[0].id

        # New user has been deleted at this point

        with pytest.raises(KeyError):
            store.get_secret(other_secret.id)

        all_secrets = store.list_secrets(
            SecretFilterModel(name=secret.name),
        ).items
        assert len(all_secrets) == 1
        assert secret.id == all_secrets[0].id

        user_secrets = store.list_secrets(
            SecretFilterModel(
                name=secret.name,
                scope=SecretScope.USER,
                user_id=user.id,
                workspace_id=client.active_workspace.id,
            ),
        ).items
        assert len(user_secrets) == 0
