from django.urls import path

from . import views

app_name = "chores"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("chores/<int:pk>/", views.chore_detail, name="chore-detail"),
    path("household/manage/", views.household_manage, name="household-manage"),
    path("household/members/new/", views.member_create, name="member-create"),
    path(
        "household/members/<int:pk>/move/<str:direction>/",
        views.member_move,
        name="member-move",
    ),
    path(
        "household/members/<int:pk>/deactivate/",
        views.member_deactivate,
        name="member-deactivate",
    ),
]
