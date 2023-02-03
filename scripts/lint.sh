#!/usr/bin/env bash
set -e
set -x
set -o pipefail

SRC=${1:-"src/zenml tests examples"}
SRC_NO_TESTS=${1:-"src/zenml tests/harness"}
TESTS_EXAMPLES=${1:-"tests examples"}

export ZENML_DEBUG=1
export ZENML_ANALYTICS_OPT_IN=false
ruff $SRC_NO_TESTS
# TODO: Fix docstrings in tests and examples and remove the `--extend-ignore D` flag
ruff $TESTS_EXAMPLES --extend-ignore D

# TODO: remove this once ruff implements the feature
autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place $SRC --exclude=__init__.py --check | ( grep -v "No issues detected" || true )

black $SRC  --check

# check type annotations
mypy $SRC_NO_TESTS
