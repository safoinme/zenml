# 🏃 Run pipelines in production using Sagemaker

[Sagemaker Pipelines](https://aws.amazon.com/sagemaker/pipelines?tag=soumet-20)
is a serverless ML workflow tool running on AWS. It is
an easy way to quickly run your code in a production-ready, repeatable 
cloud orchestrator that requires minimal setup without provisioning and paying 
for standby compute.

## 📄 Pre-requisites

In order to run on Sagemaker you will need to do some configuration
within AWS to create all the required resources and permissions. In total, you will need to have:

- [ECR container registry](https://docs.zenml.io/component-gallery/container-registries/amazon-ecr)
- [S3 artifact store](https://docs.zenml.io/component-gallery/artifact-stores/amazon-s3)
- [AWS Secrets Manager](https://docs.zenml.io/component-gallery/secrets-managers/aws).

On top of having these resources and setting them up for ZenML, you will also
need to do some permission tuning.

You will need to
[authorize](https://docs.zenml.io/component-gallery/container-registries/amazon-ecr#how-to-use-it)
your local Docker client to have access the ECR container registry, as explained
in our docs:

```shell
aws ecr get-login-password --region <YOUR_AWS_REGION> | docker login --username AWS --password-stdin <YOUR_ECR_REGISTRY_URI>
```

To handle the relevant permissions, you will need to create an IAM role that
has access to the relevant parts of your AWS account. You can do this directly
in the AWS console, or using the AWS CLI.

![Create a role](assets/sagemaker0.png)

When creating the role, make sure to add Sagemaker-specific permissions:

![Add permissions](assets/sagemaker1.png)

Once you've created the role, you will need to add permissions to allow access
to your secrets in the AWS Secrets Manager. You can do this by attaching a
`SecretsManagerReadWrite` policy to the role:

![Add secrets manager permissions](assets/sagemaker2.png)

## 🥞 Create a Sagemaker stack

Before registering the stack, you need to deploy a remote ZenML server 
on AWS. See the [deployment guide](https://docs.zenml.io/getting-started/deploying-zenml) 
for more information.

Once everything is done on the AWS side, we will need to configure a
stack with all of these components.

* The **artifact store** to store step outputs in an S3 Bucket.
* The Docker images that are created to run your pipeline are stored in ECR
  **container registry**.
* The **Sagemaker orchestrator** is responsible for running your ZenML pipeline
  in Sagemaker.
* The **secrets manager** contains the secrets to allow access to the artifact
  store.

When running the upcoming commands, make sure to
replace all the <PLACEHOLDERS> with the correct values from how you set things
up with AWS.

```bash
# install CLI
pip install "zenml[server]"

# install ZenML integrations
zenml integration install aws pytorch s3

# pull example
zenml example pull sagemaker_orchestration
cd zenml_examples/sagemaker_orchestration

# Create a zenml repository
zenml init

# The CONTAINER_REGISTRY_URI will have a format like this: xxx.dkr.ecr.REGION.amazonaws.com
zenml container-registry register aws_registry --flavor=aws --uri=<CONTAINER_REGISTRY_URI>

# For the secrets manager, all we'll need it the gcp PROJECT_ID
zenml secrets-manager register aws_secrets_manager --flavor=aws --region=<YOUR_AWS_REGION>

# You'll need to register a secret to use for your artifact-store authentication
zenml secrets-manager secret register s3_secret --aws_access_key_id=<YOUR_ACCESS_KEY_ID> --aws_secret_access_key=<YOUR_SECRET_ACCESS_KEY> --schema=aws

# The PATH_TO_YOUR_S3_BUCKET is the path to your S3 bucket: s3://xxx
zenml artifact-store register aws_artifact_store --flavor=s3 --path=<PATH_TO_YOUR_S3_BUCKET> --authentication_secret=s3_secret

# register the orchestrator
zenml orchestrator register sagemaker_orchestrator --flavor=sagemaker --execution_role=<NAME_OF_AWS_ROLE_CREATED_EARLIER>

# Now we're ready to assemble our stack
zenml stack register sagemaker_stack -a aws_artifact_store -o sagemaker_orchestrator -c aws_registry -x aws_secrets_manager --set
```

### ▶️ Run the pipeline

Once your stack is fully set up, you should be good to go. 

```bash
python run.py
```

That's it! If everything went as planned this pipeline should now be running in
the cloud! To access the Sagemaker Pipelines UI, you will have to launch
Sagemaker Studio via the AWS Sagemaker UI. Make sure that you are launching it
from within your desired AWS region.

![Sagemaker Studio launch](assets/sagemaker3.png)

Once the Studio UI is launched, click on the 'Pipeline' button on the left-hand
side and from there you can view the pipelines that have been launched via
ZenML:

![Sagemaker Studio Pipelines](assets/sagemaker4.png)

### 💻 Specifying per-step resources

If you're using the Sagemaker orchestrator and some of your pipelines steps have 
certain custom requirements, you can specify them using the step decorator as 
follows:

```python
from zenml.steps import step
from zenml.integrations.aws.flavors.sagemaker_orchestrator_flavor import (
    SagemakerOrchestratorSettings,
)

@step(settings={"orchestrator.sagemaker": SagemakerOrchestratorSettings(volume_size_in_gb=35)})
def my_step(...) -> ...:
    ...
```

For full details on which settings are configurable, please refer to [the API
docs](https://apidocs.zenml.io/latest/integration_code_docs/integrations-aws/#zenml.integrations.aws.flavors.sagemaker_step_orchestrator_flavor.SagemakerOrchestratorSettings) for full information.

### 🧽 Clean up

Once you're done experimenting, you can delete the example files by calling:

```bash
rm -rf zenml_examples
```

Additionally, you might have to clean up your cloud resources to avoid running 
costs for storage of artifacts, containers or secrets.

# 📜 Learn more

Our docs regarding the Sagemaker integration can be found 
[here](https://docs.zenml.io/component-gallery/orchestrators/sagemaker).

If you want to learn more about orchestrators in general or about how to build
your own orchestrators in ZenML check out our 
[docs](https://docs.zenml.io/component-gallery/orchestrators/custom).
