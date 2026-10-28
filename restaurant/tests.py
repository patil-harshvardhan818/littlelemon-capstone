from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Booking, Menu

User = get_user_model()

MENU_URL = "/restaurant/menu/"
BOOKING_URL = "/restaurant/booking/tables/"
REGISTER_URL = "/auth/users/"
TOKEN_URL = "/api-token-auth/"


def future(days=3):
    return timezone.now() + timedelta(days=days)


class BaseAPITestCase(TestCase):
    """Shared helpers: users, tokens and authenticated clients."""

    PASSWORD = "Str0ng-Pass-123"

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("alice", "alice@example.com", self.PASSWORD)
        self.other_user = User.objects.create_user("bob", "bob@example.com", self.PASSWORD)
        self.staff = User.objects.create_user(
            "manager", "manager@example.com", self.PASSWORD, is_staff=True
        )

    def client_for(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return client


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
class MenuAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.item = Menu.objects.create(title="Greek salad", price=Decimal("12.99"), inventory=10)
        self.auth = self.client_for(self.user)

    def test_list_is_public(self):
        Menu.objects.create(title="Bruschetta", price=Decimal("7.50"), inventory=5)
        response = self.client.get(MENU_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(
            set(response.json()[0].keys()), {"id", "title", "price", "inventory"}
        )

    def test_retrieve_is_public(self):
        response = self.client.get(f"{MENU_URL}{self.item.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["title"], "Greek salad")
        self.assertEqual(data["price"], "12.99")
        self.assertEqual(data["inventory"], 10)

    def test_retrieve_missing_item_returns_404(self):
        response = self.client.get(f"{MENU_URL}99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.json())

    def test_create_with_token(self):
        payload = {"title": "Lemon dessert", "price": "6.50", "inventory": 20}
        response = self.auth.post(MENU_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["title"], "Lemon dessert")
        self.assertTrue(Menu.objects.filter(title="Lemon dessert").exists())

    def test_create_without_token_is_rejected(self):
        payload = {"title": "Lemon dessert", "price": "6.50", "inventory": 20}
        response = self.client.post(MENU_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Menu.objects.filter(title="Lemon dessert").exists())

    def test_create_with_invalid_token_is_rejected(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Token not-a-real-token")
        response = client.post(
            MENU_URL, {"title": "X", "price": "1.00", "inventory": 1}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_put_updates_item(self):
        payload = {"title": "Greek salad XL", "price": "15.00", "inventory": 8}
        response = self.auth.put(f"{MENU_URL}{self.item.id}/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, "Greek salad XL")
        self.assertEqual(self.item.price, Decimal("15.00"))
        self.assertEqual(self.item.inventory, 8)

    def test_patch_updates_only_given_fields(self):
        response = self.auth.patch(
            f"{MENU_URL}{self.item.id}/", {"inventory": 3}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.inventory, 3)
        self.assertEqual(self.item.title, "Greek salad")

    def test_update_without_token_is_rejected(self):
        response = self.client.patch(
            f"{MENU_URL}{self.item.id}/", {"inventory": 3}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_item(self):
        response = self.auth.delete(f"{MENU_URL}{self.item.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Menu.objects.filter(pk=self.item.id).exists())

    def test_delete_without_token_is_rejected(self):
        response = self.client.delete(f"{MENU_URL}{self.item.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Menu.objects.filter(pk=self.item.id).exists())

    def test_delete_missing_item_returns_404(self):
        response = self.auth.delete(f"{MENU_URL}99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_menu_data(self):
        invalid_payloads = {
            "negative price": ({"title": "A", "price": "-1.00", "inventory": 1}, "price"),
            "zero price": ({"title": "A", "price": "0", "inventory": 1}, "price"),
            "text price": ({"title": "A", "price": "abc", "inventory": 1}, "price"),
            "too many digits": ({"title": "A", "price": "1234567.00", "inventory": 1}, "price"),
            "negative inventory": ({"title": "A", "price": "1.00", "inventory": -5}, "inventory"),
            "text inventory": ({"title": "A", "price": "1.00", "inventory": "many"}, "inventory"),
            "blank title": ({"title": "   ", "price": "1.00", "inventory": 1}, "title"),
            "missing title": ({"price": "1.00", "inventory": 1}, "title"),
            "missing price": ({"title": "A", "inventory": 1}, "price"),
            "missing inventory": ({"title": "A", "price": "1.00"}, "inventory"),
        }
        for label, (payload, bad_field) in invalid_payloads.items():
            with self.subTest(label):
                response = self.auth.post(MENU_URL, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(bad_field, response.json())
        self.assertEqual(Menu.objects.count(), 1)

    def test_invalid_patch_is_rejected(self):
        response = self.auth.patch(
            f"{MENU_URL}{self.item.id}/", {"price": "-3"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.item.refresh_from_db()
        self.assertEqual(self.item.price, Decimal("12.99"))


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------
class BookingAPITests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.alice = self.client_for(self.user)
        self.bob = self.client_for(self.other_user)
        self.manager = self.client_for(self.staff)
        self.booking = Booking.objects.create(
            name="Alice", no_of_guests=2, booking_date=future(2), user=self.user
        )
        self.bobs_booking = Booking.objects.create(
            name="Bob", no_of_guests=4, booking_date=future(4), user=self.other_user
        )

    def payload(self, **overrides):
        data = {
            "name": "Carol",
            "no_of_guests": 3,
            "booking_date": future(5).isoformat(),
        }
        data.update(overrides)
        return data

    # --- authentication -----------------------------------------------------
    def test_all_booking_endpoints_require_token(self):
        detail = f"{BOOKING_URL}{self.booking.id}/"
        requests = [
            ("get", BOOKING_URL), ("post", BOOKING_URL),
            ("get", detail), ("put", detail), ("patch", detail), ("delete", detail),
        ]
        for method, url in requests:
            with self.subTest(f"{method.upper()} {url}"):
                response = getattr(self.client, method)(url, self.payload(), format="json")
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- create -------------------------------------------------------------
    def test_create_booking_sets_user_from_token(self):
        response = self.alice.post(BOOKING_URL, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["name"], "Carol")
        self.assertEqual(data["no_of_guests"], 3)
        self.assertEqual(data["user"], "alice")
        self.assertEqual(Booking.objects.get(pk=data["id"]).user, self.user)

    def test_user_field_in_request_is_ignored(self):
        response = self.alice.post(
            BOOKING_URL, self.payload(user=self.other_user.id), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["user"], "alice")

    def test_invalid_booking_data(self):
        past = (timezone.now() - timedelta(days=1)).isoformat()
        invalid_payloads = {
            "zero guests": (self.payload(no_of_guests=0), "no_of_guests"),
            "negative guests": (self.payload(no_of_guests=-2), "no_of_guests"),
            "too many guests": (self.payload(no_of_guests=21), "no_of_guests"),
            "text guests": (self.payload(no_of_guests="lots"), "no_of_guests"),
            "past date": (self.payload(booking_date=past), "booking_date"),
            "bad date": (self.payload(booking_date="tomorrow-ish"), "booking_date"),
            "blank name": (self.payload(name="  "), "name"),
        }
        for label, (payload, bad_field) in invalid_payloads.items():
            with self.subTest(label):
                response = self.alice.post(BOOKING_URL, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(bad_field, response.json())

        for field in ("name", "no_of_guests", "booking_date"):
            with self.subTest(f"missing {field}"):
                payload = self.payload()
                del payload[field]
                response = self.alice.post(BOOKING_URL, payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.json())

        self.assertEqual(Booking.objects.count(), 2)  # only the two from setUp

    # --- list / retrieve ----------------------------------------------------
    def test_user_lists_only_own_bookings(self):
        response = self.alice.get(BOOKING_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [b["id"] for b in response.json()]
        self.assertEqual(ids, [self.booking.id])

    def test_staff_lists_all_bookings(self):
        response = self.manager.get(BOOKING_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({b["id"] for b in response.json()}, {self.booking.id, self.bobs_booking.id})

    def test_retrieve_own_booking(self):
        response = self.alice.get(f"{BOOKING_URL}{self.booking.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["id"], self.booking.id)
        self.assertEqual(set(data.keys()), {"id", "name", "no_of_guests", "booking_date", "user"})

    def test_user_cannot_retrieve_other_users_booking(self):
        response = self.alice.get(f"{BOOKING_URL}{self.bobs_booking.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_retrieve_any_booking(self):
        response = self.manager.get(f"{BOOKING_URL}{self.bobs_booking.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_missing_booking_returns_404(self):
        response = self.alice.get(f"{BOOKING_URL}99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- update -------------------------------------------------------------
    def test_put_updates_own_booking(self):
        new_date = future(10)
        response = self.alice.put(
            f"{BOOKING_URL}{self.booking.id}/",
            {"name": "Alice Smith", "no_of_guests": 6, "booking_date": new_date.isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.name, "Alice Smith")
        self.assertEqual(self.booking.no_of_guests, 6)
        self.assertEqual(self.booking.user, self.user)

    def test_patch_updates_own_booking(self):
        response = self.alice.patch(
            f"{BOOKING_URL}{self.booking.id}/", {"no_of_guests": 5}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.no_of_guests, 5)
        self.assertEqual(self.booking.name, "Alice")

    def test_invalid_update_is_rejected(self):
        response = self.alice.patch(
            f"{BOOKING_URL}{self.booking.id}/", {"no_of_guests": 0}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.no_of_guests, 2)

    def test_user_cannot_update_other_users_booking(self):
        url = f"{BOOKING_URL}{self.bobs_booking.id}/"
        for method in ("put", "patch"):
            with self.subTest(method):
                response = getattr(self.alice, method)(url, self.payload(), format="json")
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.bobs_booking.refresh_from_db()
        self.assertEqual(self.bobs_booking.name, "Bob")

    def test_staff_can_update_any_booking(self):
        response = self.manager.patch(
            f"{BOOKING_URL}{self.bobs_booking.id}/", {"no_of_guests": 8}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bobs_booking.refresh_from_db()
        self.assertEqual(self.bobs_booking.no_of_guests, 8)
        self.assertEqual(self.bobs_booking.user, self.other_user)

    # --- delete -------------------------------------------------------------
    def test_delete_own_booking(self):
        response = self.alice.delete(f"{BOOKING_URL}{self.booking.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Booking.objects.filter(pk=self.booking.id).exists())

    def test_user_cannot_delete_other_users_booking(self):
        response = self.alice.delete(f"{BOOKING_URL}{self.bobs_booking.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Booking.objects.filter(pk=self.bobs_booking.id).exists())

    def test_staff_can_delete_any_booking(self):
        response = self.manager.delete(f"{BOOKING_URL}{self.bobs_booking.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_missing_booking_returns_404(self):
        response = self.alice.delete(f"{BOOKING_URL}99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleting_user_keeps_booking(self):
        self.other_user.delete()
        self.bobs_booking.refresh_from_db()
        self.assertIsNone(self.bobs_booking.user)


# ---------------------------------------------------------------------------
# Registration and token authentication
# ---------------------------------------------------------------------------
class AuthenticationTests(BaseAPITestCase):
    def test_register_new_user(self):
        response = self.client.post(
            REGISTER_URL,
            {"username": "newdiner", "email": "new@example.com", "password": "Another-Str0ng-1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["username"], "newdiner")
        self.assertNotIn("password", response.json())

        user = User.objects.get(username="newdiner")
        self.assertNotEqual(user.password, "Another-Str0ng-1")  # hashed, not plain text
        self.assertTrue(user.check_password("Another-Str0ng-1"))

    def test_register_rejects_duplicate_username(self):
        response = self.client.post(
            REGISTER_URL, {"username": "alice", "password": "Another-Str0ng-1"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.json())

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            REGISTER_URL, {"username": "weakling", "password": "123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.json())
        self.assertFalse(User.objects.filter(username="weakling").exists())

    def test_register_requires_username_and_password(self):
        response = self.client.post(REGISTER_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.json())
        self.assertIn("password", response.json())

    def test_obtain_token_with_valid_credentials(self):
        response = self.client.post(
            TOKEN_URL, {"username": "alice", "password": self.PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.json()["token"]
        self.assertEqual(token, Token.objects.get(user=self.user).key)

    def test_obtained_token_grants_access(self):
        token = self.client.post(
            TOKEN_URL, {"username": "alice", "password": self.PASSWORD}, format="json"
        ).json()["token"]
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(client.get(BOOKING_URL).status_code, status.HTTP_200_OK)

    def test_register_then_login_then_use_token(self):
        creds = {"username": "journey", "password": "Journey-Str0ng-1"}
        self.assertEqual(
            self.client.post(REGISTER_URL, creds, format="json").status_code,
            status.HTTP_201_CREATED,
        )
        token_response = self.client.post(TOKEN_URL, creds, format="json")
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token_response.json()['token']}")
        response = client.post(
            BOOKING_URL,
            {"name": "Journey", "no_of_guests": 2, "booking_date": future().isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_token_with_wrong_password_fails(self):
        response = self.client.post(
            TOKEN_URL, {"username": "alice", "password": "wrong-password"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.json())

    def test_token_with_unknown_user_fails(self):
        response = self.client.post(
            TOKEN_URL, {"username": "ghost", "password": self.PASSWORD}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_with_missing_fields_fails(self):
        response = self.client.post(TOKEN_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_authorization_scheme_is_rejected(self):
        token, _ = Token.objects.get_or_create(user=self.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
        self.assertEqual(client.get(BOOKING_URL).status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ModelTests(TestCase):
    def test_menu_str(self):
        item = Menu.objects.create(title="Bruschetta", price=Decimal("7.50"), inventory=5)
        self.assertEqual(str(item), "Bruschetta (7.50)")

    def test_booking_str(self):
        booking = Booking.objects.create(name="Dana", no_of_guests=2, booking_date=future())
        self.assertIn("Dana", str(booking))


# ---------------------------------------------------------------------------
# HTML landing page
# ---------------------------------------------------------------------------
class LandingPageTests(TestCase):
    def test_root_returns_200_and_uses_template(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertEqual(response["Content-Type"].split(";")[0], "text/html")

    def test_home_url_name_resolves_to_root(self):
        self.assertEqual(reverse("home"), "/")

    def test_page_contains_expected_sections(self):
        response = self.client.get("/")
        for text in ("Little Lemon", 'id="about"', 'id="menu"', 'id="booking"', "<footer", "<nav"):
            with self.subTest(text):
                self.assertContains(response, text)

    def test_page_links_stylesheet(self):
        response = self.client.get("/")
        self.assertContains(response, "/static/css/style.css")
        self.assertIsNotNone(finders.find("css/style.css"))

    def test_page_shows_menu_items_from_database(self):
        Menu.objects.create(title="Grilled sea bass", price=Decimal("21.00"), inventory=4)
        Menu.objects.create(title="Sold out special", price=Decimal("9.00"), inventory=0)
        response = self.client.get("/")
        self.assertContains(response, "Grilled sea bass")
        self.assertNotContains(response, "Sold out special")

    def test_page_shows_fallback_dishes_when_menu_is_empty(self):
        response = self.client.get("/")
        self.assertContains(response, "Greek salad")
