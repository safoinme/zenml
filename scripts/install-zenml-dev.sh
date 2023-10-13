#!/bin/sh -e

INTEGRATIONS=no

parse_args () {
    while [ $# -gt 0 ]; do
        case $1 in
            -i|--integrations)
                INTEGRATIONS="$2"
                shift # past argument
                shift # past value
                ;;
            -*|--*)
                echo "Unknown option $1"
                exit 1
                ;;
            *)
                shift # past argument
                ;;
        esac
    done
}

install_zenml() {
    # install ZenML in editable mode
    pip install -e .[server,templates,terraform,secrets-aws,secrets-gcp,secrets-azure,secrets-hashicorp,s3fs,gcsfs,adlfs,dev,mlstacks]
}

install_integrations() {

    # figure out the python version
    python_version=$(python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")

    ignore_integrations="feast label_studio bentoml seldon kserve langchain llama_index pycaret skypilot_aws skypilot_gcp skypilot_azure"
    # if python version is 3.11, exclude all integrations depending on kfp
    # because they are not yet compatible with python 3.11
    if [ "$python_version" = "3.11" ]; then
        ignore_integrations="$ignore_integrations kubeflow tekton gcp"
    fi

    # turn the ignore integrations into a list of --ignore-integration args
    ignore_integrations_args=""
    for integration in $ignore_integrations; do
        ignore_integrations_args="$ignore_integrations_args --ignore-integration $integration"
    done

    # install basic ZenML integrations
    zenml integration export-requirements \
        --output-file integration-requirements.txt \
        $ignore_integrations_args
    pip install -r integration-requirements.txt
    rm integration-requirements.txt

    # install langchain and llama_index integrations separately
    zenml integration install -y langchain llama_index
}


set -x
set -e

parse_args "$@"

python -m pip install --upgrade pip

install_zenml

# install integrations, if requested
if [ "$INTEGRATIONS" = yes ]; then
    install_integrations
    # refresh the ZenML installation after installing integrations
    install_zenml
fi
