---
description: We answer the most frequently asked questions about ZenML here.
---

# FAQ

#### How does ZenML compare to orchestrators (Airflow, Kubeflow, Flyte, etc.)?

An orchestrator in MLOps is the system component that is responsible for executing and managing the execution of a ML pipeline. ZenML pipelines can be run on multiple orchestration systems. There are [standard orchestrators](../extending-zenml/orchestrator.md) that ZenML supports out-of-the-box, but you are encourage to write your own [orchestrator](../extending-zenml/orchestrator.md) in order to gain more control as to exactly how your pipelines are executed!

#### Can I use tool X? How does tool Y integrate with ZenML?

Take a look at our [examples](https://github.com/zenml-io/zenml/tree/main/examples) directory, which showcases detailed examples for each integration that ZenML supports out-of-the-box.

The ZenML team and community is constantly working to include more tools and integrations to the above list (check out the [roadmap](https://zenml.io/roadmap) for more details). You can [upvote features](https://zenml.io/discussion) you'd like and add your ideas to the roadmap.

#### How can I make ZenML work with my custom tool? How can I extend or build on ZenML?

This depends on the tool and its respective MLOps category. We have a full guide on this over [here](../extending-zenml/)!

#### Why did you build ZenML?

We built it because we scratched our own itch while deploying multiple machine learning models in production for the past three years. Our team struggled to find a simple yet production-ready solution whilst developing large-scale ML pipelines, and built a solution for it that we are now proud to share with all of you!

#### How can I contribute?

We would love to develop ZenML together with our community! The best way to get
started is to select any issue from the [`good-first-issue`
label](https://github.com/zenml-io/zenml/labels/good%20first%20issue). If you
would like to contribute, please review our [Contributing
Guide](https://github.com/zenml-io/zenml/blob/main/CONTRIBUTING.md) for all relevant details.

#### How can I learn more about MLOps?

Check out [ZenBytes](https://github.com/zenml-io/zenbytes), where you learn MLOps concepts 
in a practical manner with the ZenML framework. Other great resources are:

* [MadeWithML](https://madewithml.com/)
* [Full Stack Deep Learning](https://fullstackdeeplearning.com/)
* [CS 329S: Machine Learning Systems Design](https://stanford-cs329s.github.io/)

#### Why should I use ZenML?

ZenML pipelines are designed to be written early on the development lifecycle. Data scientists can explore their pipelines as they develop towards production, switching stacks from local to cloud deployments with ease. You can read more about why we started building ZenML [on our blog](https://blog.zenml.io/). By using ZenML in the early stages of your project, you get the following benefits:

* Extensible so you can build out the framework to suit your specific needs
* Reproducibility of training and inference workflows
* A simple and clear way to represent the steps of your pipeline in code
* Batteries-included integrations: bring all your favorite tools together
* Easy switch between local and cloud stacks
* Painless deployment and configuration of infrastructure

#### How can I be sure you'll stick around as a tool?

The [team behind ZenML](https://zenml.io/team) have a shared vision of making MLOps simple and accessible to accelerate problem solving in the world. We recently raised our [seed round](https://venturebeat.com/2021/12/14/open-source-mlops-framework-zenml-raises-2-7m/) to fulfill this vision, and you can be sure we're here to stay!

Plus, ZenML is and always will be an open-source effort, which lowers the risk of it just going away any time soon.

#### How can I speak with the community?

The first point of call should be [our Slack group](https://zenml.io/slack-invite/).
Ask your questions about bugs or specific use cases and someone from the core
team will respond.

#### Which license does ZenML use?

ZenML is distributed under the terms of the Apache License Version 2.0. A
complete version of the license is available in the [LICENSE.md](https://github.com/zenml-io/zenml/blob/main/LICENSE) in this repository. Any contribution made to this project will be licensed under the Apache License Version 2.0.
