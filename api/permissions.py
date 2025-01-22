# beDoggo/permissions.py

from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """
    Permiso para permitir acceso solo al dueño del objeto o a un administrador.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.owner == request.user
