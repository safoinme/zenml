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
from pipelines import github_example_pipeline
from steps import get_first_num, get_random_int, subtract_numbers

if __name__ == "__main__":
    pipeline_instance = github_example_pipeline(
        first_step=get_first_num(),
        second_step=get_random_int(),
        third_step=subtract_numbers(),
    )

    pipeline_instance.run()

    # If you want to run your pipeline on a schedule instead, you need to pass
    # in a `Schedule` object with a cron expression. Note that for the schedule
    # to get active, you'll need to merge the GitHub Actions workflow into your
    # GitHub default branch. To see it in action, uncomment the following lines:

    # from zenml.pipelines import Schedule
    # pipeline_instance.run(
    #     schedule=Schedule(cron_expression="* 1 * * *")
    # )
