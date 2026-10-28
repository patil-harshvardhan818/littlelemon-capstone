from django.contrib import admin

from .models import Booking, Menu


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "price", "inventory")
    list_editable = ("price", "inventory")
    search_fields = ("title",)
    ordering = ("id",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "no_of_guests", "booking_date", "user")
    list_filter = ("booking_date",)
    search_fields = ("name", "user__username")
    date_hierarchy = "booking_date"
    raw_id_fields = ("user",)
