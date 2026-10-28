# Little Lemon Restaurant — Django REST Framework Capstone

A backend for the fictional Little Lemon restaurant, built with Django and Django REST Framework. It serves a landing page, exposes menu and table-booking REST APIs, and supports user registration with token authentication. Data is stored in MySQL.

## Features

| Capstone requirement | Where it lives |
| --- | --- |
| Django serves static HTML content | `GET /` renders `templates/index.html` with CSS from `static/css/style.css` |
| Committed to Git | See [GitHub setup](#github-setup) |
| MySQL backend | `littlelemon/settings.py`, configured through environment variables |
| Menu APIs | `/restaurant/menu/` and `/restaurant/menu/<id>/` |
| Table booking APIs | `/restaurant/booking/tables/` and `/restaurant/booking/tables/<id>/` |
| Registration and authentication | `POST /auth/users/` (Djoser) and `POST /api-token-auth/` (DRF token) |
| Unit tests | `restaurant/tests.py`, run with `python manage.py test` |
| Insomnia-testable | See [Testing with Insomnia](#testing-with-insomnia) |

Also included: Django Admin for menu items and bookings, validation with readable error messages, and object-level permissions on bookings.

## Technology stack

- Python 3.10 or newer (3.12 was used for development)
- Django 5.2 LTS, Django REST Framework 3.16, Djoser 2.3
- MySQL 8 with the `mysqlclient` driver
- Django templates, HTML5 and CSS3 (no frontend framework)
- Django's test framework with DRF's `APIClient`
- Insomnia REST client, Git and GitHub

## Project structure

```
littlelemon-capstone/
├── manage.py
├── requirements.txt
├── .gitignore
├── .env.example          # template for your local .env (never commit .env)
├── Readme.txt            # short guide for peer reviewers
├── README.md             # this file
├── littlelemon/          # project package
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── restaurant/           # application
│   ├── models.py         # Menu, Booking
│   ├── serializers.py    # validation and JSON representation
│   ├── views.py          # landing page + API viewsets
│   ├── permissions.py    # IsOwnerOrStaff
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
├── templates/index.html
└── static/css/style.css
```

## Installation (Windows, VS Code)

Commands below use PowerShell, the default terminal in VS Code. macOS and Linux users can follow the same steps with the usual `source venv/bin/activate` syntax.

### 1. Install MySQL

1. Download **MySQL Installer** from <https://dev.mysql.com/downloads/installer/> and install *MySQL Server 8.x* (MySQL Workbench is optional but handy).
2. During setup choose a password for the `root` account and keep the server running as a Windows service.
3. Confirm it works: `mysql --version` (if the command is not found, use the *MySQL Command Line Client* from the Start menu).

### 2. Create the database and a database user

Open the MySQL command line (`mysql -u root -p`) and run:

```sql
CREATE DATABASE littlelemon CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'littlelemon_user'@'localhost' IDENTIFIED BY 'choose-a-strong-password';

-- Access to the application database and to the temporary database Django
-- creates while running unit tests (it is named test_<DB_NAME>).
GRANT ALL PRIVILEGES ON littlelemon.* TO 'littlelemon_user'@'localhost';
GRANT ALL PRIVILEGES ON test_littlelemon.* TO 'littlelemon_user'@'localhost';
FLUSH PRIVILEGES;
```

You can also use `root` for local development, but a dedicated user is better practice.

### 3. Get the code and create a virtual environment

```powershell
git clone YOUR_GITHUB_REPOSITORY_URL littlelemon-capstone
cd littlelemon-capstone

python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell refuses to run the activation script, run this once and retry:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

In VS Code, press `Ctrl+Shift+P` → *Python: Select Interpreter* and choose the interpreter inside `venv`.

### 4. Install Python dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Environment variables

The project reads its configuration from environment variables. For local development, put them in a `.env` file next to `manage.py`:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

| Variable | Purpose | Example |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key (required) | output of the command below |
| `DJANGO_DEBUG` | `True` for local development | `True` |
| `DJANGO_ALLOWED_HOSTS` | Optional, comma separated | `localhost,127.0.0.1` |
| `DB_NAME` | MySQL database name | `littlelemon` |
| `DB_USER` | MySQL user | `littlelemon_user` |
| `DB_PASSWORD` | MySQL password | the password you chose |
| `DB_HOST` | MySQL host | `127.0.0.1` |
| `DB_PORT` | MySQL port | `3306` |
| `USE_SQLITE_FOR_TESTS` | Optional. `True` runs `manage.py test` on in-memory SQLite | `False` |

Generate a secret key:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

`.env` is listed in `.gitignore`. Only `.env.example` (placeholders) is committed. If `DJANGO_DEBUG` is missing, it defaults to `False`, which is the safe setting for production.

### 6. Run migrations

```powershell
python manage.py migrate
```

This creates the Django tables plus `restaurant_menu`, `restaurant_booking` and the auth token table in MySQL. The migration files are committed, so you do not need to run `makemigrations` unless you change the models.

### 7. Create a superuser

```powershell
python manage.py createsuperuser
```

### 8. Start the server

```powershell
python manage.py runserver
```

| URL | What you get |
| --- | --- |
| <http://127.0.0.1:8000/> | Landing page |
| <http://127.0.0.1:8000/admin/> | Django Admin (log in as the superuser) |
| <http://127.0.0.1:8000/restaurant/menu/> | Menu API |

In the admin you can add, edit, search and delete **Menu items** and **Bookings**. Bookings can be filtered and browsed by date.

## Running the unit tests

```powershell
python manage.py test
```

Django automatically creates a separate, temporary database called `test_<DB_NAME>` (for example `test_littlelemon`), runs the tests in it, and deletes it afterwards. Your real data is never touched and you do not need to add any data first. The MySQL user therefore needs permission to create that database (the `GRANT` in step 2 covers this).

If you cannot grant that permission, set `USE_SQLITE_FOR_TESTS=True` in `.env` and the tests run on in-memory SQLite instead.

The suite covers menu CRUD and validation, booking CRUD, validation and access control, registration, token authentication (valid and invalid), unauthorized requests, and the HTML landing page.

## API reference

All request and response bodies are JSON. Send `Content-Type: application/json` with every request that has a body.

### Authentication

Menu reads are public. **Every booking endpoint, and menu writes (POST, PUT, PATCH, DELETE), require a token.**

1. Register: `POST /auth/users/`
2. Obtain a token: `POST /api-token-auth/`
3. Send it on each protected request in this header (the word `Token`, a space, then the key):

```
Authorization: Token YOUR_AUTH_TOKEN
```

A missing or invalid token returns `401 Unauthorized`.

| Method | URL | Auth | Purpose | Success |
| --- | --- | --- | --- | --- |
| POST | `/auth/users/` | none | Register a user | `201` |
| POST | `/api-token-auth/` | none | Get a token | `200` |

Register body (`email` is optional; passwords are checked against Django's password validators and stored hashed):

```json
{ "username": "alice", "email": "alice@example.com", "password": "Str0ng-Pass-123" }
```

Token body, and response:

```json
{ "username": "alice", "password": "Str0ng-Pass-123" }
```
```json
{ "token": "9054f7aa9305e012b3c2300408c3dfdf390fcddf" }
```

Wrong credentials return `400` with `{"non_field_errors": ["Unable to log in with provided credentials."]}`.

### Menu

| Method | URL | Auth | Purpose | Success |
| --- | --- | --- | --- | --- |
| GET | `/restaurant/menu/` | none | List items | `200` |
| POST | `/restaurant/menu/` | token | Create item | `201` |
| GET | `/restaurant/menu/<id>/` | none | Retrieve item | `200` |
| PUT | `/restaurant/menu/<id>/` | token | Replace item (all fields) | `200` |
| PATCH | `/restaurant/menu/<id>/` | token | Partial update | `200` |
| DELETE | `/restaurant/menu/<id>/` | token | Delete item | `204` |

Item representation:

```json
{ "id": 1, "title": "Greek salad", "price": "12.99", "inventory": 25 }
```

Validation: `title` is required and not blank; `price` is a decimal greater than 0 with up to 6 digits in total and 2 decimal places; `inventory` is an integer of 0 or more. An unknown `<id>` returns `404`.

### Table bookings

| Method | URL | Auth | Purpose | Success |
| --- | --- | --- | --- | --- |
| GET | `/restaurant/booking/tables/` | token | List your bookings (staff: all) | `200` |
| POST | `/restaurant/booking/tables/` | token | Create booking | `201` |
| GET | `/restaurant/booking/tables/<id>/` | token | Retrieve booking | `200` |
| PUT | `/restaurant/booking/tables/<id>/` | token | Replace booking | `200` |
| PATCH | `/restaurant/booking/tables/<id>/` | token | Partial update | `200` |
| DELETE | `/restaurant/booking/tables/<id>/` | token | Delete booking | `204` |

Booking representation:

```json
{
  "id": 1,
  "name": "Alice Smith",
  "no_of_guests": 4,
  "booking_date": "2027-06-15T19:30:00Z",
  "user": "alice"
}
```

Request bodies contain `name`, `no_of_guests` and `booking_date`. The `user` field is read-only: it is set from the token that made the request.

Validation: `name` is required and not blank; `no_of_guests` is a whole number from 1 to 20; `booking_date` is an ISO 8601 date-time and must be in the future (an existing booking can be re-saved without changing its date).

Access rules:

- Regular users only see and manage **their own** bookings. Another user's booking returns `404`, so its existence is not revealed.
- Staff users (`is_staff`, set in the admin) can list and manage **all** bookings.
- A booking whose user account is later deleted is kept, with `user` set to `null`.

### Error format

Validation failures return `400` with a field-to-messages object:

```json
{
  "title": ["This field may not be blank."],
  "price": ["Ensure this value is greater than or equal to 0.01."]
}
```

Other errors use `{"detail": "..."}`, for example `{"detail": "Authentication credentials were not provided."}` (`401`) or `{"detail": "No Menu matches the given query."}` (`404`).

## Testing with Insomnia

Download Insomnia from <https://insomnia.rest/download>. Keep `python manage.py runserver` running in VS Code. Use the Insomnia **Request** type (a plain HTTP request).

> **Important:** Do not use Insomnia's *Auth → Bearer Token* tab. It sends `Authorization: Bearer ...`, but this project requires `Authorization: Token ...`. Add the header manually on the **Headers** tab as described below.

### Optional: set up an environment

Click the environment dropdown → *Manage Environments*, and set the base environment to:

```json
{ "base_url": "http://127.0.0.1:8000", "token": "PASTE_TOKEN_HERE" }
```

You can then write `{{ _.base_url }}/restaurant/menu/` as the URL and `Token {{ _.token }}` as the header value. If you prefer, type full URLs and paste the token directly; both work.

### Step 1: Register a user

1. New Request → method **POST** → URL `http://127.0.0.1:8000/auth/users/`.
2. **Body** tab → **JSON**:
   ```json
   { "username": "alice", "email": "alice@example.com", "password": "Str0ng-Pass-123" }
   ```
3. Send. Expect **201 Created** and `{"email": "...", "username": "alice", "id": 1}`.

### Step 2: Obtain a token

1. **POST** `http://127.0.0.1:8000/api-token-auth/`
2. Body (JSON): `{ "username": "alice", "password": "Str0ng-Pass-123" }`
3. Send. Expect **200 OK** and `{"token": "..."}`. Copy the token.

### Step 3: Add the Authorization header

On every protected request open the **Headers** tab and add:

| Name | Value |
| --- | --- |
| `Authorization` | `Token YOUR_AUTH_TOKEN` |

Tip: create the header once, then *Duplicate* the request for the next endpoint, or store the token in the environment as shown above.

### Step 4: Menu requests

| # | Method | URL | Token? | Body | Expect |
| --- | --- | --- | --- | --- | --- |
| 1 | GET | `/restaurant/menu/` | no | none | `200` and a JSON array |
| 2 | POST | `/restaurant/menu/` | yes | `{"title": "Greek salad", "price": "12.99", "inventory": 25}` | `201` with the new item and its `id` |
| 3 | GET | `/restaurant/menu/1/` | no | none | `200` (use the `id` from step 2) |
| 4 | PUT | `/restaurant/menu/1/` | yes | `{"title": "Greek salad XL", "price": "15.50", "inventory": 20}` | `200` |
| 5 | PATCH | `/restaurant/menu/1/` | yes | `{"inventory": 18}` | `200` |
| 6 | DELETE | `/restaurant/menu/1/` | yes | none | `204` (empty body) |
| 7 | GET | `/restaurant/menu/1/` | no | none | `404` after deletion |

All URLs are prefixed with `http://127.0.0.1:8000`.

### Step 5: Booking requests

All of these require the `Authorization: Token ...` header. Use a date in the future.

| # | Method | URL | Body | Expect |
| --- | --- | --- | --- | --- |
| 1 | POST | `/restaurant/booking/tables/` | `{"name": "Alice Smith", "no_of_guests": 4, "booking_date": "2027-06-15T19:30:00Z"}` | `201`, response includes `"user": "alice"` |
| 2 | GET | `/restaurant/booking/tables/` | none | `200`, array of your bookings |
| 3 | GET | `/restaurant/booking/tables/1/` | none | `200` (use the `id` from step 1) |
| 4 | PUT | `/restaurant/booking/tables/1/` | `{"name": "Alice Smith", "no_of_guests": 6, "booking_date": "2027-06-16T20:00:00Z"}` | `200` |
| 5 | PATCH | `/restaurant/booking/tables/1/` | `{"no_of_guests": 2}` | `200` |
| 6 | DELETE | `/restaurant/booking/tables/1/` | none | `204` |
| 7 | GET | `/restaurant/booking/tables/1/` | none | `404` after deletion |

### Step 6: Test invalid requests

| Test | Request | Expect |
| --- | --- | --- |
| No token | `GET /restaurant/booking/tables/` without the header | `401` `{"detail": "Authentication credentials were not provided."}` |
| No token on write | `POST /restaurant/menu/` without the header | `401` |
| Wrong token | Header `Authorization: Token abc123` | `401` `{"detail": "Invalid token."}` |
| Wrong scheme | Header `Authorization: Bearer <token>` | `401` |
| Bad credentials | `POST /api-token-auth/` with a wrong password | `400` |
| Weak password | `POST /auth/users/` with `{"username": "x", "password": "123"}` | `400` with password errors |
| Negative price | `POST /restaurant/menu/` with `{"title": "A", "price": "-1", "inventory": 1}` | `400` with a `price` error |
| Negative inventory | `POST /restaurant/menu/` with `{"title": "A", "price": "1.00", "inventory": -5}` | `400` with an `inventory` error |
| Zero guests | `POST /restaurant/booking/tables/` with `"no_of_guests": 0` | `400` with a `no_of_guests` error |
| Too many guests | same with `"no_of_guests": 21` | `400` |
| Past date | same with `"booking_date": "2020-01-01T19:00:00Z"` | `400` with a `booking_date` error |
| Unknown id | `GET /restaurant/menu/9999/` | `404` |
| Someone else's booking | Register a second user, then request the first user's booking id with the second user's token | `404` |

### Verifying status codes

Insomnia shows the status code (green for 2xx, orange or red otherwise) at the top of the response pane, next to the response time and size. Compare it with the *Expect* column. The **Timeline** tab shows the exact request headers sent, which is the place to check that your `Authorization` header is present and spelled `Token`.

## GitHub setup

The `.gitignore` already excludes virtual environments, `__pycache__`, `*.pyc`, local `.env` files and IDE folders. Source code, migrations, `requirements.txt`, both README files and `.env.example` are committed.

1. Create an **empty** repository on GitHub (no README or .gitignore, so there are no conflicts).
2. From the project folder:

```bash
git init
git add .
git commit -m "Initial commit - Little Lemon Capstone"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Run `git remote add origin ...` **only if no remote has been configured yet**. If you get `remote origin already exists`, check it with `git remote -v`, and either skip the command or change the address with `git remote set-url origin YOUR_GITHUB_REPOSITORY_URL`.

Before pushing, confirm that no secrets are tracked: `git status` should not list `.env`, and `git ls-files` should show `.env.example` but not `.env`. Never commit passwords, tokens or a real `DJANGO_SECRET_KEY`.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ImproperlyConfigured: DJANGO_SECRET_KEY is not set` | Create `.env` from `.env.example` in the folder that contains `manage.py`, and set the key. |
| `Access denied for user ...` | `DB_USER` or `DB_PASSWORD` is wrong, or the user lacks privileges on the database. Re-run the `GRANT` statements. |
| `Can't connect to MySQL server on '127.0.0.1'` | Start the MySQL service (Windows *Services* → *MySQL80* → Start) and check `DB_HOST` and `DB_PORT`. |
| `Unknown database 'littlelemon'` | Run the `CREATE DATABASE` statement from step 2. |
| `pip install mysqlclient` fails to build | Upgrade pip (`python -m pip install --upgrade pip`) so a prebuilt Windows wheel is used, and use a 64-bit Python 3.10 to 3.13. On Linux install `libmysqlclient-dev`, `pkg-config` and `python3-dev` first. |
| `Access denied ... to database 'test_littlelemon'` when testing | Run the `GRANT ... ON test_littlelemon.*` statement, or set `USE_SQLITE_FOR_TESTS=True`. |
| Tests stop with `database test_littlelemon already exists` | A previous run was interrupted. Answer `yes` to the prompt, or run `python manage.py test --noinput`. |
| Insomnia returns `401` with a valid token | Check the header reads `Token <key>`, not `Bearer <key>`, and that there is no extra whitespace or quotes around the key. |
| `400` with "JSON parse error" | The body type must be **JSON** and the body valid JSON (double quotes, no trailing commas). |
| Page has no styling | `DJANGO_DEBUG` must be `True` for `runserver` to serve `/static/`. |
| `ModuleNotFoundError` | The virtual environment is not active. Run `.\venv\Scripts\Activate.ps1` and `pip install -r requirements.txt`. |

## Notes

- Menu reads are public so the menu can be shown to anyone. Writes need a token, but any registered user may write. To restrict menu editing to staff, change `permission_classes` in `MenuViewSet` to `permissions.IsAdminUser`.
- This is a development setup. Before any real deployment, set `DJANGO_DEBUG=False`, configure `DJANGO_ALLOWED_HOSTS`, serve static files properly and use HTTPS.
