#!/usr/bin/env bash

set -Eeo pipefail

setup_stack () {
  zenml container-registry register local_registry  --flavor=default --uri=localhost:5000|| \
    msg "${WARNING}Reusing preexisting container registry ${NOFORMAT}local_registry, this might fail if port 5000 is blocked by another process."
  zenml orchestrator register local_kubeflow_orchestrator --flavor=kubeflow || \
    msg "${WARNING}Reusing preexisting orchestrator ${NOFORMAT}local_kubeflow_orchestrator"
  zenml stack register local_kubeflow_stack \
      -a default \
      -o local_kubeflow_orchestrator \
      -c local_registry || \
    msg "${WARNING}Reusing preexisting stack ${NOFORMAT}local_kubeflow_stack"

  zenml stack set local_kubeflow_stack

  zenml stack up
}

pre_run () {
  zenml integration install kubeflow tensorflow tensorboard
}

pre_run_forced () {
  zenml integration install kubeflow tensorflow tensorboard -y
}

post_run () {
  # cleanup the last local ZenML daemon started by the example
  pkill -n -f zenml.services.local.local_daemon_entrypoint || true
}
