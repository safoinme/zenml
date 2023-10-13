---
description: Learning how to switch the infrastructure backend of your code.
---

# Understand stacks

In the previous section, you might have already noticed the term `stack` in the logs and on the dashboard.

## Stacks

A `stack` is the combination of tools and infrastructure that your pipelines can run on. When you run ZenML code without configuring a stack, the pipeline will run on the so-called `default` stack.

<figure><img src="../../.gitbook/assets/02_pipeline_local_stack.png" alt=""><figcaption><p>ZenML is the translation layer that allows your code to run on any of your stacks</p></figcaption></figure>

#### Separation of code from configuration and infrastructure

As visualized in the diagram above, there are two separate domains that are connected through ZenML. The left side shows the code domain. The user's Python code is translated into a ZenML pipeline. On the right side, you can see the infrastructure domain, in this case, an instance of the `default` stack. By separating these two domains, it is easy to switch the environment that the pipeline runs on without making any changes in the code. It also allows domain experts to write code/configure infrastructure without worrying about the other domain.

#### The `default` stack

{% tabs %}
{% tab title="Dashboard" %}
You can explore all your stacks in the dashboard. When you click on a specific one you can see its configuration and all the pipeline runs that were executed using this stack.

<figure><img src="../../.gitbook/assets/DefaultStack.png" alt=""><figcaption><p>The default stack on the Dashboard</p></figcaption></figure>
{% endtab %}

{% tab title="CLI" %}
`zenml stack describe` lets you find out details about your active stack:

```bash
...
        Stack Configuration        
┏━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━┓
┃ COMPONENT_TYPE │ COMPONENT_NAME ┃
┠────────────────┼────────────────┨
┃ ARTIFACT_STORE │ default        ┃
┠────────────────┼────────────────┨
┃ ORCHESTRATOR   │ default        ┃
┗━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━┛
     'default' stack (ACTIVE)      
Stack 'default' with id '...' is owned by user default and is 'private'.
...
```

`zenml stack list` lets you see all stacks that are registered in your zenml deployment.

```bash
...
┏━━━━━━━━┯━━━━━━━━━━━━┯━━━━━━━━━━━┯━━━━━━━━┯━━━━━━━━━┯━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━┓
┃ ACTIVE │ STACK NAME │ STACK ID  │ SHARED │ OWNER   │ ARTIFACT_STORE │ ORCHESTRATOR ┃
┠────────┼────────────┼───────────┼────────┼─────────┼────────────────┼──────────────┨
┃   👉   │ default    │ ...       │ ➖     │ default │ default        │ default      ┃
┗━━━━━━━━┷━━━━━━━━━━━━┷━━━━━━━━━━━┷━━━━━━━━┷━━━━━━━━━┷━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━┛
...
```

{% hint style="info" %}
As you can see a stack can be **active** on your **client**. This simply means that any pipeline you run will be using the **active stack** as its environment.
{% endhint %}
{% endtab %}
{% endtabs %}

## Components of a stack

As you can see in the section above, a stack consists of multiple components. All stacks have at minimum an **orchestrator** and an **artifact store**.

### Orchestrator

The **orchestrator** is responsible for executing the pipeline code. In the simplest case, this will be a simple Python thread on your machine. Let's explore this default orchestrator.

{% tabs %}
{% tab title="Dashboard" %}
<figure><img src="../../.gitbook/assets/DefaultOrch.png" alt=""><figcaption><p>Default orchestrator in the dashboard.</p></figcaption></figure>
{% endtab %}

{% tab title="CLI" %}
`zenml orchestrator list` lets you see all orchestrators that are registered in your zenml deployment.

```bash
┏━━━━━━━━┯━━━━━━━━━┯━━━━━━━━━━━━━━┯━━━━━━━━┯━━━━━━━━┯━━━━━━━━━┓
┃ ACTIVE │ NAME    │ COMPONENT ID │ FLAVOR │ SHARED │ OWNER   ┃
┠────────┼─────────┼──────────────┼────────┼────────┼─────────┨
┃   👉   │ default │ ...          │ local  │ ➖     │ default ┃
┗━━━━━━━━┷━━━━━━━━━┷━━━━━━━━━━━━━━┷━━━━━━━━┷━━━━━━━━┷━━━━━━━━━┛
```
{% endtab %}
{% endtabs %}

### Artifact store

The **artifact store** is responsible for persisting the step outputs. As we learned in the previous section, the step outputs are not passed along in memory, rather the outputs of each step are stored in the **artifact store** and then loaded from there when the next step needs them. By default this will also be on your own machine:

{% tabs %}
{% tab title="Dashboard" %}
<figure><img src="../../.gitbook/assets/DefaultArtifactStore.png" alt=""><figcaption><p>Default artifact store in the dashboard.</p></figcaption></figure>
{% endtab %}

{% tab title="CLI" %}
`zenml artifact-store list` lets you see all artifact stores that are registered in your zenml deployment.

```bash
┏━━━━━━━━┯━━━━━━━━━┯━━━━━━━━━━━━━━┯━━━━━━━━┯━━━━━━━━┯━━━━━━━━━┓
┃ ACTIVE │ NAME    │ COMPONENT ID │ FLAVOR │ SHARED │ OWNER   ┃
┠────────┼─────────┼──────────────┼────────┼────────┼─────────┨
┃   👉   │ default │ ...          │ local  │ ➖     │ default ┃
┗━━━━━━━━┷━━━━━━━━━┷━━━━━━━━━━━━━━┷━━━━━━━━┷━━━━━━━━┷━━━━━━━━━┛
```
{% endtab %}
{% endtabs %}

{% hint style="info" %}
There are many more components that you can add to your stacks, like experiment trackers, model deployers, and more. You can see all supported stack component types in a single table view [here](../../stacks-and-components/component-guide/component-guide.md)
{% endhint %}

## Registering a stack

Just to illustrate how to interact with stacks, let's create an alternate local stack. We start by first creating a local artifact store.

### Create an artifact store

{% tabs %}
{% tab title="Dashboard" %}
<figure><img src="../../.gitbook/assets/CreateArtifactStore.png" alt=""><figcaption><p>Creating an Artifact Store in the dashboard.</p></figcaption></figure>
{% endtab %}

{% tab title="CLI" %}
```bash
zenml artifact-store register my_artifact_store --flavor=local 
```

Let's understand the individual parts of this command:

* `artifact-store` : This describes the top-level group, to find other stack components simply run `zenml --help`
* `register` : Here we want to register a new component, instead, we could also `update` , `delete` and more `zenml artifact-store --help` will give you all possibilities
* `my_artifact_store` : This is the unique name that the stack component will have.
* `--flavor=local`: A flavor is a possible implementation for a stack component. So in the case of an artifact store, this could be an s3-bucket or a local filesystem. You can find out all possibilities with `zenml artifact-store flavor --list`

This will be the output that you can expect from the command above.

```bash
Using the default local database.
Running with active workspace: 'default' (global)
Running with active stack: 'default' (global)
Successfully registered artifact_store `my_artifact_store`.bash
```

To see the new artifact store that you just registered, just run:

```bash
zenml artifact-store describe my_artifact_store
```
{% endtab %}
{% endtabs %}

### Create a local stack

With the artifact store created, we can now create a new stack with this artifact store.

{% tabs %}
{% tab title="Dashboard" %}
<figure><img src="../../.gitbook/assets/CreateStack.png" alt=""><figcaption><p>Register a new stack.</p></figcaption></figure>
{% endtab %}

{% tab title="CLI" %}
```bash
zenml stack register my_stack -o default -a my_artifact_store
```

* `stack` : This is the CLI group that enables interactions with the stacks
* `register`: Here we want to register a new stack. Explore other operations with`zenml stack --help`.
* `my_stack` : This is the unique name that the stack will have.
* `--orchestrator` or `-o` are used to specify which orchestrator to use for the stack
* `--artifact-store` or `-a` are used to specify which artifact store to use for the stack

The output for the command should look something like this:

```bash
Using the default local database.
Running with active workspace: 'default' (repository)
Stack 'my_stack' successfully registered!
```

You can inspect the stack with the following command:

```bash
 zenml stack describe my_stack
```

Which will give you an output like this:

```bash
         Stack Configuration          
┏━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━┓
┃ COMPONENT_TYPE │ COMPONENT_NAME    ┃
┠────────────────┼───────────────────┨
┃ ORCHESTRATOR   │ default           ┃
┠────────────────┼───────────────────┨
┃ ARTIFACT_STORE │ my_artifact_store ┃
┗━━━━━━━━━━━━━━━━┷━━━━━━━━━━━━━━━━━━━┛
           'my_stack' stack           
Stack 'my_stack' with id '...' is owned by user default and is 'private'.
```
{% endtab %}
{% endtabs %}

To run a pipeline using the new stack:

1.  Set the stack as active on your client

    ```bash
    zenml stack set my_stack
    ```
2.  Run your pipeline code (you can use the code from the [previous section](create-an-ml-pipeline.md))

    ```bash
    python run.py
    ```

Before we can move on to using a cloud stack, we need to find out more about the ZenML server in the next section.

<!-- For scarf -->
<figure><img alt="ZenML Scarf" referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=f0b4f458-0a54-4fcd-aa95-d5ee424815bc" /></figure>
