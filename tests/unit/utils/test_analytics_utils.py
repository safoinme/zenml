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
from contextlib import ExitStack as does_not_raise
from types import TracebackType
from typing import Dict, Optional, Type
from unittest.mock import patch
from uuid import UUID

from pytest_mock import MockFixture

from zenml.enums import StackComponentType, StoreType
from zenml.utils.analytics_utils import (
    AnalyticsEvent,
    get_segment_key,
    track_event,
)


def event_check(
    user_id: str, event: AnalyticsEvent, metadata: Dict[str, str]
) -> None:
    """Mock function to replace the 'analytics.track' function for tests.

    By utilizing this mock function, we can validate the inputs given to
    actual track function.

    Args:
        user_id: the string representation of the client id
        event: the type of the event
        metadata: the collection of metadata describing the event

    Raises:
        ...
    """
    # Check whether the user id corresponds to the client id
    from zenml.config.global_config import GlobalConfiguration

    gc = GlobalConfiguration()
    assert user_id == str(gc.user_id)

    # Check the validity of the event
    assert event in AnalyticsEvent.__members__.values()

    # Check the type of each metadata entry
    assert all([not isinstance(v, UUID) for v in metadata.values()])

    # Check whether common parameters are included in the metadata
    assert "environment" in metadata
    assert "python_version" in metadata
    assert "version" in metadata
    assert "event_success" in metadata

    from zenml.client import Client

    client = Client()

    if event == AnalyticsEvent.REGISTERED_STACK:

        assert "user_id" in metadata
        assert metadata["user_id"] == str(client.active_user.id)

        assert "project_id" in metadata
        assert metadata["project_id"] == str(client.active_project.id)

        assert "entity_id" in metadata

        assert StackComponentType.ARTIFACT_STORE in metadata
        assert StackComponentType.ORCHESTRATOR in metadata
        assert "is_shared" in metadata

    if event == AnalyticsEvent.REGISTERED_STACK_COMPONENT:
        assert "user_id" in metadata
        assert metadata["user_id"] == str(client.active_user.id)

        assert "type" in metadata
        assert metadata["type"] in StackComponentType.__members__.values()

        assert "flavor" in metadata
        assert "entity_id" in metadata
        assert "is_shared" in metadata

    if event == AnalyticsEvent.RUN_PIPELINE:
        assert "store_type" in metadata
        assert metadata["store_type"] in StoreType.__members__.values()

        assert "artifact_store" in metadata
        assert (
            metadata["artifact_store"]
            == client.active_stack_model.components[
                StackComponentType.ARTIFACT_STORE
            ][0].flavor
        )

        assert "orchestrator" in metadata
        assert (
            metadata["orchestrator"]
            == client.active_stack_model.components[
                StackComponentType.ORCHESTRATOR
            ][0].flavor
        )


def event_context_exit(
    _,
    exc_type: Optional[Type[BaseException]],
    exc_val: Optional[BaseException],
    exc_tb: Optional[TracebackType],
):
    """Mock exit function to replace the exit method of the AnalyticsContext.

    Normally, the analytics context has an exit function which allows the main
    thread to continue by suppressing exceptions which occur during the event
    tracking. However, for the sake of the tests we would like to disable this
    behaviour, so we can catch the errors which happen during this process.
    """


@patch.dict(
    "os.environ", {"ZENML_DEBUG": "true", "ZENML_ANALYTICS_OPT_IN": "true"}
)
def test_analytics_event(
    mocker: MockFixture, clean_client, one_step_pipeline, empty_step
) -> None:
    """Checks whether the event sent for analytics has the right properties.

    This is achieved by modifying the behaviour of several functionalities
    within the analytics process:

        1 - The environmental variables are patched to set the "ZENML_DEBUG"
            and "ZENML_ANALYTICS_OPT_IN" to true. This way, the process to send
            analytics events is activated. ("ZENML_DEBUG" is only set as a
            security measure.)
        2 - The function "analytics.track" which is responsible for sending
            the actual analytics events is also patched with a different
            function. This way, we stop sending any actual events during the
            test and have a platform to check the validity of the final
            attributes which get passed to it.
        3 - Finally, the exit function of our AnalyticsContext is also
            patched. In a normal workflow, this context manager is responsible
            for keeping the main thread alive by suppressing any exceptions
            which might happen during the preparation/tracking of any events.
            However, since we want to test the attributes, this method needs to
            be disabled with a dummy method, so that we can catch any errors
            that happen during the check.

    Once the patches are set, we can execute any events such as `initializing
    zenml`, `registering stacks` or `registering stack components` and check
    the validity of the corresponding event and metadata.
    """

    mocker.patch("analytics.track", new=event_check)
    mocker.patch(
        "zenml.utils.analytics_utils.AnalyticsContext.__exit__",
        new=event_context_exit,
    )

    # Test zenml initialization
    clean_client.initialize()

    # Test stack and component registration
    clean_client.create_stack_component(
        name="new_artifact_store",
        flavor="local",
        component_type=StackComponentType.ARTIFACT_STORE,
        configuration={"path": "/tmp/path/for/test"},
    )
    clean_client.create_stack(
        name="new_stack",
        components={
            StackComponentType.ARTIFACT_STORE: "new_artifact_store",
            StackComponentType.ORCHESTRATOR: "default",
        },
    )

    # Test pipeline run
    one_step_pipeline(empty_step()).run(unlisted=True)


def test_get_segment_key():
    """Checks the get_segment_key method returns a value."""
    with does_not_raise():
        get_segment_key()


def test_track_event_conditions():
    """It should return true for the analytics events but false for everything else."""
    assert track_event(AnalyticsEvent.OPT_IN_ANALYTICS)
    assert track_event(AnalyticsEvent.OPT_OUT_ANALYTICS)
    assert not track_event(AnalyticsEvent.EVENT_TEST)
