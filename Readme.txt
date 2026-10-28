==============================================================
LITTLE LEMON RESTAURANT - DJANGO REST FRAMEWORK CAPSTONE
Guide for peer reviewers
==============================================================

DESCRIPTION
-----------
Backend for the Little Lemon restaurant built with Django and
Django REST Framework, using MySQL. It provides:
  - an HTML landing page served by Django (GET /)
  - Menu REST API
  - Table Booking REST API
  - User registration and token authentication
  - Django Admin for menu items and bookings
  - Unit tests (python manage.py test)

Full documentation: README.md (same folder).


PREREQUISITES
-------------
  - Python 3.10 or newer
  - MySQL Server 8.x, running
  - Git
  - Insomnia REST client (https://insomnia.rest/download)


SETUP (Windows PowerShell; run inside the project folder)
---------------------------------------------------------
1. Create the MySQL database and user (mysql -u root -p):

     CREATE DATABASE littlelemon CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     CREATE USER 'littlelemon_user'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
     GRANT ALL PRIVILEGES ON littlelemon.* TO 'littlelemon_user'@'localhost';
     GRANT ALL PRIVILEGES ON test_littlelemon.* TO 'littlelemon_user'@'localhost';
     FLUSH PRIVILEGES;

2. Virtual environment and dependencies:

     python -m venv venv
     .\venv\Scripts\Activate.ps1
     python -m pip install --upgrade pip
     pip install -r requirements.txt

3. Environment variables:

     Copy-Item .env.example .env

   Edit .env and set DJANGO_SECRET_KEY, DB_NAME, DB_USER,
   DB_PASSWORD, DB_HOST, DB_PORT and DJANGO_DEBUG=True.
   Generate a secret key with:

     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

   (.env is not in the repository on purpose, because it holds secrets.)

4. Create the tables:

     python manage.py migrate

5. Create an admin user:

     python manage.py createsuperuser

6. Start the server:

     python manage.py runserver

7. Run the unit tests (uses a temporary test_littlelemon database,
   which Django creates and deletes by itself):

     python manage.py test

   If your MySQL user cannot create databases, set
   USE_SQLITE_FOR_TESTS=True in .env to run tests on SQLite.


PAGES
-----
  http://127.0.0.1:8000/          Landing page (HTML + CSS)
  http://127.0.0.1:8000/admin/    Django Admin (superuser login)


API ENDPOINTS  (base URL http://127.0.0.1:8000)
-----------------------------------------------
Authentication
  POST   /auth/users/                     Register          (no token)      -> 201
  POST   /api-token-auth/                 Obtain token      (no token)      -> 200

Menu
  GET    /restaurant/menu/                List items        (no token)      -> 200
  POST   /restaurant/menu/                Create item       (token)         -> 201
  GET    /restaurant/menu/<id>/           Retrieve item     (no token)      -> 200 / 404
  PUT    /restaurant/menu/<id>/           Update item       (token)         -> 200
  PATCH  /restaurant/menu/<id>/           Partial update    (token)         -> 200
  DELETE /restaurant/menu/<id>/           Delete item       (token)         -> 204

Table bookings (ALL require a token)
  GET    /restaurant/booking/tables/          List bookings     -> 200
  POST   /restaurant/booking/tables/          Create booking    -> 201
  GET    /restaurant/booking/tables/<id>/     Retrieve booking  -> 200 / 404
  PUT    /restaurant/booking/tables/<id>/     Update booking    -> 200
  PATCH  /restaurant/booking/tables/<id>/     Partial update    -> 200
  DELETE /restaurant/booking/tables/<id>/     Delete booking    -> 204


AUTHENTICATION
--------------
1. Register with POST /auth/users/
2. Get a token with POST /api-token-auth/
3. Send the token on protected requests as an HTTP header:

     Authorization: Token YOUR_AUTH_TOKEN

IMPORTANT FOR INSOMNIA: do NOT use the "Auth > Bearer Token" tab
(it sends "Bearer", which this API rejects). Add the header
manually on the Headers tab: name = Authorization,
value = Token YOUR_AUTH_TOKEN

Missing or invalid token -> 401 Unauthorized.


EXAMPLE REQUEST BODIES (JSON; set Body type to JSON in Insomnia)
-----------------------------------------------------------------
Register  - POST /auth/users/
  {"username": "alice", "email": "alice@example.com", "password": "Str0ng-Pass-123"}
  -> 201 {"email": "alice@example.com", "username": "alice", "id": 1}

Get token - POST /api-token-auth/
  {"username": "alice", "password": "Str0ng-Pass-123"}
  -> 200 {"token": "..."}

Create menu item - POST /restaurant/menu/   (token)
  {"title": "Greek salad", "price": "12.99", "inventory": 25}
  -> 201 {"id": 1, "title": "Greek salad", "price": "12.99", "inventory": 25}

Update menu item - PUT /restaurant/menu/1/   (token)
  {"title": "Greek salad XL", "price": "15.50", "inventory": 20}

Partial update - PATCH /restaurant/menu/1/   (token)
  {"inventory": 18}

Create booking - POST /restaurant/booking/tables/   (token)
  {"name": "Alice Smith", "no_of_guests": 4, "booking_date": "2027-06-15T19:30:00Z"}
  -> 201 {"id": 1, "name": "Alice Smith", "no_of_guests": 4,
          "booking_date": "2027-06-15T19:30:00Z", "user": "alice"}

Update booking - PUT /restaurant/booking/tables/1/   (token)
  {"name": "Alice Smith", "no_of_guests": 6, "booking_date": "2027-06-16T20:00:00Z"}

Partial update - PATCH /restaurant/booking/tables/1/   (token)
  {"no_of_guests": 2}

Invalid examples (expect 400):
  POST /restaurant/menu/            {"title": "A", "price": "-1", "inventory": -5}
  POST /restaurant/booking/tables/  {"name": "A", "no_of_guests": 0,
                                     "booking_date": "2020-01-01T19:00:00Z"}
Other expected errors:
  No/invalid token            -> 401
  GET /restaurant/menu/9999/  -> 404


NOTES FOR REVIEWERS
-------------------
- booking_date must be in the future; use a date later than today.
  no_of_guests must be between 1 and 20.
- A "user" field in a booking request is ignored. The booking is
  always linked to the owner of the token.
- Regular users see and manage only their own bookings (another
  user's booking returns 404). Staff users (is_staff, set in
  /admin/) can see and manage all bookings.
- The menu can be read by anyone; creating, updating and deleting
  menu items requires a token from any registered user.
- Each GET on the landing page lists menu items stored in MySQL
  (items with inventory > 0); with an empty menu it shows three
  default dishes.
- Passwords are hashed by Django; weak passwords are rejected at
  registration (for example "123").
- SECRET_KEY and database credentials come from environment
  variables, so no secrets are stored in the repository.
- The Insomnia step-by-step guide with a full request table is in
  README.md, section "Testing with Insomnia".
