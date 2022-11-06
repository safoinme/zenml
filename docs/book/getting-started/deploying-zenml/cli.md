---
description: Deploying ZenML on cloud using the CLI
---

The easiest and fastest way to get running on the cloud is by using the `deploy` CLI command. It currently only supports deploying to Kubernetes on managed cloud services. You can check the [overview page](./deploying-zenml.md) to learn other options that you have.  

Before we begin, it will help to understand the [architecture](./deploying-zenml.md#scenario-3-server-and-database-hosted-in-the-cloud) around the ZenML server and the database that it uses. Now, depending on your setup, you may find one of the following scenarios relevant.

## Option 1: Starting from scratch

If you don't have an existing Kubernetes cluster, you have the following two options to set it up:
- Creating it manually using the documentation for your cloud provider. For convenience, here are links for [AWS](https://docs.aws.amazon.com/eks/latest/userguide/create-cluster.html), [Azure](https://learn.microsoft.com/en-us/azure/aks/learn/quick-kubernetes-deploy-portal?tabs=azure-cli) and [GCP](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-zonal-cluster#before_you_begin).
- Using a [stack recipe](../../advanced-guide/practical/practical-mlops.md) that sets up a cluster along with other tools that you might need in your cloud stack like artifact stores, and secret managers. Take a look at all [available stack recipes](https://github.com/zenml-io/mlops-stacks#-list-of-recipes) to see if there's something that works for you.

> **Note**
> Once you have created your cluster, make sure that you configure your [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl) client to talk to it. If you have used stack recipes, this step is already done for you!

You're now ready to deploy ZenML! Run the following command:
```
zenml deploy
```
You will be prompted to provide a name for your deployment and details like what cloud provider you want to deploy to, in addition to the username, password and email you want to set for the default user — and that's it! It creates the database and any VPCs, permissions and more that is needed.

> **Note**
> To be able to run the deploy command, you should have your cloud provider's CLI configured locally with permissions to create resources like MySQL databases and networks.

Reasonable defaults are in place for you already and if you wish to configure more settings, take a look at the next scenario that uses a config file.

## Option 2: Using existing cloud resources

### Existing Kubernetes Cluster

If you already have an existing cluster without an ingress controller, you can jump straight to the `deploy` command above to get going with the defaults. Please make sure you have your local `kubectl` configured to talk to your cluster.

#### Having an existing NGINX Ingress Controller
The `deploy` command, by default, tries to create an NGINX ingress controller on your cluster. If you already have an existing controller, you can tell ZenML to not re-deploy it through the use of a config file. This file can be found in the [Configuration File Templates](#configuration-file-templates) towards the end of this guide. It offers a host of configuration options that you can leverage for advanced use cases.

- Check if an ingress controller is running on your cluster by running the following command. You should see an entry in the output with the hostname populated.
    ```
    # change the namespace to any other where 
    # you might have the controller installed
    kubectl get svc -n ingress-nginx
    ```
- Set `create_ingress_controller` to `false`.
- Supply your controller's hostname to the `ingress_controller_hostname` variable.
    > **Note**
    > The address should not have a trailing `/`.
- You can now run the `deploy` command and pass the config file above, to it.

    ```
    zenml deploy --config=/PATH/TO/FILE
    ```
    > **Note**
    > To be able to run the deploy command, you should have your cloud provider's CLI configured locally with permissions to create resources like MySQL databases and networks.

### Existing Hosted SQL Database
If you also already have a database that you would want to use with the deployment, you can choose to configure it with the use of the config file. Here we will demonstrate setting the database.

> **Note**
> Only MySQL version 5.7.x are supported by ZenML, currently.

- Fill the fields below from the config file with values from your database.

    ```
    database_username: The username for the database.
    database_password: The password for the database.
    
    database_url: The URL of the database to use for the ZenML server.
    database_ssl_ca: The path to the SSL CA certificate to use for the
        database connection.
    database_ssl_cert: The path to the client SSL certificate to use for the
        database connection.
    database_ssl_key: The path to the client SSL key to use for the
        database connection.
    database_ssl_verify_server_cert: Whether to verify the database server
        SSL certificate.
    ```

- Run the `deploy` command and pass the config file above to it.

    ```
    zenml deploy --config=/PATH/TO/FILE
    ```
    > **Note**
    > To be able to run the deploy command, you should have your cloud provider's CLI configured locally with permissions to create resources like MySQL databases and networks.



## Configuration File Templates

### Base Config File
This is the general structure of a config file. Use this as a base and then add any cloud-specific parameters from the sections below. 

> **Note**
> Feel free to include only those variables that you want to customize, in your file. For all other variables, the defaults (specified in square brackets) would be used.

<details>
    <summary>General</summary>

```
name: Name of the server deployment.
provider: The server provider type. # one of aws, gcp or azure
username: The username for the default ZenML server account.
password: The password for the default ZenML server account.

kubectl_config_path: The path to the kubectl config file to use for
    deployment.
namespace [zenmlserver]: The Kubernetes namespace to deploy the ZenML server to.
helm_chart: The path to the ZenML server helm chart to use for
    deployment.
zenmlserver_image_tag [latest]: The tag to use for the ZenML server Docker image.

create_ingress_controller [true]: Whether to deploy an nginx ingress
    controller as part of the deployment.
ingress_tls [true]: Whether to use TLS for the ingress.
ingress_tls_generate_certs [true]: Whether to generate self-signed TLS
    certificates for the ingress.
ingress_tls_secret_name [zenml-tls-certs]: The name of the Kubernetes secret to use for
    the ingress.
ingress_path [""]: The path to use for the ingress.
ingress_controller_hostname: The ingress controller hostname to use for
    the ingress self-signed certificate and to compute the ZenML server
    URL.

deploy_db [true]: Whether to create a SQL database service as part of the recipe.
database_username [admin]: The username for the database.
database_password: The password for the database.
database_url: The URL of the database to use for the ZenML server.
database_ssl_ca: The path to the SSL CA certificate to use for the
    database connection.
database_ssl_cert: The path to the client SSL certificate to use for the
    database connection.
database_ssl_key: The path to the client SSL key to use for the
    database connection.
database_ssl_verify_server_cert: Whether to verify the database server
    SSL certificate.

log_level [ERROR]: The log level to set the terraform client to. Choose one of
    TRACE, DEBUG, INFO, WARN or ERROR (case insensitive).
```

</details>

### Cloud specific settings

{% tabs %}
{% tab title="AWS" %}

```
region [eu-west-1]: The AWS region to deploy to.

rds_name [zenmlserver]: The name of the RDS instance to create
db_name [zenmlserver]: Name of RDS database to create.
db_type [mysql]: Type of RDS database to create.
db_version [5.7.38]: Version of RDS database to create.
db_instance_class [db.t3.micro]: Instance class of RDS database to create.
db_allocated_storage [5]: Allocated storage of RDS database to create.
```

The `database_username` and `database_password` from the general config is used to set those variables for the AWS RDS instance.

{% endtab %}

{% tab title="GCP" %}

```
project_id: The project in GCP to deploy the server to.
region [europe-west3]: The GCP region to deploy to.

cloudsql_name [zenmlserver]: The name of the CloudSQL instance to create
db_name [zenmlserver]: Name of CloudSQL database to create.
db_instance_tier [db-n1-standard-1]: Instance class of CloudSQL database to create.
db_disk_size [10]: Allocated storage of CloudSQL database, in GB, to create.
```

- The `project_id` is required to be set.
- The `database_username` and `database_password` from the general config is used to set those variables for the CloudSQL instance.
- SSL is disabled by default on the database and option to enable it is coming soon!

{% endtab %}

{% tab title="Azure" %}

```
resource_group [zenml]: The Azure resource_group to deploy to.

db_instance_name [zenmlserver]: The name of the Flexible MySQL instance to create
db_name [zenmlserver]: Name of RDS database to create.
db_version [5.7]: Version of MySQL database to create.
db_sku_name [B_Standard_B1s]: The sku_name for the database resource.
db_disk_size [20]: Allocated storage of MySQL database to create.
```
The `database_username` and `database_password` from the general config is used to set those variables for the Azure Flexible MySQL server.

{% endtab %}
{% endtabs %}

## Connecting to deployed ZenML

Once ZenML is deployed, one or multiple users can connect to with the
`zenml connect` command. If no arguments are supplied, ZenML
will attempt to connect to the last ZenML server deployed from the local host using the `zenml deploy` command:

### ZenML Connect: Various options

```bash
zenml connect
```

To connect to a ZenML server, you can either pass the configuration as command
line arguments or as a YAML file:

```bash
zenml connect --url=https://zenml.example.com:8080 --username=admin --no-verify-ssl
```

or

```bash
zenml connect --config=/path/to/zenml_server_config.yaml
```

The YAML file should have the following structure when connecting to a ZenML
server:

```yaml
url: <The URL of the ZenML server>
username: <The username to use for authentication>
password: <The password to use for authentication>
verify_ssl: |
   <Either a boolean, in which case it controls whether the
   server's TLS certificate is verified, or a string, in which case it
   must be a path to a CA certificate bundle to use or the CA bundle
   value itself>
```

Example of a ZenML server YAML configuration file:

```yaml
url: https://ac8ef63af203226194a7725ee71d85a-7635928635.us-east-1.elb.amazonaws.com/zenml
username: admin
password: Pa$$word123
verify_ssl: |
-----BEGIN CERTIFICATE-----
MIIDETCCAfmgAwIBAgIQYUmQg2LR/pHAMZb/vQwwXjANBgkqhkiG9w0BAQsFADAT
MREwDwYDVQQDEwh6ZW5tbC1jYTAeFw0yMjA5MjYxMzI3NDhaFw0yMzA5MjYxMzI3
...
ULnzA0JkRWRnFqH6uXeJo1KAVqtxn1xf8PYxx3NlNDr9wi8KKwARf2lwm6sH4mvq
1aZ/0iYnGKCu7rLJzxeguliMf69E
-----END CERTIFICATE-----
```

Both options can be combined, in which case the command line arguments will
override the values in the YAML file. For example, it is possible and
recommended that you supply the password only as a command line argument:

```bash
zenml connect --username zenml --password=Pa@#$#word --config=/path/to/zenml_server_config.yaml
```

To disconnect from the current ZenML server and revert to using the local default database, use the following command:

```bash
zenml disconnect
```