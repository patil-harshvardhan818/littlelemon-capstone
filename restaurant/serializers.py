from django.utils import timezone
from rest_framework import serializers

from .models import MAX_GUESTS_PER_BOOKING, Booking, Menu


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ["id", "title", "price", "inventory"]
        read_only_fields = ["id"]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_inventory(self, value):
        if value < 0:
            raise serializers.ValidationError("Inventory cannot be negative.")
        return value


class BookingSerializer(serializers.ModelSerializer):
    # Shown as the username; set automatically from the authenticated user.
    user = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "name", "no_of_guests", "booking_date", "user"]
        read_only_fields = ["id", "user"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        return value

    def validate_no_of_guests(self, value):
        if value < 1:
            raise serializers.ValidationError("At least 1 guest is required.")
        if value > MAX_GUESTS_PER_BOOKING:
            raise serializers.ValidationError(
                f"A booking can have at most {MAX_GUESTS_PER_BOOKING} guests."
            )
        return value

    def validate_booking_date(self, value):
        # Allow re-saving an existing booking without changing its date.
        if self.instance is not None and value == self.instance.booking_date:
            return value
        if value <= timezone.now():
            raise serializers.ValidationError("Booking date must be in the future.")
        return value
