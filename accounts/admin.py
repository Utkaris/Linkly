from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ("-date_joined",)

    list_display = (
        "id",
        "email",
        "username",
        "is_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "is_verified",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name",
    )

    readonly_fields = (
        "date_joined",
        "updated_at",
    )

    fieldsets = (
        (
            "Account Information",
            {
                "fields": (
                    "email",
                    "username",
                    "password",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "is_verified",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "date_joined",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                ),
            },
        ),
    )