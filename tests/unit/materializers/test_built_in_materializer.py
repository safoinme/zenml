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
import os

from tests.unit.test_general import _test_materializer


def test_basic_type_materialization():
    """Test materialization for `bool`, `float`, `int`, `str` objects."""
    for type_, example in [
        (bool, True),
        (float, 0.0),
        (int, 0),
        (str, ""),
    ]:
        result = _test_materializer(
            step_output_type=type_, step_output=example
        )
        assert result == example


def test_bytes_materialization():
    """Test materialization for `bytes` objects.

    This is a separate test since `bytes` is not JSON serializable.
    """
    example = b""
    result = _test_materializer(step_output_type=bytes, step_output=example)
    assert result == example


def test_empty_dict_list_tuple_materialization():
    """Test materialization for empty `dict`, `list`, `tuple` objects."""
    for type_, example in [
        (dict, {}),
        (list, []),
        (tuple, ()),
    ]:
        result = _test_materializer(
            step_output_type=type_, step_output=example
        )
        assert result == example


def test_simple_dict_list_tuple_materialization(tmp_path):
    """Test materialization for `dict`, `list`, `tuple` with data."""

    def _validate_single_file(artifact_uri: str) -> None:
        files = os.listdir(artifact_uri)
        assert len(files) == 1

    for type_, example in [
        (dict, {"a": 0, "b": 1, "c": 2}),
        (list, [0, 1, 2]),
        (tuple, (0, 1, 2)),
    ]:
        result = _test_materializer(
            step_output_type=type_,
            step_output=example,
            validation_function=_validate_single_file,
        )
        assert result == example


def test_list_of_bytes_materialization():
    """Test materialization for lists of bytes."""
    example = [b"0", b"1", b"2"]
    result = _test_materializer(step_output_type=list, step_output=example)
    assert result == example


def test_dict_of_bytes_materialization():
    """Test materialization for dicts of bytes."""
    example = {"a": b"0", "b": b"1", "c": b"2"}
    result = _test_materializer(step_output_type=dict, step_output=example)
    assert result == example


def test_tuple_of_bytes_materialization():
    """Test materialization for tuples of bytes."""
    example = (b"0", b"1", b"2")
    result = _test_materializer(step_output_type=tuple, step_output=example)
    assert result == example


def test_set_materialization():
    """Test materialization for `set` objects."""
    for example in [set(), {1, 2, 3}, {b"0", b"1", b"2"}]:
        result = _test_materializer(step_output_type=set, step_output=example)
        assert result == example


def test_mixture_of_all_builtin_types():
    """Test a mixture of built-in types as the ultimate stress test."""
    example = [
        {
            "a": (42, 1.0, "aa", True),  # tuple of serializable basic types
            "b": {
                "ba": ["baa", "bab"],
                "bb": [3.7, 1.8],
            },  # dict of lists of serializable basic types
            "c": b"ca",  # bytes (non-serializable)
        },  # non-serializable dict
        {1.0, 2.0, 4, 4},  # set of serializable types
    ]  # non-serializable list
    result = _test_materializer(step_output_type=list, step_output=example)
    assert result == example


def test_none_values():
    """Tests serialization of `None` values in container types."""
    for type_, example in [
        (list, [1, "a", None]),
        (tuple, (1, "a", None)),
        (dict, {"key": None}),
    ]:
        result = _test_materializer(
            step_output_type=type_, step_output=example
        )
        assert result == example
