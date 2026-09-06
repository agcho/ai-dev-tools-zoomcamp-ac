from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Household(models.Model):
    name = models.CharField(max_length=120)
    next_rotation_position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membership",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    rotation_order = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rotation_order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["household", "rotation_order"],
                condition=Q(is_active=True),
                name="unique_household_rotation_order",
            ),
            models.UniqueConstraint(
                fields=["household"],
                condition=Q(role="admin"),
                name="unique_household_admin",
            ),
        ]

    def clean(self):
        super().clean()
        if self.role == self.Role.ADMIN and not self.is_active:
            raise ValidationError({"is_active": "A household admin must be active."})

    def __str__(self):
        return f"{self.user} — {self.household}"


class Chore(models.Model):
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="chores",
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    assignee = models.ForeignKey(
        Membership,
        on_delete=models.PROTECT,
        related_name="assigned_chores",
    )
    creator = models.ForeignKey(
        Membership,
        on_delete=models.PROTECT,
        related_name="created_chores",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        Membership,
        on_delete=models.PROTECT,
        related_name="completed_chores",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["due_date", "created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(completed_at__isnull=True, completed_by__isnull=True)
                    | Q(completed_at__isnull=False, completed_by__isnull=False)
                ),
                name="chore_completion_fields_match",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}

        for field_name in ("assignee", "creator", "completed_by"):
            membership_id = getattr(self, f"{field_name}_id")
            if membership_id is None:
                continue
            belongs_to_household = Membership.objects.filter(
                pk=membership_id,
                household_id=self.household_id,
            ).exists()
            if not belongs_to_household:
                errors[field_name] = "Must belong to the chore's household."

        has_completed_at = self.completed_at is not None
        has_completed_by = self.completed_by_id is not None
        if has_completed_at != has_completed_by:
            errors["completed_at"] = (
                "Completion time and completing member must be set together."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title
