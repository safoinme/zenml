---
description: Annotating data using Label Studio.
---

# Label Studio

Label Studio is one of the leading open-source annotation platforms available to data scientists and ML practitioners.
It is used to create or edit datasets that you can then use as part of training or validation workflows. It supports a
broad range of annotation types, including:

* Computer Vision (image classification, object detection, semantic segmentation)
* Audio & Speech (classification, speaker diarization, emotion recognition, audio transcription)
* Text / NLP (classification, NER, question answering, sentiment analysis)
* Time Series (classification, segmentation, event recognition)
* Multi-Modal / Domain (dialogue processing, OCR, time series with reference)

### When would you want to use it?

If you need to label data as part of your ML workflow, that is the point at which you could consider adding the optional
annotator stack component as part of your ZenML stack.

We currently support the use of annotation at the various stages described
in [the main annotators docs page](annotators.md), and also offer custom utility functions to generate Label Studio
label config files for image classification and object detection. (More will follow in due course.)

The Label Studio integration currently is built to support workflows using the following three cloud artifact stores:
AWS S3, GCP/GCS, and Azure Blob Storage. Purely local stacks will currently _not_ work if you want to do add the
annotation stack component as part of your stack.

{% hint style="info" %}
COMING SOON: The Label Studio Integration supports the use of annotations in an ML workflow, but we do not currently
handle the universal conversion between data formats as part of the training workflow. Our initial use case was built to
support image classification and object detection, but we will add helper steps and functions for other use cases in due
course. We will update the docs when we enable this functionality.
{% endhint %}

### How to deploy it?

The Label Studio Annotator flavor is provided by the Label Studio ZenML integration, you need to install it, to be able
to register it as an Annotator and add it to your stack:

```shell
zenml integration install label_studio
```

{% hint style="warning" %}
There is a known issue with Label Studio installations via `zenml integration install...`. You might find that the Label
Studio installation breaks the ZenML CLI. In this case, please run `pip install 'pydantic<1.11,>=1.9.0'` to fix the
issue or [message us on Slack](https://zenml.io/slack-invite) if you need more help with this. We are working on a more
definitive fix.
{% endhint %}

The following instructions below offer a general guide to the parts that need attention when deploying/using the Label
Studio stack component and integration.
The [`label_studio_annotation` example](https://github.com/zenml-io/zenml/tree/develop/examples/label\_studio\_annotation)
offers a detailed guide for each cloud provider on how to set it up.

Before registering a `label_studio` flavor stack component as part of your stack, you'll need to have registered a cloud
artifact store. (See the docs on how to register and set
up[ a cloud artifact store](/docs/book/stacks-and-components/component-guide/artifact-stores/artifact-stores.md).)

Be sure to register a secret for whichever artifact store you choose, and then you should make sure to pass the name of
that secret into the artifact store as the `--authentication_secret`
as [described in this guide](/docs/book/stacks-and-components/component-guide/artifact-stores/s3.md#advanced-configuration), 
for example in the case of AWS.

You will next need to obtain your Label Studio API key. This will give you access to the web annotation interface. (The
following steps apply to a local instance of Label Studio, but feel free to obtain your API key directly from your
deployed instance if that's what you are using.)

```shell
# choose a username and password for your label-studio account
label-studio reset_password --username <USERNAME> --password <PASSWORD>
# start a local label-studio instance
label-studio start -p 8093
```

Then visit [http://localhost:8093/](http://localhost:8093/) to log in, and then
visit [http://localhost:8093/user/account](http://localhost:8093/user/account) and get your Label Studio API key (from
the upper right-hand corner). You will need it for the next step. Keep the Label Studio server running, because the
ZenML Label Studio annotator will use it as the backend.

At this point you should register the API key under a custom secret name, making sure to replace the two parts in `<>`
with whatever you choose:

```shell
zenml secret create <LABEL_STUDIO_SECRET_NAME> --api_key="<your_label_studio_api_key>"
```

Then register your annotator with ZenML:

```shell
zenml annotator register label_studio --flavor label_studio --authentication_secret="<LABEL_STUDIO_SECRET_NAME>"

# for deployed instances of Label Studio, you can also pass in the URL as follows, for example:
# zenml annotator register label_studio --flavor label_studio --authentication_secret="<LABEL_STUDIO_SECRET_NAME>" --instance_url="<your_label_studio_url>" --port=80
```

When using a deployed instance of Label Studio, the instance URL must be specified without any trailing `/` at the end.
You should specify the port, for example, port 80 for a standard HTTP connection.

Finally, add all these components to a stack and set it as your active stack. For example:

```shell
zenml stack copy annotation
zenml stack update annotation -a <YOUR_CLOUD_ARTIFACT_STORE>
# this must be done separately so that the other required stack components are first registered
zenml stack update annotation -an <YOUR_LABEL_STUDIO_ANNOTATOR>
zenml stack set annotation
# optionally also
zenml stack describe
```

Now if you run a simple CLI command like `zenml annotator dataset list` this should work without any errors. You're
ready to use your annotator in your ML workflow!

### How do you use it?

ZenML assumes that users have registered a cloud artifact store and an annotator as described above. ZenML currently
only supports this setup, but we will add in the fully local stack option in the future.

ZenML supports access to your data and annotations via the `zenml annotator ...` CLI command.

You can access information about the datasets you're using with the `zenml annotator dataset list`. To work on
annotation for a particular dataset, you can run `zenml annotator dataset annotate <dataset_name>`.

[Our full continuous annotation/training example](https://github.com/zenml-io/zenml/tree/develop/examples/label\_studio\_annotation)
is the best place to see how all the pieces of making this integration work fit together. What follows is an overview of
some key components to the Label Studio integration and how it can be used.

#### Label Studio Annotator Stack Component

Our Label Studio annotator component inherits from the `BaseAnnotator` class. There are some methods that are core
methods that must be defined, like being able to register or get a dataset. Most annotators handle things like the
storage of state and have their own custom features, so there are quite a few extra methods specific to Label Studio.

The core Label Studio functionality that's currently enabled includes a way to register your datasets, export any
annotations for use in separate steps as well as start the annotator daemon process. (Label Studio requires a server to
be running in order to use the web interface, and ZenML handles the provisioning of this server locally using the
details you passed in when registering the component unless you've specified that you want to use a deployed instance.)

#### Standard Steps

ZenML offers some standard steps (and their associated config objects) which will get you up and running with the Label
Studio integration quickly. These include:

* `LabelStudioDatasetRegistrationConfig` - a step config object to be used when registering a dataset with Label studio
  using the `get_or_create_dataset` step
* `LabelStudioDatasetSyncConfig` - a step config object to be used when registering a dataset with Label studio using
  the `sync_new_data_to_label_studio` step. Note that this requires a ZenML secret to have been pre-registered with your
  artifact store as being the one that holds authentication secrets specific to your particular cloud provider. (Label
  Studio provides some documentation on what permissions these secrets
  require [here](https://labelstud.io/guide/tasks.html).)
* `get_or_create_dataset` step - This takes a `LabelStudioDatasetRegistrationConfig` config object which includes the
  name of the dataset. If it exists, this step will return the name, but if it doesn't exist then ZenML will register
  the dataset along with the appropriate label config with Label Studio.
* `get_labeled_data` step - This step will get all labeled data available for a particular dataset. Note that these are
  output in a Label Studio annotation format, which will subsequently be converted into a format appropriate for your
  specific use case.
* `sync_new_data_to_label_studio` step - This step is for ensuring that ZenML is handling the annotations and that the
  files being used are stored and synced with the ZenML cloud artifact store. This is an important step as part of a
  continuous annotation workflow since you want all the subsequent steps of your workflow to remain in sync with
  whatever new annotations are being made or have been created.

#### Helper Functions

Label Studio requires the use of what it calls 'label config' when you are creating/registering your dataset. These are
strings containing HTML-like syntax that allow you to define a custom interface for your annotation. ZenML provides
three helper functions that will construct these label config strings in the case of object detection, image
classification, and OCR. See the `integrations.label_studio.label_config_generators` module for those three functions.

A concrete example of using the Label Studio annotator can be
found [here](https://github.com/zenml-io/zenml/tree/develop/examples/label\_studio\_annotation).

<!-- For scarf -->
<figure><img alt="ZenML Scarf" referrerpolicy="no-referrer-when-downgrade" src="https://static.scarf.sh/a.png?x-pxid=f0b4f458-0a54-4fcd-aa95-d5ee424815bc" /></figure>
