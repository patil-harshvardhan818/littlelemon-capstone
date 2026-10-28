"""Root URL configuration for the Little Lemon project."""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from restaurant.views import index

urlpatterns = [
    path("", index, name="home"),
    path("admin/", admin.site.urls),
    # User registration (Djoser): POST /auth/users/
    path("auth/", include("djoser.urls")),
    # Token login (DRF): POST /api-token-auth/
    path("api-token-auth/", obtain_auth_token, name="api-token-auth"),
    # Menu and booking APIs
    path("restaurant/", include("restaurant.urls")),
]
