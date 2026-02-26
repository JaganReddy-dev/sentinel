# Sentinel Prompt Instructions

## Project

Sentinel — a FastAPI authentication service.
GitHub: [sentinel](https://github.com/JaganReddy-dev/sentinel)
Stack: FastAPI, SQLAlchemy async, asyncpg, Neon PostgreSQL, Pydantic v2, Argon2id, Resend

## Versions

Always check `pyproject.toml` for exact package versions before generating code.
Never assume versions — FastAPI, Pydantic, SQLAlchemy, and asyncpg have breaking changes between major versions.

## Naming Conventions

- snake_case = functions, file_names, variables
- CapCase = classes
- UPPER_SNAKE_CASE = constants and env vars

## Timestamps

- Always UTC
- Always int: `int(utc_now().timestamp())`
- Pass `now` from service layer, never call `utc_now()` inside models
- Single `now` passed to all models in the same operation — ensures identical timestamps

## Project Structure

- Core logic goes into `app/core`
- Services go into `app/services`
- Route handlers go into `app/handlers`
- Schemas go into `app/schemas`
  - Internal schemas for DB models in `app/schemas/v1/internal`
  - Request schemas in `app/schemas/v1/request`
  - Response schemas in `app/schemas/v1/response`
- Utils go into `app/utils`
- Config and env vars go into `app/config.py`
- ORM models go into `app/models`
- Tests go into `tests/`

## Schema Rules

- Use Pydantic v2 (never pydantic.v1)
- UserBase as shared base, never inherit DB models from request schemas
- DB models use `from_signup()` classmethod pattern
- Response models use `from_db()` classmethod pattern
- Exclude sensitive fields (password, terms_accepted) from DB and response models
- Internal service result containers use `@dataclass`, not Pydantic

## Security

- Hash passwords with Argon2id (`m=7168, t=5, p=1`) via env vars in production
- OTPs hashed with SHA-256 (short-lived, attempt-limited — Argon2id not needed)
- JWT in response body (5 min expiry)
- Refresh token as HttpOnly, Secure, SameSite=Strict cookie
- Raw refresh token in cookie, hashed token stored in DB
- Never expose: `is_locked`, `failed_login_count`, `hashed_password`, `raw_token`, `previous_passwords`
- Account lockout: 5 failed attempts = 15 min lock, tracked via `failed_login_count` and `locked_until`
- OTP: expires in 15 min, invalidated after 3 wrong attempts, 60s resend cooldown

## Database

- SQLAlchemy async ORM with asyncpg
- Neon PostgreSQL (serverless)
- All related writes in a single transaction
- Use `db.flush()` for FK ordering within a transaction
- Never use `async with db.begin()` after a select — implicit transaction already started, use `db.commit()` directly
- `create_all()` on startup (never drop)
- ForeignKeys always use `ondelete="CASCADE"`
- Try/except around every `db.commit()` — rollback on failure

## Layer Separation

- Route handlers handle HTTP only: read request, call service, set cookies, return response
- Services own all business logic and DB writes
- Schemas validate and structure data
- Route handlers never make DB calls directly

## Token Strategy

- JWT expiry: 5 minutes, returned in response body
- Refresh token expiry: from `REFRESH_TOKEN_EXPIRE_DAYS` env var
- RT stored as hash in DB, raw token only in HttpOnly cookie
- Rotate on every refresh: revoke old RT, issue new RT
- Reuse detection: if revoked RT is used, revoke ALL user RTs
- `TokenServiceResult` `@dataclass` shared across login, verify, refresh handlers

## Error Handling

- Always raise `HTTPException` with correct status codes
- Wrap all `db.commit()` calls in try/except with `db.rollback()` on failure
- Return `tuple[bool, str]` from service functions where appropriate
- Custom exception handler in `main.py` transforms detail to message if needed
- Document all possible responses in route decorator using `responses={}`

## Email

- Resend for transactional email
- `send_verification_email` returns bool — never crashes the signup flow
- OTP sent after transaction commits — user creation does not depend on email success

## Commit Style

Conventional commits: `feat:`, `fix:`, `chore:`, `refactor:`

## Endpoints Built

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/verify-email`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

## Endpoints Remaining

- `POST /api/v1/auth/resend-verification`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `GET  /api/v1/auth/me`
- `POST /api/v1/auth/logout-all`
