#  Copyright (c) ZenML GmbH 2021. All Rights Reserved.
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

import inspect
import os
import pathlib
import sys
from collections import OrderedDict
from contextlib import ExitStack as does_not_raise
from pathlib import Path
from typing import Callable

import pytest
from pytest_mock import MockerFixture

from zenml.client import Client
from zenml.utils import source_utils


def test_is_third_party_module(module_mocker: MockerFixture):
    """Tests that third party modules get detected correctly."""
    module_mocker.patch(
        "zenml.utils.source_utils.get_source_root_path",
        return_value=str(pathlib.Path(__file__).absolute().parents[3]),
    )
    third_party_file = inspect.getfile(pytest.Cache)
    assert source_utils.is_third_party_module(third_party_file)

    non_third_party_file = inspect.getfile(source_utils)
    assert not source_utils.is_third_party_module(non_third_party_file)

    standard_lib_file = inspect.getfile(OrderedDict)
    assert source_utils.is_third_party_module(standard_lib_file)


class EmptyClass:
    pass


def test_resolve_class(module_mocker: MockerFixture):
    """Tests that class resolving works as expected."""
    os.getcwd()
    parent_directory = os.path.dirname(os.path.dirname(__file__))
    os.chdir(parent_directory)

    module_mocker.patch(
        "zenml.utils.source_utils.get_source_root_path",
        return_value=str(pathlib.Path(__file__).absolute().parents[1]),
    )

    try:
        assert (
            source_utils.resolve_class(EmptyClass)
            == "utils.test_source_utils.EmptyClass"
        )
    finally:
        os.chdir(parent_directory)


def test_get_source():
    """Tests if source of objects is gotten properly."""
    assert source_utils.get_source(pytest.Cache)


def test_get_hashed_source():
    """Tests if hash of objects is computed properly."""
    assert source_utils.get_hashed_source(pytest.Cache)


def test_prepend_python_path():
    """Tests that the context manager prepends an element to the pythonpath and
    removes it again after the context is exited."""
    path_element = "definitely_not_part_of_pythonpath"

    assert path_element not in sys.path
    with source_utils.prepend_python_path([path_element]):
        assert sys.path[0] == path_element

    assert path_element not in sys.path


def test_loading_class_by_path_prepends_repo_path(
    clean_client, mocker, tmp_path
):
    """Tests that loading a class always prepends the active repository root to
    the python path."""

    os.chdir(str(tmp_path))

    Client.initialize()
    clean_client.activate_root()

    python_file = clean_client.root / "some_directory" / "python_file.py"
    python_file.parent.mkdir()
    python_file.write_text("test = 1")

    mocker.patch.object(sys, "path", [])

    with does_not_raise():
        # the repo root should be in the python path right now, so this file
        # can be imported
        source_utils.load_source_path_class("some_directory.python_file.test")

    with pytest.raises(ModuleNotFoundError):
        # the subdirectory will not be in the python path and therefore this
        # import should not work
        source_utils.load_source_path_class("python_file.test")


def test_import_python_file_for_first_time(
    clean_client, mocker, files_dir: Path
):
    """Test that importing a python file as module works and allows for
    importing of module attributes even with module popped from sys path"""

    SOME_MODULE = "some_module"
    SOME_MODULE_FILENAME = SOME_MODULE + ".py"
    SOME_FUNC = "some_func"

    os.chdir(str(files_dir))
    clean_client.activate_root()
    Client.initialize()

    mocker.patch.object(sys, "path", [])

    module = source_utils.import_python_file(
        SOME_MODULE_FILENAME, zen_root=str(files_dir)
    )

    # Assert that attr could be fetched from module
    assert isinstance(getattr(module, SOME_FUNC), Callable)

    # Assert that module has been loaded into sys.module
    assert SOME_MODULE in sys.modules

    # Assert that sys path is unaffected
    assert len(sys.path) == 0

    # Cleanup modules for future tests
    del sys.modules[SOME_MODULE]


def test_import_python_file_when_already_loaded(
    clean_client, mocker, files_dir: Path
):
    """Test that importing a python file as module works even if it is
    already on sys path and allows for importing of module attributes"""

    SOME_MODULE = "some_module"
    SOME_MODULE_FILENAME = SOME_MODULE + ".py"
    SOME_FUNC = "some_func"

    os.chdir(str(files_dir))
    clean_client.activate_root()
    Client.initialize(root=files_dir)

    mocker.patch.object(sys, "path", [])

    source_utils.import_python_file(
        str(SOME_MODULE_FILENAME), zen_root=str(files_dir)
    )

    # Assert that module has been loaded into sys.module
    assert SOME_MODULE in sys.modules

    # Load module again, to cover alternative behavior of the
    #  import_python_file, where the module is loaded already
    module = source_utils.import_python_file(
        str(SOME_MODULE_FILENAME), zen_root=str(files_dir)
    )

    # Assert that attr could be fetched from the module returned by the func
    assert isinstance(getattr(module, SOME_FUNC), Callable)

    # Assert that sys path is unaffected
    assert len(sys.path) == 0

    # Cleanup modules for future tests
    del sys.modules[SOME_MODULE]


def test_import_python_file(clean_client, mocker, files_dir: Path):
    """Test that importing a python file as module works even if it is
    already imported within the another previously loaded module"""

    MAIN_MODULE = "main_module"
    MAIN_MODULE_FILENAME = MAIN_MODULE + ".py"
    SOME_MODULE = "some_module"
    SOME_MODULE_FILENAME = SOME_MODULE + ".py"
    OTHER_FUNC = "other_func"

    os.chdir(str(files_dir))
    clean_client.activate_root()
    Client.initialize(root=files_dir)

    main_python_file = files_dir / MAIN_MODULE_FILENAME
    some_python_file = files_dir / SOME_MODULE_FILENAME

    assert main_python_file.exists()
    assert some_python_file.exists()

    mocker.patch.object(sys, "path", [])

    source_utils.import_python_file(
        str(main_python_file), zen_root=str(files_dir)
    )

    # Assert that module has been loaded into sys.module
    assert MAIN_MODULE in sys.modules

    module = source_utils.import_python_file(
        str(some_python_file), zen_root=str(files_dir)
    )

    # Assert that attr could be fetched from the module returned by the func
    assert isinstance(getattr(module, OTHER_FUNC), Callable)

    # Assert that sys path is unaffected
    assert len(sys.path) == 0

    # Cleanup modules for future tests
    del sys.modules[MAIN_MODULE]
    del sys.modules[SOME_MODULE]
