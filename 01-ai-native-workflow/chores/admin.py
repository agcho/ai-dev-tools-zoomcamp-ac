from django.contrib import admin

from .models import Chore, Household, Membership


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "next_rotation_position", "created_at")
    search_fields = ("name",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "household", "role", "rotation_order", "is_active")
    list_filter = ("role", "is_active", "household")
    search_fields = ("user__username", "household__name")


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ("title", "household", "assignee", "due_date", "completed_at")
    list_filter = ("household", "due_date", "completed_at")
    search_fields = ("title", "description")
