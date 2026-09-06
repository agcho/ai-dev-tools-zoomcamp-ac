from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import MemberCreationForm
from .models import Chore, Membership
from .permissions import active_membership_required, household_admin_required


@active_membership_required
def dashboard(request):
    chores = Chore.objects.filter(
        household=request.household_membership.household
    ).select_related("assignee__user")
    return render(request, "chores/dashboard.html", {"chores": chores})


@active_membership_required
def chore_detail(request, pk):
    chore = get_object_or_404(
        Chore.objects.select_related("assignee__user", "creator__user"),
        pk=pk,
        household=request.household_membership.household,
    )
    return render(request, "chores/chore_detail.html", {"chore": chore})


@household_admin_required
def household_manage(request):
    memberships = request.household_membership.household.memberships.select_related(
        "user"
    )
    return render(
        request,
        "chores/household_manage.html",
        {
            "household": request.household_membership.household,
            "memberships": memberships,
        },
    )


@household_admin_required
def member_create(request):
    if request.method == "POST":
        form = MemberCreationForm(request.POST)
        if form.is_valid():
            household = request.household_membership.household
            with transaction.atomic():
                user = form.save()
                last_order = household.memberships.filter(is_active=True).aggregate(
                    maximum=Max("rotation_order")
                )["maximum"]
                Membership.objects.create(
                    household=household,
                    user=user,
                    role=Membership.Role.MEMBER,
                    rotation_order=0 if last_order is None else last_order + 1,
                )
            messages.success(request, f"Created account for {user.get_username()}.")
            return redirect("chores:household-manage")
    else:
        form = MemberCreationForm()

    return render(request, "chores/member_form.html", {"form": form})


@require_POST
@household_admin_required
def member_move(request, pk, direction):
    if direction not in {"up", "down"}:
        raise Http404

    household = request.household_membership.household
    with transaction.atomic():
        members = list(
            household.memberships.select_for_update()
            .filter(is_active=True)
            .order_by("rotation_order", "pk")
        )
        member = next((item for item in members if item.pk == pk), None)
        if member is None:
            raise Http404

        index = members.index(member)
        other_index = index - 1 if direction == "up" else index + 1
        if 0 <= other_index < len(members):
            other = members[other_index]
            temporary_order = (
                household.memberships.aggregate(maximum=Max("rotation_order"))[
                    "maximum"
                ]
                or 0
            ) + 1
            Membership.objects.filter(pk=member.pk).update(
                rotation_order=temporary_order
            )
            Membership.objects.filter(pk=other.pk).update(
                rotation_order=member.rotation_order
            )
            Membership.objects.filter(pk=member.pk).update(
                rotation_order=other.rotation_order
            )

    return redirect("chores:household-manage")


@require_POST
@household_admin_required
def member_deactivate(request, pk):
    household = request.household_membership.household
    member = get_object_or_404(
        Membership.objects.select_related("user"),
        pk=pk,
        household=household,
        role=Membership.Role.MEMBER,
        is_active=True,
    )

    with transaction.atomic():
        member.is_active = False
        member.save(update_fields=["is_active"])
        member.user.is_active = False
        member.user.save(update_fields=["is_active"])

        active_members = list(
            household.memberships.select_for_update()
            .filter(is_active=True)
            .order_by("rotation_order", "pk")
        )
        temporary_offset = (
            household.memberships.aggregate(maximum=Max("rotation_order"))["maximum"]
            or 0
        ) + len(active_members) + 1
        for active_member in active_members:
            Membership.objects.filter(pk=active_member.pk).update(
                rotation_order=active_member.rotation_order + temporary_offset
            )
        for order, active_member in enumerate(active_members):
            Membership.objects.filter(pk=active_member.pk).update(rotation_order=order)

        active_count = len(active_members)
        household.next_rotation_position = (
            household.next_rotation_position % active_count if active_count else 0
        )
        household.save(update_fields=["next_rotation_position"])

    messages.success(request, f"Deactivated {member.user.get_username()}.")
    return redirect("chores:household-manage")
