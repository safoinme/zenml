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
import sys
from contextlib import ExitStack as does_not_raise
from typing import Dict, List, Tuple

import pytest
from pydantic import BaseModel

from zenml import pipeline, step
from zenml.exceptions import StepInterfaceError


@step
def step_with_int_input(input_: int) -> int:
    return input_


def test_input_validation_outside_of_pipeline():
    with pytest.raises(Exception):
        # Missing input
        step_with_int_input()

    with pytest.raises(Exception):
        # Wrong type
        step_with_int_input(input_="wrong_type")

    output = step_with_int_input(input_=1)
    assert output == 1
    assert isinstance(output, int)

    output = step_with_int_input(input_=3.0)
    assert output == 3
    assert isinstance(output, int)


def test_input_validation_inside_pipeline():
    @pipeline
    def test_pipeline(step_input):
        return step_with_int_input(step_input)

    with pytest.raises(RuntimeError):
        test_pipeline(step_input="wrong_type")

    with does_not_raise():
        test_pipeline(step_input=1)
        test_pipeline(step_input=3.0)


def test_passing_invalid_parameters():
    class UnsupportedClass:
        # This class is not supported as a parameter as it's not JSON
        # serializable
        pass

    @step
    def s(a: UnsupportedClass) -> None:
        pass

    @pipeline
    def test_pipeline():
        s(a=UnsupportedClass())

    with pytest.raises(StepInterfaceError):
        test_pipeline()


class BaseModelSubclass(BaseModel):
    pass


@step
def step_with_valid_parameter_inputs(
    a: BaseModelSubclass,
    b: int,
    c: Dict[str, float],
    d: Tuple[int, ...],
    e: List[int],
) -> None:
    pass


def test_passing_valid_parameters():
    @pipeline
    def test_pipeline():
        step_with_valid_parameter_inputs(
            a=BaseModelSubclass(), b=1, c={"key": 0.1}, d=(1, 2), e=[3, 4]
        )

    with does_not_raise():
        test_pipeline()


def test_step_parameter_merging():
    """Tests that parameters defined in the run config overwrite values defined
    in code."""
    from zenml.client import Client
    from zenml.config.compiler import Compiler
    from zenml.config.pipeline_run_configuration import (
        PipelineRunConfiguration,
    )

    @pipeline
    def test_pipeline():
        step_with_int_input(input_=1)

    run_config = PipelineRunConfiguration.parse_obj(
        {"steps": {"step_with_int_input": {"parameters": {"input_": 5}}}}
    )
    test_pipeline.prepare()
    deployment, _ = Compiler().compile(
        pipeline=test_pipeline,
        stack=Client().active_stack,
        run_configuration=run_config,
    )
    assert (
        deployment.step_configurations[
            "step_with_int_input"
        ].config.parameters["input_"]
        == 5
    )


if sys.version_info >= (3, 9):

    @step
    def step_with_non_generic_inputs(
        a: dict[str, int], b: list[float]
    ) -> set[bytes]:
        return set()


@pytest.mark.skipif(
    sys.version_info < (3, 9), reason="Only works on python>=3.9"
)
def test_step_allows_dict_list_annotations():
    """Tests that a step can use `list`, `dict` annotations instead of
    `typing.Dict`/`typing.List`"""

    @pipeline
    def test_pipeline():
        step_with_non_generic_inputs(a={"key": 1}, b=[2.1])

    with does_not_raise():
        test_pipeline()
