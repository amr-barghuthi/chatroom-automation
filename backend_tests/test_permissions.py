from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from types import SimpleNamespace

from apis.permissions import HasGroupPermission
from apis.role.role_model import Role


class HasGroupPermissionTest(TestCase):

    def test_user_with_required_permission_is_allowed(self):
        # Arrange
        group = Group.objects.create(name="QA Test Group")

        permission = Permission.objects.first()
        group.permissions.add(permission)

        role = Role.objects.create(
            name="QA Test Role",
            group=group
        )

        user = SimpleNamespace(
            is_authenticated=True,
            role=role
        )

        request = SimpleNamespace(user=user)

        permission_checker = HasGroupPermission(
            [permission.codename]
        )

        # Act
        result = permission_checker.has_permission(
            request=request,
            view=None
        )

        # Assert
        self.assertTrue(result)


    def test_user_without_required_permission_is_denied(self):
        # Arrange
        group = Group.objects.create(name="QA No Permission Group")

        permission = Permission.objects.first()

        role = Role.objects.create(
            name="QA No Permission Role",
            group=group
        )

        user = SimpleNamespace(
            is_authenticated=True,
            role=role
        )

        request = SimpleNamespace(user=user)

        permission_checker = HasGroupPermission(
            [permission.codename]
        )

        # Act
        result = permission_checker.has_permission(
            request=request,
            view=None
        )

        # Assert
        self.assertFalse(result)


    def test_unauthenticated_user_is_denied(self):
        # Arrange
        user = SimpleNamespace(
            is_authenticated=False
        )

        request = SimpleNamespace(user=user)

        permission_checker = HasGroupPermission(
            ["anything"]
        )

        # Act
        result = permission_checker.has_permission(
            request=request,
            view=None
        )

        # Assert
        self.assertFalse(result)