# Educational Center

School CRM / electronic diary backend on Django + DRF.

## Stack

- Django
- Django REST Framework
- SimpleJWT
- drf-spectacular
- SQLite for local development

## What Is Implemented

- Roles: `student`, `parent`, `teacher`, `admin`
- Academic domain: subjects, groups, enrollments, lessons, confirmations
- Finance domain: parent charges, teacher payouts
- Workflow actions for lessons and finance
- Object-level permissions
- OpenAPI schema and Swagger UI

## Local Run

```bash
python backend/manage.py migrate
python backend/manage.py runserver
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
