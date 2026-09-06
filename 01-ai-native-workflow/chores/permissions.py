from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Membership


def active_membership_required(view_func):
    """Require login and attach the user's active membership to the request."""

    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        try:
            membership = request.user.membership
        except Membership.DoesNotExist as exc:
            raise PermissionDenied("An active household membership is required.") from exc

        if not membership.is_active:
            raise PermissionDenied("An active household membership is required.")

        request.household_membership = membership
        return view_func(request, *args, **kwargs)

    return wrapped


def household_admin_required(view_func):
    """Require the active admin role for the user's household."""

    @active_membership_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.household_membership.role != Membership.Role.ADMIN:
            raise PermissionDenied("Household admin access is required.")
        return view_func(request, *args, **kwargs)

    return wrapped

