# Shared Household Chores

A responsive Django web application for roommates to manage household chores fairly through a shared assignment rotation.

## Core Features

1. Admins create chores and set due dates.
2. Chores are assigned through a household rotation, with an admin override.
3. Assigned roommates or admins mark chores as completed.

These are the three features included in the homework scope. Authentication, household permissions, member management, chore status display, and email delivery support these features.

The app supports multiple households. Each user has a separate account and belongs to one household. Household members can see all chores in their household, while only the admin can manage chores, members, and rotation order.

An email reminder is sent to the assigned roommate one day before a chore is due. Overdue chores remain assigned until completion.

## Documentation

- [Product scope and plan](_docs/plan.md)

## Technology

- Python
- Django
- Django templates and responsive CSS
- A relational database supported by Django

## Project Status

Planning and Django project setup are complete. Backlog tasks 1 through 3 are
implemented, covering the data model, authentication, household authorization,
and admin management of roommate accounts and rotation order.
