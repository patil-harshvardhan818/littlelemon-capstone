from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MAX_GUESTS_PER_BOOKING = 20


class Menu(models.Model):
    """A dish or drink on the Little Lemon menu."""

    title = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    inventory = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Number of portions currently available.",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "menu item"
        verbose_name_plural = "menu items"

    def __str__(self):
        return f"{self.title} ({self.price})"


class Booking(models.Model):
    """A table reservation."""

    name = models.CharField(max_length=255)
    no_of_guests = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_GUESTS_PER_BOOKING)],
    )
    booking_date = models.DateTimeField()
    # Optional link to the account that made the booking. If the account is
    # deleted the booking is kept (the restaurant still needs the record).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )

    class Meta:
        ordering = ["booking_date", "id"]

    def __str__(self):
        return f"{self.name} - {self.no_of_guests} guest(s) on {self.booking_date:%Y-%m-%d %H:%M}"
