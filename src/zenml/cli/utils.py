#  Copyright (c) ZenML GmbH 2020. All Rights Reserved.
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
"""Utility functions for the CLI."""

import json
import os
import subprocess
import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    NoReturn,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

import click
from pydantic import BaseModel
from rich import box, table
from rich.markup import escape
from rich.prompt import Confirm
from rich.style import Style

from zenml.config.global_config import GlobalConfiguration
from zenml.console import console, zenml_style_defaults
from zenml.constants import IS_DEBUG_ENV
from zenml.enums import StackComponentType, StoreType
from zenml.logger import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from rich.text import Text

    from zenml.client import Client
    from zenml.enums import ExecutionStatus
    from zenml.integrations.integration import Integration
    from zenml.model_deployers import BaseModelDeployer
    from zenml.models import (
        ComponentModel,
        FlavorModel,
        HydratedComponentModel,
        HydratedStackModel,
        PipelineRunModel,
        StackModel,
    )
    from zenml.secret import BaseSecretSchema
    from zenml.services import BaseService, ServiceState
    from zenml.zen_server.deploy.deployment import ServerDeployment

MAX_ARGUMENT_VALUE_SIZE = 10240


def title(text: str) -> None:
    """Echo a title formatted string on the CLI.

    Args:
        text: Input text string.
    """
    console.print(text.upper(), style=zenml_style_defaults["title"])


def confirmation(text: str, *args: Any, **kwargs: Any) -> bool:
    """Echo a confirmation string on the CLI.

    Args:
        text: Input text string.
        *args: Args to be passed to click.confirm().
        **kwargs: Kwargs to be passed to click.confirm().

    Returns:
        Boolean based on user response.
    """
    return Confirm.ask(text, console=console)


def declare(
    text: Union[str, "Text"],
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    **kwargs: Any,
) -> None:
    """Echo a declaration on the CLI.

    Args:
        text: Input text string.
        bold: Optional boolean to bold the text.
        italic: Optional boolean to italicize the text.
        **kwargs: Optional kwargs to be passed to console.print().
    """
    base_style = zenml_style_defaults["info"]
    style = Style.chain(base_style, Style(bold=bold, italic=italic))
    console.print(text, style=style, **kwargs)


def error(text: str) -> NoReturn:
    """Echo an error string on the CLI.

    Args:
        text: Input text string.

    Raises:
        ClickException: when called.
    """
    raise click.ClickException(message=click.style(text, fg="red", bold=True))


def warning(
    text: str,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    **kwargs: Any,
) -> None:
    """Echo a warning string on the CLI.

    Args:
        text: Input text string.
        bold: Optional boolean to bold the text.
        italic: Optional boolean to italicize the text.
        **kwargs: Optional kwargs to be passed to console.print().
    """
    base_style = zenml_style_defaults["warning"]
    style = Style.chain(base_style, Style(bold=bold, italic=italic))
    console.print(text, style=style, **kwargs)


def print_table(obj: List[Dict[str, Any]], **columns: table.Column) -> None:
    """Prints the list of dicts in a table format.

    The input object should be a List of Dicts. Each item in that list represent
    a line in the Table. Each dict should have the same keys. The keys of the
    dict will be used as headers of the resulting table.

    Args:
        obj: A List containing dictionaries.
        columns: Optional column configurations to be used in the table.
    """
    column_keys = {key: None for dict_ in obj for key in dict_}
    column_names = [columns.get(key, key.upper()) for key in column_keys]
    rich_table = table.Table(box=box.HEAVY_EDGE, show_lines=True)
    for col_name in column_names:
        if isinstance(col_name, str):
            rich_table.add_column(str(col_name), overflow="fold")
        else:
            rich_table.add_column(str(col_name.header).upper(), overflow="fold")
    for dict_ in obj:
        values = []
        for key in column_keys:
            if key is None:
                values.append(None)
            else:
                value = str(dict_.get(key) or " ")
                # escape text when square brackets are used
                if "[" in value:
                    value = escape(value)
                values.append(value)
        rich_table.add_row(*values)
    if len(rich_table.columns) > 1:
        rich_table.columns[0].justify = "center"
    console.print(rich_table)


M = TypeVar("M", bound=BaseModel)


def print_pydantic_models(
    models: Sequence[M],
    columns: Optional[Sequence[str]] = None,
    exclude_columns: Sequence[str] = (),
    is_active: Optional[Callable[[M], bool]] = None,
) -> None:
    """Prints the list of Pydantic models in a table.

    Args:
        models: List of Pydantic models that will be represented as a row in
            the table.
        columns: Optionally specify subset and order of columns to display.
        exclude_columns: Optionally specify columns to exclude. (Note: `columns`
            takes precedence over `exclude_columns`.)
        is_active: Optional function that marks as row as active.

    """

    def __dictify(model: M) -> Dict[str, str]:
        """Helper function to map over the list to turn Models into dicts.

        Args:
            model: Pydantic model.

        Returns:
            Dict of model attributes.
        """
        items = (
            {
                key: str(value)
                for key, value in model.dict().items()
                if key not in exclude_columns
            }
            if columns is None
            else {key: str(model.dict()[key]) for key in columns}
        )
        # prepend an active marker if a function to mark active was passed
        marker = "active"
        if marker in items:
            marker = "current"
        return (
            {marker: ":point_right:" if is_active(model) else "", **items}
            if is_active is not None
            else items
        )

    print_table([__dictify(model) for model in models])


def format_integration_list(
    integrations: List[Tuple[str, Type["Integration"]]]
) -> List[Dict[str, str]]:
    """Formats a list of integrations into a List of Dicts.

    This list of dicts can then be printed in a table style using
    cli_utils.print_table.

    Args:
        integrations: List of tuples containing the name of the integration and
            the integration metadata.

    Returns:
        List of Dicts containing the name of the integration and the integration
    """
    list_of_dicts = []
    for name, integration_impl in integrations:
        is_installed = integration_impl.check_installation()
        list_of_dicts.append(
            {
                "INSTALLED": ":white_check_mark:" if is_installed else ":x:",
                "INTEGRATION": name,
                "REQUIRED_PACKAGES": ", ".join(integration_impl.REQUIREMENTS),
            }
        )
    return list_of_dicts


def print_stack_configuration(
    stack: "HydratedStackModel", active: bool
) -> None:
    """Prints the configuration options of a stack.

    Args:
        stack: Instance of a stack model.
        active: Whether the stack is active.
    """
    stack_caption = f"'{stack.name}' stack"
    if active:
        stack_caption += " (ACTIVE)"
    rich_table = table.Table(
        box=box.HEAVY_EDGE,
        title="Stack Configuration",
        caption=stack_caption,
        show_lines=True,
    )
    rich_table.add_column("COMPONENT_TYPE", overflow="fold")
    rich_table.add_column("COMPONENT_NAME", overflow="fold")
    for component_type, components in stack.components.items():
        rich_table.add_row(component_type, components[0].name)

    # capitalize entries in first column
    rich_table.columns[0]._cells = [
        component.upper()  # type: ignore[union-attr]
        for component in rich_table.columns[0]._cells
    ]
    console.print(rich_table)
    declare(
        f"Stack '{stack.name}' with id '{stack.id}' is owned by "
        f"user '{stack.user.name}' and is "
        f"'{'shared' if stack.is_shared else 'private'}'."
    )


def print_flavor_list(flavors: List["FlavorModel"]) -> None:
    """Prints the list of flavors.

    Args:
        flavors: List of flavors to print.
    """
    flavor_table = []
    for f in flavors:
        flavor_table.append(
            {
                "FLAVOR": f.name,
                "INTEGRATION": f.integration,
                "SOURCE": f.source,
            }
        )

    print_table(flavor_table)


def print_stack_component_configuration(
    component: "HydratedComponentModel", active_status: bool
) -> None:
    """Prints the configuration options of a stack component.

    Args:
        component: The stack component to print.
        active_status: Whether the stack component is active.
    """
    declare(
        f"{component.type.value.title()} '{component.name}' of flavor "
        f"'{component.flavor}' with id '{component.id}' is owned by "
        f"user '{component.user.name}' and is "
        f"'{'shared' if component.is_shared else 'private'}'."
    )

    if len(component.configuration) == 0:
        declare("No configuration options are set for this component.")
        return

    title_ = (
        f"'{component.name}' {component.type.value.upper()} "
        f"Component Configuration"
    )

    if active_status:
        title_ += " (ACTIVE)"
    rich_table = table.Table(
        box=box.HEAVY_EDGE,
        title=title_,
        show_lines=True,
    )
    rich_table.add_column("COMPONENT_PROPERTY")
    rich_table.add_column("VALUE", overflow="fold")

    component_dict = component.dict()
    component_dict.pop("configuration")
    component_dict.update(component.configuration)

    items = component.configuration.items()
    for item in items:
        elements = []
        for idx, elem in enumerate(item):
            if idx == 0:
                elements.append(f"{elem.upper()}")
            else:
                elements.append(str(elem))
        rich_table.add_row(*elements)

    console.print(rich_table)


def print_active_config() -> None:
    """Print the active configuration."""
    from zenml.client import Client

    gc = GlobalConfiguration()
    client = Client()

    # We use gc.store here instead of client.zen_store for two reasons:
    # 1. to avoid initializing ZenML with the default store just because we want
    # to print the active config
    # 2. to avoid connecting to the active store and keep this call lightweight
    if not gc.store:
        return

    if gc.uses_default_store():
        declare("Using the default local database.")
    elif gc.store.type == StoreType.SQL:
        declare(f"Using the SQL database: '{gc.store.url}'.")
    elif gc.store.type == StoreType.REST:
        declare(f"Connected to the ZenML server: '{gc.store.url}'")
    if gc.active_project_name:
        scope = "repository" if client.uses_local_configuration else "global"
        declare(
            f"Running with active project: '{gc.active_project_name}' "
            f"({scope})"
        )


def print_active_stack() -> None:
    """Print active stack."""
    from zenml.client import Client

    client = Client()
    scope = "repository" if client.uses_local_configuration else "global"
    declare(
        f"Running with active stack: '{client.active_stack_model.name}' "
        f"({scope})"
    )


def expand_argument_value_from_file(name: str, value: str) -> str:
    """Expands the value of an argument pointing to a file into the contents of that file.

    Args:
        name: Name of the argument. Used solely for logging purposes.
        value: The value of the argument. This is to be interpreted as a
            filename if it begins with a `@` character.

    Returns:
        The argument value expanded into the contents of the file, if the
        argument value begins with a `@` character. Otherwise, the argument
        value is returned unchanged.

    Raises:
        ValueError: If the argument value points to a file that doesn't exist,
            that cannot be read, or is too long(i.e. exceeds
            `MAX_ARGUMENT_VALUE_SIZE` bytes).
    """
    if value.startswith("@@"):
        return value[1:]
    if not value.startswith("@"):
        return value
    filename = os.path.abspath(os.path.expanduser(value[1:]))
    logger.info(
        f"Expanding argument value `{name}` to contents of file `{filename}`."
    )
    if not os.path.isfile(filename):
        raise ValueError(
            f"Could not load argument '{name}' value: file "
            f"'{filename}' does not exist or is not readable."
        )
    try:
        if os.path.getsize(filename) > MAX_ARGUMENT_VALUE_SIZE:
            raise ValueError(
                f"Could not load argument '{name}' value: file "
                f"'{filename}' is too large (max size is "
                f"{MAX_ARGUMENT_VALUE_SIZE} bytes)."
            )

        with open(filename, "r") as f:
            return f.read()
    except OSError as e:
        raise ValueError(
            f"Could not load argument '{name}' value: file "
            f"'{filename}' could not be accessed: {str(e)}"
        )


def parse_name_and_extra_arguments(
    args: List[str],
    expand_args: bool = False,
    name_mandatory: bool = True,
) -> Tuple[Optional[str], Dict[str, str]]:
    """Parse a name and extra arguments from the CLI.

    This is a utility function used to parse a variable list of optional CLI
    arguments of the form `--key=value` that must also include one mandatory
    free-form name argument. There is no restriction as to the order of the
    arguments.

    Examples:
        >>> parse_name_and_extra_arguments(['foo']])
        ('foo', {})
        >>> parse_name_and_extra_arguments(['foo', '--bar=1'])
        ('foo', {'bar': '1'})
        >>> parse_name_and_extra_arguments('--bar=1', 'foo', '--baz=2'])
        ('foo', {'bar': '1', 'baz': '2'})
        >>> parse_name_and_extra_arguments(['--bar=1'])
        Traceback (most recent call last):
            ...
            ValueError: Missing required argument: name

    Args:
        args: A list of command line arguments from the CLI.
        expand_args: Whether to expand argument values into the contents of the
            files they may be pointing at using the special `@` character.
        name_mandatory: Whether the name argument is mandatory.

    Returns:
        The name and a dict of parsed args.
    """
    name: Optional[str] = None
    # The name was not supplied as the first argument, we have to
    # search the other arguments for the name.
    for i, arg in enumerate(args):
        if arg.startswith("--"):
            continue
        name = args.pop(i)
        break
    else:
        if name_mandatory:
            error(
                "A name must be supplied. Please see the command help for more "
                "information."
            )

    message = (
        "Please provide args with a proper "
        "identifier as the key and the following structure: "
        '--custom_argument="value"'
    )
    args_dict: Dict[str, str] = {}
    for a in args:
        if not a.startswith("--") or "=" not in a:
            error(f"Invalid argument: '{a}'. {message}")
        key, value = a[2:].split("=", maxsplit=1)
        if not key.isidentifier():
            error(f"Invalid argument: '{a}'. {message}")
        args_dict[key] = value

    if expand_args:
        args_dict = {
            k: expand_argument_value_from_file(k, v)
            for k, v in args_dict.items()
        }

    return name, args_dict


def parse_unknown_component_attributes(args: List[str]) -> List[str]:
    """Parse unknown options from the CLI.

    Args:
        args: A list of strings from the CLI.

    Returns:
        List of parsed args.
    """
    warning_message = (
        "Please provide args with a proper "
        "identifier as the key and the following structure: "
        "--custom_attribute"
    )

    assert all(a.startswith("--") for a in args), warning_message
    p_args = [a.lstrip("-") for a in args]
    assert all(v.isidentifier() for v in p_args), warning_message
    return p_args


def install_packages(packages: List[str]) -> None:
    """Installs pypi packages into the current environment with pip.

    Args:
        packages: List of packages to install.
    """
    command = [sys.executable, "-m", "pip", "install"] + packages

    if not IS_DEBUG_ENV:
        command += [
            "-qqq",
            "--no-warn-conflicts",
        ]

    subprocess.check_call(command)


def uninstall_package(package: str) -> None:
    """Uninstalls pypi package from the current environment with pip.

    Args:
        package: The package to uninstall.
    """
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "uninstall",
            "-qqq",
            "-y",
            package,
        ]
    )


def pretty_print_secret(
    secret: "BaseSecretSchema", hide_secret: bool = True
) -> None:
    """Given a secret set, print all key-value pairs associated with the secret.

    Args:
        secret: Secret of type BaseSecretSchema
        hide_secret: boolean that configures if the secret values are shown
            on the CLI
    """

    def get_secret_value(value: Any) -> str:
        if value is None:
            return ""
        if hide_secret:
            return "***"
        return str(value)

    stack_dicts = [
        {
            "SECRET_KEY": key,
            "SECRET_VALUE": get_secret_value(value),
        }
        for key, value in secret.content.items()
    ]
    print_table(stack_dicts)


def print_list_items(list_items: List[str], column_title: str) -> None:
    """Prints the configuration options of a stack.

    Args:
        list_items: List of items
        column_title: Title of the column
    """
    rich_table = table.Table(
        box=box.HEAVY_EDGE,
        show_lines=True,
    )
    rich_table.add_column(column_title.upper(), overflow="fold")
    list_items.sort()
    for item in list_items:
        rich_table.add_row(item)

    console.print(rich_table)


def get_service_state_emoji(state: "ServiceState") -> str:
    """Get the rich emoji representing the operational state of a Service.

    Args:
        state: Service state to get emoji for.

    Returns:
        String representing the emoji.
    """
    from zenml.services.service_status import ServiceState

    if state == ServiceState.ACTIVE:
        return ":white_check_mark:"
    if state == ServiceState.INACTIVE:
        return ":pause_button:"
    if state == ServiceState.ERROR:
        return ":heavy_exclamation_mark:"
    return ":hourglass_not_done:"


def pretty_print_model_deployer(
    model_services: List["BaseService"], model_deployer: "BaseModelDeployer"
) -> None:
    """Given a list of served_models, print all associated key-value pairs.

    Args:
        model_services: list of model deployment services
        model_deployer: Active model deployer
    """
    model_service_dicts = []
    for model_service in model_services:
        served_model_info = model_deployer.get_model_server_info(model_service)
        dict_uuid = str(model_service.uuid)
        dict_pl_name = model_service.config.pipeline_name
        dict_pl_stp_name = model_service.config.pipeline_step_name
        dict_model_name = served_model_info.get("MODEL_NAME", "")
        model_service_dicts.append(
            {
                "STATUS": get_service_state_emoji(model_service.status.state),
                "UUID": dict_uuid,
                "PIPELINE_NAME": dict_pl_name,
                "PIPELINE_STEP_NAME": dict_pl_stp_name,
                "MODEL_NAME": dict_model_name,
            }
        )
    print_table(
        model_service_dicts, UUID=table.Column(header="UUID", min_width=36)
    )


def print_served_model_configuration(
    model_service: "BaseService", model_deployer: "BaseModelDeployer"
) -> None:
    """Prints the configuration of a model_service.

    Args:
        model_service: Specific service instance to
        model_deployer: Active model deployer
    """
    title_ = f"Properties of Served Model {model_service.uuid}"

    rich_table = table.Table(
        box=box.HEAVY_EDGE,
        title=title_,
        show_lines=True,
    )
    rich_table.add_column("MODEL SERVICE PROPERTY", overflow="fold")
    rich_table.add_column("VALUE", overflow="fold")

    # Get implementation specific info
    served_model_info = model_deployer.get_model_server_info(model_service)

    served_model_info = {
        **served_model_info,
        "UUID": str(model_service.uuid),
        "STATUS": get_service_state_emoji(model_service.status.state),
        "STATUS_MESSAGE": model_service.status.last_error,
        "PIPELINE_NAME": model_service.config.pipeline_name,
        "PIPELINE_RUN_ID": model_service.config.pipeline_run_id,
        "PIPELINE_STEP_NAME": model_service.config.pipeline_step_name,
    }

    # Sort fields alphabetically
    sorted_items = {k: v for k, v in sorted(served_model_info.items())}

    for item in sorted_items.items():
        rich_table.add_row(*[str(elem) for elem in item])

    # capitalize entries in first column
    rich_table.columns[0]._cells = [
        component.upper()  # type: ignore[union-attr]
        for component in rich_table.columns[0]._cells
    ]
    console.print(rich_table)


def print_server_deployment_list(servers: List["ServerDeployment"]) -> None:
    """Print a table with a list of ZenML server deployments.

    Args:
        servers: list of ZenML server deployments
    """
    server_dicts = []
    for server in servers:
        status = ""
        url = ""
        connected = ""
        if server.status:
            status = get_service_state_emoji(server.status.status)
            if server.status.url:
                url = server.status.url
            if server.status.connected:
                connected = ":point_left:"
        server_dicts.append(
            {
                "STATUS": status,
                "NAME": server.config.name,
                "PROVIDER": server.config.provider.value,
                "URL": url,
                "CONNECTED": connected,
            }
        )
    print_table(server_dicts)


def print_server_deployment(server: "ServerDeployment") -> None:
    """Prints the configuration and status of a ZenML server deployment.

    Args:
        server: Server deployment to print
    """
    server_name = server.config.name
    title_ = f"ZenML server '{server_name}'"

    rich_table = table.Table(
        box=box.HEAVY_EDGE,
        title=title_,
        show_header=False,
        show_lines=True,
    )
    rich_table.add_column("", overflow="fold")
    rich_table.add_column("", overflow="fold")

    server_info = []

    if server.status:
        server_info.extend(
            [
                ("URL", server.status.url or ""),
                ("STATUS", get_service_state_emoji(server.status.status)),
                ("STATUS_MESSAGE", server.status.status_message or ""),
                (
                    "CONNECTED",
                    ":white_check_mark:" if server.status.connected else "",
                ),
            ]
        )

    for item in server_info:
        rich_table.add_row(*item)

    console.print(rich_table)


def describe_pydantic_object(schema_json: str) -> None:
    """Describes a Pydantic object based on the json of its schema.

    Args:
        schema_json: str, represents the schema of a Pydantic object, which
            can be obtained through BaseModelClass.schema_json()
    """
    # Get the schema dict
    schema = json.loads(schema_json)

    # Extract values with defaults
    schema_title = schema["title"]
    required = schema.get("required", [])
    description = schema.get("description", "")
    properties = schema.get("properties", {})

    # Pretty print the schema
    warning(f"Configuration class: {schema_title}\n", bold=True)

    if description:
        declare(f"{description}\n")

    if properties:
        warning("Properties", bold=True)
        for prop, prop_schema in properties.items():
            warning(
                f"{prop}, {prop_schema['type']}"
                f"{', REQUIRED' if prop in required else ''}"
            )

            if "description" in prop_schema:
                declare(f"  {prop_schema['description']}", width=80)


def get_stack_by_id_or_name_or_prefix(
    client: "Client",
    id_or_name_or_prefix: str,
) -> "StackModel":
    """Fetches a stack within active project using the name, id or partial id.

    Args:
        client: Instance of the Repository singleton
        id_or_name_or_prefix: The id, name or partial id of the stack to
                              fetch.

    Returns:
        The stack with the given name.

    Raises:
        KeyError: If no stack with the given name exists.
    """
    # First interpret as full UUID
    try:
        stack_id = UUID(id_or_name_or_prefix)
        return client.zen_store.get_stack(stack_id)
    except ValueError:
        pass

    user_only_stacks = cast(
        List["StackModel"],
        client.zen_store.list_stacks(
            project_name_or_id=client.active_project.name,
            name=id_or_name_or_prefix,
            user_name_or_id=client.active_user.name,
            is_shared=False,
        ),
    )

    shared_stacks = cast(
        List["StackModel"],
        client.zen_store.list_stacks(
            project_name_or_id=client.active_project.name,
            name=id_or_name_or_prefix,
            is_shared=True,
        ),
    )

    named_stacks = user_only_stacks + shared_stacks

    if len(named_stacks) > 1:
        hydrated_name_stacks = [s.to_hydrated_model() for s in named_stacks]
        print_stacks_table(client=client, stacks=hydrated_name_stacks)
        error(
            f"Multiple stacks have been found for name "
            f"'{id_or_name_or_prefix}'. The stacks listed above all share "
            f"this name. Please specify the stack by full or partial id."
        )

    elif len(named_stacks) == 1:
        return named_stacks[0]
    else:
        logger.debug(
            f"No stack with name '{id_or_name_or_prefix}' "
            f"exists. Trying to resolve as partial_id"
        )

        user_only_stacks = cast(
            List["StackModel"],
            client.zen_store.list_stacks(
                project_name_or_id=client.active_project.name,
                user_name_or_id=client.active_user.name,
                is_shared=False,
            ),
        )

        shared_stacks = cast(
            List["StackModel"],
            client.zen_store.list_stacks(
                project_name_or_id=client.active_project.name,
                is_shared=True,
            ),
        )

        all_stacks = user_only_stacks + shared_stacks

        filtered_stacks = [
            stack
            for stack in all_stacks
            if str(stack.id).startswith(id_or_name_or_prefix)
        ]
        if len(filtered_stacks) > 1:
            hydrated_all_stacks = [s.to_hydrated_model() for s in all_stacks]
            print_stacks_table(client=client, stacks=hydrated_all_stacks)
            error(
                f"The stacks listed above all share the provided prefix "
                f"'{id_or_name_or_prefix}' on their ids. Please provide more "
                f"characters to uniquely identify only one stack."
            )

        elif len(filtered_stacks) == 1:
            return filtered_stacks[0]
        else:
            raise KeyError(
                f"No stack with name or id prefix "
                f"'{id_or_name_or_prefix}' exists."
            )


def get_shared_emoji(is_shared: bool) -> str:
    """Returns the emoji for whether a stack is shared or not.

    Args:
        is_shared: Whether the stack is shared or not.

    Returns:
        The emoji for whether the stack is shared or not.
    """
    return ":white_heavy_check_mark:" if is_shared else ":heavy_minus_sign:"


def print_stacks_table(
    client: "Client", stacks: List["HydratedStackModel"]
) -> None:
    """Print a prettified list of all stacks supplied to this method.

    Args:
        client: Repository instance
        stacks: List of stacks
    """
    stack_dicts = []
    active_stack_model_id = client.active_stack_model.id
    for stack in stacks:
        is_active = stack.id == active_stack_model_id
        stack_config = {
            "ACTIVE": ":point_right:" if is_active else "",
            "STACK NAME": stack.name,
            "STACK ID": stack.id,
            "SHARED": get_shared_emoji(stack.is_shared),
            "OWNER": stack.user.name,
            **{
                component_type.upper(): components[0].name
                for component_type, components in stack.components.items()
            },
        }
        stack_dicts.append(stack_config)

    print_table(stack_dicts)


def print_components_table(
    client: "Client",
    component_type: StackComponentType,
    components: List["HydratedComponentModel"],
) -> None:
    """Prints a table with configuration options for a list of stack components.

    If a component is active (its name matches the `active_component_name`),
    it will be highlighted in a separate table column.

    Args:
        client: Instance of the Repository singleton
        component_type: Type of stack component
        components: List of stack components to print.
    """
    display_name = _component_display_name(component_type, plural=True)
    if len(components) == 0:
        warning(f"No {display_name} registered.")
        return
    active_stack = client.active_stack_model
    active_component_id = None
    if component_type in active_stack.components.keys():
        active_components = active_stack.components[component_type]
        active_component_id = (
            active_components[0].id if active_components else None
        )

    configurations = []
    for component in components:
        is_active = component.id == active_component_id
        component_config = {
            "ACTIVE": ":point_right:" if is_active else "",
            "NAME": component.name,
            "COMPONENT ID": component.id,
            "FLAVOR": component.flavor,
            "SHARED": get_shared_emoji(component.is_shared),
            "OWNER": component.user.name,
            # **{
            #     key.upper(): str(value)
            #     for key, value in component.configuration.items()
            # },
        }
        configurations.append(component_config)
    print_table(configurations)


def _component_display_name(
    component_type: "StackComponentType", plural: bool = False
) -> str:
    """Human-readable name for a stack component.

    Args:
        component_type: Type of the component to get the display name for.
        plural: Whether the display name should be plural or not.

    Returns:
        A human-readable name for the given stack component type.
    """
    name = component_type.plural if plural else component_type.value
    return name.replace("_", " ")


def get_component_by_id_or_name_or_prefix(
    client: "Client",
    id_or_name_or_prefix: str,
    component_type: StackComponentType,
) -> "ComponentModel":
    """Fetches a component of given type within active project using the name, id or partial id.

    Args:
        client: Instance of the Client singleton
        id_or_name_or_prefix: The id, name or partial id of the component to
                              fetch.
        component_type: The type of the component to fetch.

    Returns:
        The component with the given name.

    Raises:
        KeyError: If no stack with the given name exists.
    """
    # First interpret as full UUID
    try:
        component_id = UUID(id_or_name_or_prefix)
        return client.zen_store.get_stack_component(component_id)
    except ValueError:
        pass

    user_only_components = client.zen_store.list_stack_components(
        project_name_or_id=client.active_project.name,
        name=id_or_name_or_prefix,
        type=component_type,
        user_name_or_id=client.active_user.id,
        is_shared=False,
    )

    shared_components = client.zen_store.list_stack_components(
        project_name_or_id=client.active_project.name,
        name=id_or_name_or_prefix,
        type=component_type,
        is_shared=True,
    )

    named_components = user_only_components + shared_components

    if len(named_components) > 1:
        hydrated_components = [c.to_hydrated_model() for c in named_components]
        print_components_table(
            client=client,
            component_type=component_type,
            components=hydrated_components,
        )
        error(
            f"Multiple {component_type.value} components have been found for name "
            f"'{id_or_name_or_prefix}'. The components listed above all share "
            f"this name. Please specify the component by full or partial id."
        )

    elif len(named_components) == 1:
        return named_components[0]
    else:
        logger.debug(
            f"No component with name '{id_or_name_or_prefix}' "
            f"exists. Trying to resolve as partial_id"
        )

        user_only_components = client.zen_store.list_stack_components(
            project_name_or_id=client.active_project.name,
            user_name_or_id=client.active_user.id,
            type=component_type,
            is_shared=False,
        )

        shared_components = client.zen_store.list_stack_components(
            project_name_or_id=client.active_project.name,
            type=component_type,
            is_shared=True,
        )

        all_components = user_only_components + shared_components

        filtered_comps = [
            component
            for component in all_components
            if str(component.id).startswith(id_or_name_or_prefix)
        ]
        if len(filtered_comps) > 1:
            hydrated_components = [
                c.to_hydrated_model() for c in all_components
            ]

            print_components_table(
                client=client,
                component_type=component_type,
                components=hydrated_components,
            )
            error(
                f"The components listed above all share the provided prefix "
                f"'{id_or_name_or_prefix}' on their ids. Please provide more "
                f"characters to uniquely identify only one component."
            )

        elif len(filtered_comps) == 1:
            return filtered_comps[0]
        else:
            raise KeyError(
                f"No component of type `{component_type}` with name or id "
                f"prefix '{id_or_name_or_prefix}' exists."
            )


def get_execution_status_emoji(status: "ExecutionStatus") -> str:
    """Returns an emoji representing the given execution status.

    Args:
        status: The execution status to get the emoji for.

    Returns:
        An emoji representing the given execution status.

    Raises:
        RuntimeError: If the given execution status is not supported.
    """
    from zenml.enums import ExecutionStatus

    if status == ExecutionStatus.FAILED:
        return ":x:"
    if status == ExecutionStatus.RUNNING:
        return ":gear:"
    if status == ExecutionStatus.COMPLETED:
        return ":white_check_mark:"
    if status == ExecutionStatus.CACHED:
        return ":package:"
    raise RuntimeError(f"Unknown status: {status}")


def print_pipeline_runs_table(
    client: "Client", pipeline_runs: List["PipelineRunModel"]
) -> None:
    """Print a prettified list of all pipeline runs supplied to this method.

    Args:
        client: Repository instance
        pipeline_runs: List of pipeline runs
    """
    runs_dicts = []
    for pipeline_run in pipeline_runs:
        if pipeline_run.pipeline_id is None:
            pipeline_name = "unlisted"
        else:
            pipeline_name = client.zen_store.get_pipeline(
                pipeline_run.pipeline_id
            ).name
        if pipeline_run.stack_id is None:
            stack_name = "[DELETED]"
        else:
            stack_name = client.zen_store.get_stack(pipeline_run.stack_id).name
        status = client.zen_store.get_run(pipeline_run.id).status
        status_emoji = get_execution_status_emoji(status)
        run_dict = {
            "PIPELINE NAME": pipeline_name,
            "RUN NAME": pipeline_run.name,
            "RUN ID": pipeline_run.id,
            "STATUS": status_emoji,
            "STACK": stack_name,
            "OWNER": client.zen_store.get_user(pipeline_run.user).name,
        }
        runs_dicts.append(run_dict)
    print_table(runs_dicts)
