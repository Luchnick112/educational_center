# Educational Center

School CRM / electronic diary backend on Django + DRF.

## Stack

- Django
- Django REST Framework
- SimpleJWT
- drf-spectacular
- PostgreSQL for development and production

## What Is Implemented

- Roles: `student`, `parent`, `teacher`, `admin`
- Academic domain: subjects, groups, enrollments, lessons, confirmations
- Finance domain: parent charges, teacher payouts
- Workflow actions for lessons and finance
- Object-level permissions
- OpenAPI schema and Swagger UI

## Local Run

Start the development PostgreSQL database:

```bash
docker compose -f docker-compose.dev.yml up -d db
```

Install backend dependencies and run migrations:

```bash
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver
```

`educational_center.settings` imports `educational_center.settings_dev` by default. The dev settings use PostgreSQL with these defaults:

```text
POSTGRES_DB=educational_center
POSTGRES_USER=educational_center
POSTGRES_PASSWORD=educational_center
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

For production, run Django with:

```text
DJANGO_SETTINGS_MODULE=educational_center.settings_prod
```

Use `.env.example` and `.env.prod.example` as templates for environment variables.

## Production Docker Deploy

Create the production environment file:

```bash
cp .env.prod.example .env.prod
```

Edit `.env.prod` and set real values for:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `APP_PORT` if the app should not listen on port `80`

Build and start the production stack:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

The stack contains:

- `db`: PostgreSQL
- `backend`: Django + Gunicorn
- `frontend`: nginx serving Vue and proxying `/api/` and `/admin/`

The backend entrypoint waits for PostgreSQL, runs migrations, collects static files, then starts Gunicorn.

Create an admin user:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Import transferred data after first deploy, if needed:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend python manage.py loaddata fixtures/postgres_transfer_dump.json
```

Useful operations:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f backend
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml down
```

## Demo Fixture

Load demo data into the local database:

```bash
python backend/manage.py loaddata demo_data.json
```

Demo credentials for browser forms and API:

- `admin@example.com` / `pass12345` (legacy, email login still accepted)
- `teacher@example.com` / `pass12345` (legacy, email login still accepted)
- `student@example.com` / `pass12345` (legacy, email login still accepted)
- `parent@example.com` / `pass12345` (legacy, email login still accepted)

## API Docs

- Swagger UI: `/api/docs/`
- OpenAPI schema: `/api/schema/`

## Auth

Base prefix: `/api/users/`

- `POST /api/users/register/`
- `POST /api/users/token/`
- `POST /api/users/token/refresh/`
- `GET /api/users/register/` browser registration form
- `GET /api/users/token/` browser login form
- `GET /api/users/token/refresh/` browser token refresh form

Example register payload:

```json
{
  "password": "pass12345",
  "first_name": "New",
  "last_name": "Teacher",
  "telegram_username": "@teacher_example",
  "role": "teacher",
  "phone": "+380001112233"
}
```

Example token payload:

```json
{
  "telegram_username": "@teacher_api",
  "password": "pass12345"
}
```

Use JWT in headers:

```text
Authorization: Bearer <access_token>
```

## Telegram Linking (Optional)

To send messages to users in Telegram, you must store their `chat_id`. Bots cannot reliably message a user by username only.

1. Set environment variables:

```bash
set TELEGRAM_BOT_USERNAME=YourBotNameWithoutAtSign
```

2. Generate a link token (authenticated):

- `POST /api/users/telegram/link-token/` -> returns `{ token, expires_at, deep_link_url }`

3. User opens `deep_link_url` and presses Start in Telegram.

### Option A: Webhook (needs public HTTPS)

Configure Telegram webhook to:

- `POST /api/users/telegram/webhook/`

When the webhook receives `/start <token>`, it links `telegram_chat_id` and `telegram_user_id` to the user.

### Option B: Long Polling (no public URL)

Set environment variable `TELEGRAM_BOT_TOKEN` and run:

```bash
python backend/manage.py telegram_poll --drop-pending
```

## Core Endpoints

- `GET /api/me/`
- `GET /api/my/lessons/`
- `GET /api/my/children/`
- `GET /api/my/children-summary/`
- `GET /api/my/payments/`
- `GET /api/my/confirmations/`

## Users API

Base prefix: `/api/users/`

- `GET/POST /api/users/`
- `GET /api/users/me/`
- `GET /api/users/dashboard/`
- `GET/POST /api/users/students/`
- `GET/POST /api/users/parents/`
- `GET/POST /api/users/teachers/`

Non-admin users only see related objects.

## Academics API

Base prefix: `/api/academics/`

- `GET/POST /api/academics/subjects/`
- `GET/POST /api/academics/groups/`
- `GET/POST /api/academics/enrollments/`
- `GET/POST /api/academics/lessons/`
- `GET/POST /api/academics/confirmations/`

### Lesson Workflow Actions

- `POST /api/academics/lessons/<id>/mark-attendance/`
- `POST /api/academics/lessons/<id>/complete/`
- `POST /api/academics/lessons/<id>/cancel/`
- `POST /api/academics/confirmations/<id>/confirm/`

Example `mark-attendance` payload:

```json
{
  "participant_id": 12,
  "attendance_status": "present"
}
```

Example `complete` payload:

```json
{
  "notes": "Completed on time"
}
```

Example `cancel` payload:

```json
{
  "reason": "Teacher sick leave"
}
```

Example `confirm` payload:

```json
{
  "comment": "Confirmed"
}
```

## Finance API

Base prefix: `/api/finance/`

- `GET/POST /api/finance/parent-charges/`
- `GET/POST /api/finance/teacher-payouts/`

### Finance Workflow Actions

- `POST /api/finance/parent-charges/<id>/issue/`
- `POST /api/finance/parent-charges/<id>/mark-paid/`
- `POST /api/finance/teacher-payouts/<id>/approve/`
- `POST /api/finance/teacher-payouts/<id>/mark-paid/`

Example `issue` payload:

```json
{
  "due_date": "2026-03-31"
}
```

Example `mark-paid` payload:

```json
{}
```

## Access Rules

- Admin can access all objects and workflow actions.
- Teacher can access only own groups, lessons, confirmations and payouts.
- Student can access only own enrollments, lessons, confirmations and related charges.
- Parent can access only linked children, their lessons, confirmations and charges.
- Object-level permissions protect direct access by a known object `id`, not only list filtering.

## Testing

```bash
python backend/manage.py check
python backend/manage.py test academics finance
```
