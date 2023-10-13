# User Management

In ZenML Cloud, there is a slightly different entity hierarchy as compared to the open-source ZenML
framework. This document walks you through the key differences and new concepts that are cloud-only.
## Organizations, Tenants, and Roles

ZenML Cloud arranges various aspects of your work experience around the concept
of an **Organization**. This is the top-most level structure within the ZenML
Cloud environment. Generally, an organization contains a group of users and one
or more **tenants**. Tenants are individual, isolated deployments of the ZenML server.

Every user in an organization has a distinct role. Each role configures what
they can view, modify, and their level of involvement in collaborative tasks. A
role thus helps determine the level of access that a user has within an
organization.

The `admin` has all permissions on an organization. They are allowed to add
members, adjust the billing information and assign roles. The `editor` can still
fully manage tenants and members but is not allowed to access the subscription
information or delete the organization. The `viewer` Role allows you to allow
users to access the tenants within the organization with only view permissions.

## Inviting Team Members

Inviting users to your organization to work on the organization's tenants is
easy. Simply click `Add Member` in the Organization settings, and give them an
initial Role. The User will be sent an invitation email. If a user is part of an
organization, they can utilize their login on all tenants they have authority to
access.

### Device-to-device authentication

{% hint style="info" %}
We are actively developing low privilege service accounts and will update this
when they are implemented. For the time being all workloads (like for example a
pipeline run) will get an irrevocable API Token that is valid for 24h - please
reach out to us in case longer-lasting tokens are needed for your Tenants.
{% endhint %}
