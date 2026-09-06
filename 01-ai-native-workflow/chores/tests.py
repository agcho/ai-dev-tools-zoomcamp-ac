from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Chore, Household, Membership


class HouseholdModelTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.household = Household.objects.create(name="Harbour House")

    def make_membership(self, username, *, household=None, role="member", order=0):
        user = self.user_model.objects.create_user(username=username)
        return Membership.objects.create(
            household=household or self.household,
            user=user,
            role=role,
            rotation_order=order,
        )

    def test_user_can_belong_to_only_one_household(self):
        member = self.make_membership("alex")
        other_household = Household.objects.create(name="Garden Flat")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Membership.objects.create(
                household=other_household,
                user=member.user,
                rotation_order=0,
            )

    def test_household_can_have_only_one_admin(self):
        self.make_membership("admin-one", role=Membership.Role.ADMIN, order=0)

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_membership(
                "admin-two",
                role=Membership.Role.ADMIN,
                order=1,
            )

    def test_rotation_order_is_unique_within_household(self):
        self.make_membership("alex", order=0)

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_membership("sam", order=0)

    def test_admin_must_be_active(self):
        admin = Membership(
            household=self.household,
            user=self.user_model.objects.create_user(username="inactive-admin"),
            role=Membership.Role.ADMIN,
            rotation_order=0,
            is_active=False,
        )

        with self.assertRaises(ValidationError):
            admin.full_clean()

    def test_chore_rejects_cross_household_memberships(self):
        creator = self.make_membership(
            "admin",
            role=Membership.Role.ADMIN,
            order=0,
        )
        other_household = Household.objects.create(name="Garden Flat")
        outsider = self.make_membership(
            "outsider",
            household=other_household,
            order=0,
        )
        chore = Chore(
            household=self.household,
            title="Clean the kitchen",
            due_date=date(2026, 9, 12),
            assignee=outsider,
            creator=creator,
        )

        with self.assertRaises(ValidationError) as context:
            chore.full_clean()

        self.assertIn("assignee", context.exception.message_dict)

    def test_chore_rejects_cross_household_creator_and_completer(self):
        member = self.make_membership("alex", order=0)
        other_household = Household.objects.create(name="Garden Flat")
        outsider = self.make_membership(
            "outsider",
            household=other_household,
            order=0,
        )
        chore = Chore(
            household=self.household,
            title="Clean the kitchen",
            due_date=date(2026, 9, 12),
            assignee=member,
            creator=outsider,
            completed_at="2026-09-10T12:00:00Z",
            completed_by=outsider,
        )

        with self.assertRaises(ValidationError) as context:
            chore.full_clean()

        self.assertIn("creator", context.exception.message_dict)
        self.assertIn("completed_by", context.exception.message_dict)

    def test_completion_fields_must_be_set_together(self):
        member = self.make_membership("alex", order=0)
        chore = Chore(
            household=self.household,
            title="Take out the rubbish",
            due_date=date(2026, 9, 12),
            assignee=member,
            creator=member,
            completed_by=member,
        )

        with self.assertRaises(ValidationError) as context:
            chore.full_clean()

        self.assertIn("completed_at", context.exception.message_dict)


class HouseholdAuthorizationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.household = Household.objects.create(name="Harbour House")
        self.admin_user = user_model.objects.create_user(
            username="admin",
            password="test-password",
        )
        self.admin_membership = Membership.objects.create(
            household=self.household,
            user=self.admin_user,
            role=Membership.Role.ADMIN,
            rotation_order=0,
        )
        self.member_user = user_model.objects.create_user(
            username="member",
            password="test-password",
        )
        self.member_membership = Membership.objects.create(
            household=self.household,
            user=self.member_user,
            rotation_order=1,
        )

        self.other_household = Household.objects.create(name="Garden Flat")
        self.other_user = user_model.objects.create_user(username="other")
        self.other_membership = Membership.objects.create(
            household=self.other_household,
            user=self.other_user,
            role=Membership.Role.ADMIN,
            rotation_order=0,
        )
        self.other_chore = Chore.objects.create(
            household=self.other_household,
            title="Clean the kitchen",
            due_date=date(2026, 9, 12),
            assignee=self.other_membership,
            creator=self.other_membership,
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("chores:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('chores:dashboard')}",
        )

    def test_member_can_access_household_dashboard(self):
        self.client.force_login(self.member_user)

        response = self.client.get(reverse("chores:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.household.name)

    def test_user_cannot_access_chore_from_another_household(self):
        self.client.force_login(self.member_user)

        response = self.client.get(
            reverse("chores:chore-detail", args=[self.other_chore.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_regular_member_cannot_access_admin_view(self):
        self.client.force_login(self.member_user)

        response = self.client.get(reverse("chores:household-manage"))

        self.assertEqual(response.status_code, 403)

    def test_household_admin_can_access_admin_view(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("chores:household-manage"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.household.name)

    def test_authenticated_user_without_membership_is_forbidden(self):
        user = get_user_model().objects.create_user(username="no-household")
        self.client.force_login(user)

        response = self.client.get(reverse("chores:dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_inactive_membership_is_forbidden(self):
        self.member_membership.is_active = False
        self.member_membership.save(update_fields=["is_active"])
        self.client.force_login(self.member_user)

        response = self.client.get(reverse("chores:dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_logout_redirects_to_login(self):
        self.client.force_login(self.member_user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))


class MemberManagementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.household = Household.objects.create(name="Harbour House")
        self.admin_user = user_model.objects.create_user(
            username="admin",
            password="test-password",
        )
        self.admin = Membership.objects.create(
            household=self.household,
            user=self.admin_user,
            role=Membership.Role.ADMIN,
            rotation_order=0,
        )
        self.member_user = user_model.objects.create_user(
            username="alex",
            password="test-password",
        )
        self.member = Membership.objects.create(
            household=self.household,
            user=self.member_user,
            rotation_order=1,
        )

    def test_admin_can_create_roommate_account(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("chores:member-create"),
            {
                "username": "sam",
                "email": "sam@example.com",
                "password1": "a-strong-test-password-2026",
                "password2": "a-strong-test-password-2026",
            },
        )

        self.assertRedirects(response, reverse("chores:household-manage"))
        membership = Membership.objects.get(user__username="sam")
        self.assertEqual(membership.household, self.household)
        self.assertEqual(membership.role, Membership.Role.MEMBER)
        self.assertEqual(membership.rotation_order, 2)
        self.assertTrue(
            membership.user.check_password("a-strong-test-password-2026")
        )

    def test_regular_member_cannot_create_account(self):
        self.client.force_login(self.member_user)

        response = self.client.get(reverse("chores:member-create"))

        self.assertEqual(response.status_code, 403)

    def test_admin_can_reorder_members(self):
        second_user = get_user_model().objects.create_user(username="sam")
        second_member = Membership.objects.create(
            household=self.household,
            user=second_user,
            rotation_order=2,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("chores:member-move", args=[self.member.pk, "down"])
        )

        self.assertRedirects(response, reverse("chores:household-manage"))
        self.member.refresh_from_db()
        second_member.refresh_from_db()
        self.assertEqual(self.member.rotation_order, 2)
        self.assertEqual(second_member.rotation_order, 1)

    def test_deactivation_preserves_history_and_disables_login(self):
        chore = Chore.objects.create(
            household=self.household,
            title="Clean the bathroom",
            due_date=date(2026, 9, 12),
            assignee=self.member,
            creator=self.admin,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("chores:member-deactivate", args=[self.member.pk])
        )

        self.assertRedirects(response, reverse("chores:household-manage"))
        self.member.refresh_from_db()
        self.member_user.refresh_from_db()
        chore.refresh_from_db()
        self.assertFalse(self.member.is_active)
        self.assertFalse(self.member_user.is_active)
        self.assertEqual(chore.assignee, self.member)
        self.client.logout()
        self.assertFalse(
            self.client.login(username="alex", password="test-password")
        )

    def test_deactivation_compacts_rotation_and_normalizes_next_position(self):
        second_user = get_user_model().objects.create_user(username="sam")
        second_member = Membership.objects.create(
            household=self.household,
            user=second_user,
            rotation_order=2,
        )
        self.household.next_rotation_position = 2
        self.household.save(update_fields=["next_rotation_position"])
        self.client.force_login(self.admin_user)

        self.client.post(
            reverse("chores:member-deactivate", args=[self.member.pk])
        )

        self.admin.refresh_from_db()
        second_member.refresh_from_db()
        self.household.refresh_from_db()
        self.assertEqual(self.admin.rotation_order, 0)
        self.assertEqual(second_member.rotation_order, 1)
        self.assertEqual(self.household.next_rotation_position, 0)

    def test_admin_cannot_manage_member_from_another_household(self):
        other_household = Household.objects.create(name="Garden Flat")
        other_user = get_user_model().objects.create_user(username="outsider")
        outsider = Membership.objects.create(
            household=other_household,
            user=other_user,
            rotation_order=0,
        )
        self.client.force_login(self.admin_user)

        move_response = self.client.post(
            reverse("chores:member-move", args=[outsider.pk, "up"])
        )
        deactivate_response = self.client.post(
            reverse("chores:member-deactivate", args=[outsider.pk])
        )

        self.assertEqual(move_response.status_code, 404)
        self.assertEqual(deactivate_response.status_code, 404)
        outsider.refresh_from_db()
        self.assertTrue(outsider.is_active)

    def test_admin_cannot_be_deactivated(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("chores:member-deactivate", args=[self.admin.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_member_management_changes_require_post(self):
        self.client.force_login(self.admin_user)

        move_response = self.client.get(
            reverse("chores:member-move", args=[self.member.pk, "up"])
        )
        deactivate_response = self.client.get(
            reverse("chores:member-deactivate", args=[self.member.pk])
        )

        self.assertEqual(move_response.status_code, 405)
        self.assertEqual(deactivate_response.status_code, 405)
