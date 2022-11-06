# Distributed Data Processing with Spark on Kubernetes

In an MLOps workflow where the scale is high, distributed programming as a
feature has the potential to be a game-changer, especially in steps such as
pre-processing, splitting and much more. That is why we decided to create an 
integration with Spark, one of the most prominent tools when it comes to 
distributed programming. The new `spark` integration of ZenML brings a few 
implementations for our users to use:

- **Materializer**: The `SparkDataFrameMaterializer` is designed to handle the
  input and outputs which are modeled after
  the [PySpark Dataframe API](https://spark.apache.org/docs/latest/api/python/getting_started/quickstart_df.html)
  .
- **Materializer**: Similar to the dataframes, the `SparkModelMaterializer`
  brings support for most of the model types included in the Machine Learning
  Library (MLLib) of Spark.
- **Step Operator**: The `SparkStepOperator` serves as the base class for all
  the Spark-related step operators.
- **Step Operator**: The `KubernetesSparkStepOperator` is responsible for
  launching ZenML steps as Spark applications with Kubernetes as a cluster
  manager.

# Requirements

To run this example, you need to install and initialize ZenML:

```shell
# install CLI
pip install "zenml[server]"

# install ZenML integrations
zenml integration install spark

# pull example
zenml example pull spark_distributed_programming
cd zenml_examples/spark_distributed_programming

# initialize a local ZenML Repository
zenml init

# Start the ZenServer to enable dashboard access
zenml up
```

In order to follow this example, you need an AWS account which you can use to
spin up a few resources. Additionally, you have to install Spark following the 
instructions [here](https://spark.apache.org/downloads.html).

#### Recommended versions
- `spark` = 3.2.1
- `hadoop` = 3.2

# Setting up the AWS resources

In order to showcase the capabilities of the Spark integration, we build a
concrete example using a simple ZenML stack on AWS. But before registering the
stack, components, and secrets, let us create some resources on AWS first.

## Artifact Store - S3

For the artifact store, we will need to create a bucket on S3:

- Go to the [S3 website](https://s3.console.aws.amazon.com/s3/buckets).
- Click on `Create bucket`.
- Select a descriptive name and a region. Let's also store these values in our
  terminal:

```bash
REGION=<REGION> # for example us-west-1
S3_BUCKET_NAME=<S3_BUCKET_NAME>
```

## Metadata Store - RDS

For the metadata store, we will use a MySQL database on RDS:

- Go to the [RDS website](https://console.aws.amazon.com/rds).
- Make sure the correct region is selected on the top right (this region must be
  the same for all following steps).
- Click on `Create database`.
- Select `Easy Create`, `MySQL`, `Free tier` and enter values for your database
  name, username, and password.
- Note down the username and password:

```bash
RDS_MYSQL_USERNAME=<RDS_MYSQL_USERNAME>
RDS_MYSQL_PASSWORD=<RDS_MYSQL_PASSWORD>
```

- Wait until the deployment is finished.
- Select your new database and note down its endpoint:

```bash
RDS_MYSQL_ENDPOINT=<RDS_MYSQL_ENDPOINT>
```

- Click on the active VPC security group, select `Inbound rules` and click
  on `Edit inbound rules`
- Add a new rule with type `MYSQL/Aurora` and source `Anywhere-IPv4`. (**Note**:
  You can also restrict this to more limited IP address ranges or security
  groups if you want to limit access to your database.)
- Go back to your database page and click on `Modify` in the top right.
- In the `Connectivity` section, open the `Advanced configuration` and enable
  public access.

## Container Registry - ECR

For the container registry, we will use ECR:

- Go to the [ECR website](https://console.aws.amazon.com/ecr).
- Make sure the correct region is selected on the top right.
- Click on `Create repository`.
- Create a private repository called `zenml` with default settings.
- Note down the URI of your registry and log in:

```bash
# This should be the prefix of your just created repository URI, 
# e.g. 714803424590.dkr.ecr.eu-west-1.amazonaws.com
ECR_URI=<ECR_URI>

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI
```

## Step Operator - EKS

For the step operator, we will spin up a Kubernetes cluster:

- Follow [this guide](https://docs.aws.amazon.com/eks/latest/userguide/service_IAM_role.html#create-service-role)
to create an Amazon EKS cluster role. 
- Follow [this guide](https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html#create-worker-node-role)
to create an Amazon EC2 node role. 
- Go to the [IAM website](https://console.aws.amazon.com/iam), and
  select `Roles` to edit both roles.
- Attach the `SecretsManagerReadWrite`, `AmazonRDSFullAccess`,
  and `AmazonS3FullAccess` policies both roles.
- Go to the [EKS website](https://console.aws.amazon.com/eks).
- Make sure the correct region is selected on the top right.
- Click on `Add cluster` and select `Create`.
- Enter a name and select the **cluster role** for `Cluster service role`.
- Keep the default values for the networking and logging steps and create the
  cluster.
- Note down the cluster name and the API server endpoint:

```bash
EKS_CLUSTER_NAME=<EKS_CLUSTER_NAME>
EKS_API_SERVER_ENDPOINT=<API_SERVER_ENDPOINT>
```

- After the cluster is created, select it and click on `Add node group` in
  the `Compute` tab.
- Enter a name and select the **node role**.
- For the instance type, we recommend `t3a.xlarge`, as it provides up to 4 
vCPUs and 16 GB of memory.

### Docker image for the Spark drivers and executors

When you want to run your steps on a Kubernetes cluster, Spark will require you
to choose a base image for the driver and executor pods. Normally, for this 
purpose, you can either use one of the base images
in [Spark’s dockerhub](https://hub.docker.com/r/apache/spark-py/tags) or create
an image using
the [docker-image-tool](https://spark.apache.org/docs/latest/running-on-kubernetes.html#docker-images)
which will use your own Spark installation and build an image.

For this example, you need to use the latter and utilize the 
`docker-image-tool`. However, before the build process, you also need to 
download the following packages

- [`hadoop-aws` = 3.3.1](https://mvnrepository.com/artifact/org.apache.hadoop/hadoop-aws/3.3.1)
- [`aws-java-sdk-bundle` = 1.12.150](https://mvnrepository.com/artifact/com.amazonaws/aws-java-sdk-bundle/1.12.150)

and put them in the `jars` folder within your Spark installation. Once that 
is set up, you can build the image as follows:

```bash
cd $SPARK_HOME

SPARK_IMAGE_TAG=<SPARK_IMAGE_TAG>

./bin/docker-image-tool.sh -t $SPARK_IMAGE_TAG -p kubernetes/dockerfiles/spark/bindings/python/Dockerfile -u 0 build

BASE_IMAGE_NAME=spark-py:$SPARK_IMAGE_TAG
```

### Configuring RBAC

Additionally, you may need to create the following resources in Kubernetes 
in order to give Spark access to edit/manage your driver executor pods. You 
can use the `rbac.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: spark-namespace
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark-service-account
  namespace: spark-namespace
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: spark-role
  namespace: spark-namespace
subjects:
  - kind: ServiceAccount
    name: spark-service-account
    namespace: spark-namespace
roleRef:
  kind: ClusterRole
  name: edit
  apiGroup: rbac.authorization.k8s.io
---
```

Simply execute:

```bash
aws eks --region=$REGION update-kubeconfig --name=$EKS_CLUSTER_NAME

kubectl create -f rbac.yaml
```

and note down the namespace and the name of the service account.

```bash
KUBERNETES_NAMESPACE=spark-namespace
KUBERNETES_SERVICE_ACCOUNT=spark-service-account
```

# Setting up the stack 

All we need to do now is to bring everything together in ZenML. Let’s start 
by registering the most important component of the demo, namely 
the **step operator**.

```bash
# Register the spark on Kubernetes step operator
zenml step-operator register spark_step_operator \
    --flavor=spark-kubernetes \
    --master=k8s://$EKS_API_SERVER_ENDPOINT \
    --namespace=$KUBERNETES_NAMESPACE \
    --service_account=$KUBERNETES_SERVICE_ACCOUNT \
    --docker_parent_image=$BASE_IMAGE_NAME
```

Following that, we will register the **secrets manager**, as we will utilize 
it to register some secrets required by some of the other components:

```bash
# Register the secrets manager on AWS
zenml secrets-manager register spark_secrets_manager \
    --flavor=aws \
    --region_name=$REGION
```

Next, let us register our **artifact store** on S3. For this example, we 
will also use a secret while registering our artifact store.

```bash
# Register the artifact store using the secret
zenml artifact-store register spark_artifact_store \
    --flavor=s3 \
    --path=$S3_BUCKET_NAME \
    --authentication_secret=s3_authentication
```

We also register the **container registry** on ECR as follows:

```bash
# Register the container registry on ECR
zenml container-registry register spark_container_registry \
    --flavor=aws \
    --uri=$ECR_URI
```

Finally, let’s finalize the stack.

```bash
# Register the stack
zenml stack register spark_stack \
    -o default \
    -s spark_step_operator \
    -x spark_secrets_manager \
    -a spark_artifact_store \
    -c spark_container_registry \
    --set
```

and register the required secrets:

```bash
# Register the authentication secret for s3
zenml secrets-manager secret register s3_authentication \
    --schema=aws \
    --aws_access_key_id=<ACCESS_KEY_ID> \
    --aws_secret_access_key=<SECRET_ACCESS_KEY> \
    --aws_session_token=<SESSION_TOKEN>
	
# Register the authentication secret for RDS
zenml secrets-manager secret register rds_authentication \
    --schema=mysql \
    --user=$RDS_MYSQL_USERNAME \
    --password=$RDS_MYSQL_PASSWORD
```
### Running the pipeline

Now that our stack is ready, you can go ahead and run your pipeline: 

```bash
python run.py
```

This will launch the `spark_pipeline` that consists of five different steps 
which all use Spark as the step operator.

When running `kubectl get pods -n $KUBERNETES_NAMESPACE`, you should now also 
be able to see that a driver pod was created in your cluster for each pipeline 
step.

### Interacting with the pods

For debugging, it can sometimes be handy to interact with the Kubernetes pods
directly via kubectl.

```bash
kubectl get pods -n $KUBERNETES_NAMESPACE
```
