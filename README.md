# Sentinel

A production-ready authentication service built with FastAPI, PostgreSQL, and modern security practices. Sentinel handles the full auth lifecycle — signup, email verification, login, token issuance, rotation, and logout — with every decision made deliberately.

---

## What it does

- User signup with email verification via OTP
- Login with email or username
- Account lockout after repeated failed attempts
- JWT access tokens (5 min expiry)
- Refresh token rotation with reuse detection
- HttpOnly cookie-based refresh token storage
- Logout and session management

---

## Stack

- **FastAPI** — async Python web framework
- **SQLAlchemy (async)** — ORM with asyncpg driver
- **PostgreSQL (Neon)** — serverless PostgreSQL
- **Pydantic v2** — request/response validation
- **Argon2id** — password hashing
- **Resend** — transactional email

---

## Project Structure

```text
app/
  core/
    security/
      password/         # Argon2id hashing and verification
      tokens/           # JWT and refresh token generation
      otp/              # OTP generation and hashing
    email/              # Resend email utility
  db/
    base.py             # DeclarativeBase
    db.py               # Engine, session, create_tables
  handlers/
    v1/                 # Route handlers (HTTP only, no business logic)
  models/               # SQLAlchemy ORM models
  schemas/
    v1/
      internal/         # DB models (Pydantic)
      request/          # Request schemas
      response/         # Response schemas
  services/             # Business logic
  utils/                # utc_now, secret, etc.
  config.py             # Centralized env config
  main.py
tests/
```

---

## API Endpoints

| Method | Endpoint                           | Description                                   |
| ------ | ---------------------------------- | --------------------------------------------- |
| POST   | `/api/v1/auth/signup`              | Register a new user                           |
| POST   | `/api/v1/auth/verify-email`        | Verify email with OTP                         |
| POST   | `/api/v1/auth/login`               | Login with email or username                  |
| POST   | `/api/v1/auth/refresh`             | Rotate refresh token, get new JWT             |
| POST   | `/api/v1/auth/logout`              | Revoke current session                        |
| POST   | `/api/v1/auth/resend-verification` | Resend OTP if expired or max attempts reached |
| POST   | `/api/v1/auth/forgot-pasword`      | Request password reset via email              |
| POST   | `/api/v1/auth/reset-pasword`       | Reset password with token                     |

---

## Upcoming

- `GET /api/v1/auth/me` — get current user profile
- `POST /api/v1/auth/logout-all` — revoke all sessions across all devices

---

## Token Strategy

### JWT (Access Token)

- Expiry: 5 minutes
- Returned in response body
- Client attaches as `Authorization: Bearer <token>`

### Refresh Token

- Expiry: configurable via `REFRESH_TOKEN_EXPIRE_DAYS`
- Stored as HttpOnly, Secure, SameSite=Strict cookie
- Raw token in cookie, hashed token in DB
- Rotated on every refresh
- Reuse detection: if a revoked token is used, all user sessions are revoked

---

## Security Decisions

- Passwords hashed with **Argon2id** (`m=7168, t=5, p=1`)
- Refresh tokens stored as **SHA-256 hashes** in DB
- Refresh token sent only as **HttpOnly cookie** — inaccessible to JavaScript
- JWT in response body — client reads it, attaches to requests
- Account lockout after 5 failed login attempts (15 minute lockout)
- OTP expires in 15 minutes, invalidated after 3 wrong attempts
- All DB writes in a **single atomic transaction**
- FK cascade deletes — no orphaned records

---

## Environment Variables

```dotenv
DB_URL=postgresql+asyncpg://user:pass@host/db
SECRET=your_jwt_secret
REFRESH_TOKEN_EXPIRE_DAYS=30
RESEND_API_KEY=re_xxxxxxxxxxxx
ARGON2_TIME_COST=5
ARGON2_MEMORY_COST=7168
```

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run the server
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`

---

## Database Tables

| Table                 | Description                           |
| --------------------- | ------------------------------------- |
| `users`               | Core user records                     |
| `passwords`           | Hashed passwords, separate from users |
| `refresh_tokens`      | Active sessions, one per device       |
| `email_verifications` | OTP records for email verification    |

---

## Commit Style

Conventional commits: `feat:`, `fix:`, `chore:`, `refactor:`

---

## GitHub

[github.com/JaganReddy-dev/sentinel](https://github.com/JaganReddy-dev/sentinel)
