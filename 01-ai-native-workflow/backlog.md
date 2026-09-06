# Shared Household Chores — Django Backlog

## Task 1: Model households, memberships, and chores — Complete

Create the database models and migrations for households, one admin and ordered members, the household's next rotation position, and chores with assignee, due date, and completion details.

**Acceptance criteria**

- Each user belongs to at most one household and has an admin or member role.
- Memberships have an admin-controlled rotation order and active status.
- A chore belongs to one household and stores its assignee, due date, creator, completion time, and completing user.
- Model validation prevents cross-household assignments and allows only one admin per household.
- Migrations apply successfully.

## Task 2: Add login and household authorization — Complete

Configure login and logout, then add reusable authorization rules for household data and admin-only actions.

**Acceptance criteria**

- Anonymous users are redirected to login.
- Users can access chores only from their own household.
- Only the household admin can manage members or create, edit, and delete chores.
- Authorization behavior is covered by focused tests.

## Task 3: Build admin member management — Complete

Let the admin create roommate accounts, set their rotation order, reorder them, and deactivate them without deleting history.

**Acceptance criteria**

- New roommates receive a separate login account in the admin's household.
- The admin can set a unique, deterministic rotation order.
- Deactivated roommates cannot log in and are excluded from future assignments.
- Existing chore and completion history remains intact after deactivation.

## Task 4: Build chore creation and shared rotation

Add the admin chore form with a required due date, suggest the next active roommate, allow an override, and advance the shared rotation after creation.

**Acceptance criteria**

- The form requires a chore description and due date.
- The suggested assignee follows the admin-defined active-member order.
- The admin can select a different active roommate.
- The rotation advances once after every successful creation, including an override.
- Rotation behavior is tested, including inactive members and wraparound.

## Task 5: Add the household chore dashboard

Show every chore in the signed-in user's household in a responsive page, with clear status and personal assignment highlighting.

**Acceptance criteria**

- Users see no chores from other households.
- Chores are labeled upcoming, overdue, or completed.
- The current user's assigned chores are visually distinct.
- Overdue chores remain assigned to their existing roommate.

## Task 6: Add chore editing, deletion, and completion

Let admins edit or delete incomplete chores, and let either the assignee or admin permanently complete a chore.

**Acceptance criteria**

- Only admins can edit or delete incomplete chores.
- Editing an existing chore does not advance the rotation.
- Only the assigned roommate or household admin can complete a chore.
- Completion records who completed the chore and when.
- Completed chores cannot be edited, deleted, reopened, or completed again.

## Task 7: Send due-date email reminders

Create a scheduled management command that emails an assignee one day before an incomplete chore is due.

**Acceptance criteria**

- The command finds incomplete chores due the following day.
- Each reminder is sent to the assigned active roommate's email address at most once.
- Completed chores receive no reminder.
- Email behavior is verified with Django's test email backend.

## Task 8: Finish and verify the responsive app

Polish navigation, forms, and responsive styling, then validate the complete workflow against the product scope.

**Acceptance criteria**

- Admin and member workflows work on narrow and wide screens.
- Empty states and validation errors give clear guidance.
- The full automated test suite and `python manage.py check` pass.
- The README contains setup, migration, account bootstrap, run, test, and reminder scheduling instructions.
