# Shared Household Chores — Product Scope

## Goal

Build a responsive Django web app that helps roommates share household chores fairly.

## Core Features

The homework contains exactly three core features:

1. **Create chores with due dates**
   - Only a household admin can create a chore.
   - Every chore has a due date.
   - The admin can edit or delete an incomplete chore.

2. **Assign chores through a shared rotation**
   - The app suggests the next active roommate in an admin-defined order.
   - The admin can override the suggestion.
   - The rotation advances after every new chore, including an override.

3. **Mark chores as completed**
   - The assigned roommate or household admin can complete a chore.
   - The app records who completed it and when.
   - Completion is permanent and requires no note or photo.

## Supporting Requirements

These requirements support the three core features; they are not additional features:

- Every user has a separate account and must log in.
- The app supports multiple households, but a user belongs to only one.
- Each household has one admin who creates and deactivates roommate accounts.
- Deactivated roommates keep their history and leave the assignment rotation.
- Members can view all chores in their household, with their own chores highlighted.
- Members cannot view another household's data.
- Chores appear as upcoming, overdue, or completed.
- Overdue chores remain assigned until completed.
- The assignee receives one email reminder a day before the due date.

## Out of Scope

- Automatically recurring chores
- Self-registration, invitations, or join codes
- Membership in multiple households
- Chore management by regular roommates
- Automatic reassignment of overdue chores
- In-app notifications
- Completion notes or photos
- Reopening completed chores
- Permanent removal of roommate history

## Definition of Done

- An admin can create a chore with a due date.
- The app suggests the correct roommate, permits an override, and advances the rotation.
- The assignee or admin can permanently complete a chore.
- Household permissions and data isolation are enforced.
- The assignee receives one reminder email a day before an incomplete chore is due.
