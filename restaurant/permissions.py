from rest_framework import permissions


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Object-level permission for bookings.

    Staff may access any booking; other users only their own bookings.
    (The viewset additionally filters its queryset, so other users' bookings
    are not even discoverable.)
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or obj.user_id == user.id))
