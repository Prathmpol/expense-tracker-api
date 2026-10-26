# Expense Tracker & Financial Analytics API

A FastAPI backend for recording income/expenses and generating financial
analytics: totals, category breakdowns, monthly trends, and savings rate.

## Tech stack

- **FastAPI** — web framework
- **Pydantic v2** — request/response validation
- **SQLAlchemy 2.0** — ORM (works with SQLite, PostgreSQL, or MySQL)
- **Alembic** — database migrations
- **Pandas** — analytics computations
- **python-jose** — JWT auth
- **passlib[bcrypt]** — password hashing
- **Pytest + httpx** — testing

## Project structure

```
expense-tracker-api/
├── app/
│   ├── main.py            # FastAPI app, router registration, CORS
│   ├── config.py          # Settings (env vars)
│   ├── database.py        # SQLAlchemy engine/session
│   ├── models.py          # ORM models: User, Expense, Income
│   ├── schemas.py         # Pydantic request/response models
│   ├── dependencies.py    # get_current_user (JWT) dependency
│   ├── utils/
│   │   └── security.py    # password hashing + JWT helpers
│   └── routers/
│       ├── auth.py        # /auth/register, /auth/login
│       ├── expenses.py    # /expenses CRUD + filters
│       ├── income.py      # /income CRUD + filters
│       └── analytics.py   # /analytics/* (pandas-powered)
├── alembic/                # migrations (env.py wired to app settings)
├── tests/                  # pytest suite (29 tests)
├── requirements.txt
├── .env.example
└── alembic.ini
```

## Setup

```bash
cd expense-tracker-api
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit SECRET_KEY, DATABASE_URL, etc.
```

By default `DATABASE_URL` is SQLite (`sqlite:///./expense_tracker.db`), so
you can run everything with zero extra setup. To use Postgres or MySQL,
uncomment and edit the relevant line in `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/expense_tracker
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/expense_tracker
```

## Run the server

```bash
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

On startup the app auto-creates tables via `Base.metadata.create_all`, so
it works immediately for local/dev use. For a real deployment, use Alembic
migrations instead (see below) and remove/skip the auto-create call.

## Database migrations (Alembic)

An initial migration (`alembic/versions/*_initial_tables.py`) is already
included, covering the `users`, `expenses`, and `income` tables.

```bash
# Apply migrations
alembic upgrade head

# After changing models.py, generate a new migration
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## Authentication flow

1. `POST /auth/register` — create an account (name, email, password).
   Passwords are hashed with bcrypt before storage; the response never
   includes the password or hash.
2. `POST /auth/login` — exchange email/password for a JWT access token.
3. Send the token on every other request:
   `Authorization: Bearer <access_token>`

Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60, configurable
in `.env`). All `/expenses`, `/income`, and `/analytics` routes require a
valid token and are automatically scoped to the requesting user — one
user can never see or modify another user's data.

## Endpoints

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create a new user |
| POST | `/auth/login` | Get a JWT access token |

### Expenses (auth required)
| Method | Path | Description |
|---|---|---|
| POST | `/expenses` | Add an expense |
| GET | `/expenses` | List expenses (filter by `category`, `start_date`, `end_date`; paginated via `skip`/`limit`) |
| GET | `/expenses/{id}` | Get one expense |
| PUT | `/expenses/{id}` | Update an expense (partial update supported) |
| DELETE | `/expenses/{id}` | Delete an expense |

Categories: `Food`, `Travel`, `Shopping`, `Bills`, `Education`,
`Entertainment`, `Healthcare`, `Other`.

### Income (auth required)
| Method | Path | Description |
|---|---|---|
| POST | `/income` | Add an income entry |
| GET | `/income` | List income (filter by `start_date`, `end_date`, `source`) |
| GET | `/income/{id}` | Get one income entry |
| PUT | `/income/{id}` | Update an income entry (partial update supported) |
| DELETE | `/income/{id}` | Delete an income entry |

### Analytics (auth required)
| Method | Path | Description |
|---|---|---|
| GET | `/analytics/summary` | Total income, total expenses, balance, savings rate, highest spending category, avg daily spending. Optional `start_date`/`end_date`. |
| GET | `/analytics/monthly` | Income/expenses/balance broken down by month (`YYYY-MM`). Optional `year` filter. |
| GET | `/analytics/category` | Expense totals, percentage share, and transaction count per category. Optional `start_date`/`end_date`. |
| GET | `/analytics/savings` | Total income/expenses/savings and savings rate. Optional `start_date`/`end_date`. |

Example `/analytics/summary` response:

```json
{
  "total_income": 50000,
  "total_expenses": 32000,
  "balance": 18000,
  "savings_rate": 36.0,
  "highest_spending_category": "Food",
  "average_daily_spending": 8000.0
}
```

## Running tests

Run the complete test suite from the project root:

```bash
python -m pytest -q
```

The test suite contains 29 tests covering:

- **Unit testing:** Password hashing, password verification, JWT creation, invalid tokens, and expired tokens.
- **API integration testing:** Authentication, expense and income CRUD, analytics endpoints, filtering, and per-user data isolation.
- **Input validation:** Invalid expense amounts, invalid categories, invalid query parameters, and missing required income fields.

Tests use an isolated in-memory SQLite database, protecting the configured application database and existing database files.

## Continuous Integration

GitHub Actions automatically installs project dependencies and runs the pytest suite on pushes to `main` and pull requests targeting `main`.

Workflow configuration: `.github/workflows/ci.yml`

Run status: [View GitHub Actions](https://github.com/Prathmpol/expense-tracker-api/actions)

## Notes / design decisions

- **Per-user data isolation**: every expenses/income/analytics query
  filters by `user_id` derived from the JWT, so users can never read or
  modify each other's records — verified in `tests/test_expenses.py`.
- **Partial updates**: `PUT /expenses/{id}` and `PUT /income/{id}` accept
  any subset of fields (`exclude_unset=True`), so you can update just the
  amount without resending the whole record.
- **Category is an enum** (`ExpenseCategory`) validated by Pydantic/DB, so
  invalid categories are rejected with a 422 before hitting the database.
- **Analytics use pandas** for the groupby/aggregation logic, which keeps
  the router code short and makes it easy to extend (e.g. weekly trends,
  rolling averages) without hand-rolling SQL aggregations.
- **Swap databases via one env var**: switching `DATABASE_URL` between
  SQLite/Postgres/MySQL requires no code changes — SQLAlchemy handles the
  dialect differences.