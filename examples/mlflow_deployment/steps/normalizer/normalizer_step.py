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
import numpy as np  # type: ignore [import]

from zenml.steps import Output, step


@step
def normalizer(
    x_train: np.ndarray, x_test: np.ndarray
) -> Output(x_train_normed=np.ndarray, x_test_normed=np.ndarray):
    """Normalize the values for all the images so they are between 0 and 1"""
    x_train_normed = x_train / 255.0
    x_test_normed = x_test / 255.0
    return x_train_normed, x_test_normed
