from django.shortcuts import render
from rest_framework import permissions, viewsets

from .models import Booking, Menu
from .permissions import IsOwnerOrStaff
from .serializers import BookingSerializer, MenuSerializer


def index(request):
    """Landing page rendered with Django templates (GET /)."""
    menu_items = Menu.objects.filter(inventory__gt=0)[:6]
    return render(request, "index.html", {"menu_items": menu_items})


class MenuViewSet(viewsets.ModelViewSet):
    """
    CRUD for menu items.

    Anyone can read (GET). Creating, updating and deleting requires a valid
    authentication token.
    """

    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class BookingViewSet(viewsets.ModelViewSet):
    """
    CRUD for table bookings. A token is always required.

    Regular users only see and manage their own bookings; staff see all.
    """

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        queryset = Booking.objects.select_related("user")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
