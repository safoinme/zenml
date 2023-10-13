#  Copyright (c) ZenML GmbH 2023. All Rights Reserved.
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

from zenml.utils.integration_utils import parse_requirement


def test_parse_requirement():
    # Test case 1: requirement without extras
    requirement = "numpy"
    expected_output = ("numpy", None)
    assert parse_requirement(requirement) == expected_output

    # Test case 2: requirement with extras
    requirement = "numpy[tests]"
    expected_output = ("numpy", "[tests]")
    assert parse_requirement(requirement) == expected_output

    # Test case 3: requirement with hyphens and underscores
    requirement = "my-package_1"
    expected_output = ("my-package_1", None)
    assert parse_requirement(requirement) == expected_output

    # Test case 4: requirement with hyphens and extras
    requirement = "my-package-1[tests]"
    expected_output = ("my-package-1", "[tests]")
    assert parse_requirement(requirement) == expected_output

    # Test case 5: requirement with invalid characters
    requirement = "my_package-1[tests]"
    expected_output = ("my_package-1", "[tests]")
    assert parse_requirement(requirement) == expected_output

    # Edge Case 1: Empty string
    requirement = ""
    expected_output = (None, None)
    assert parse_requirement(requirement) == expected_output

    # Edge Case 2: Just extras without name
    requirement = "[extra]"
    expected_output = (None, None)
    assert parse_requirement(requirement) == expected_output

    # Edge Case 3: Only digits
    requirement = "123"
    expected_output = ("123", None)
    assert parse_requirement(requirement) == expected_output

    # Edge Case 5: Non-alphanumeric characters in extras
    requirement = "package[extra!]"
    expected_output = ("package", None)
    assert parse_requirement(requirement) == expected_output

    # Edge Case 6: Spaces in name
    requirement = "package name"
    expected_output = (None, None)
    assert parse_requirement(requirement) == expected_output

    # Edge Case 7: Spaces in extras
    requirement = "package[extra 1]"
    expected_output = (None, None)
    assert parse_requirement(requirement) == expected_output

    # Test case 8: Multiple extras
    requirement = "package[extra1,extra2]"
    expected_output = ("package", "[extra1,extra2]")
    assert parse_requirement(requirement) == expected_output

    # Test case 9: Leading and trailing whitespaces
    requirement = " package "
    expected_output = (None, None)
    assert parse_requirement(requirement) == expected_output
