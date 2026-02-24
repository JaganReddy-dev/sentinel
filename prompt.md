## Prompt Instructions:

# Naming conventions:

- snake_case = functions, file_names, variables
- CapCase = classes
- UPPER_SNAKE_CASE = constants and env vars

# Timestamps:

- Always UTC
- Always int: int(utc_now().timestamp())
- Pass `now` from service layer, never call utc_now() inside models

# Project Structure:

- Core logic goes into app/core
- Services go into app/services
- Route handlers go into app/handlers
- Schemas go into app/schemas
  -- Internal schemas for DB models in app/schemas/internal
  -- Request schemas in app/schemas/request
  -- Response schemas in app/schemas/response
- Utils go into app/utils
- Config and env vars go into app/config.py
- ORM models go into app/models
- Tests go into tests/

# Schema Rules:

- Use Pydantic v2 (never pydantic.v1)
- UserBase as shared base, never inherit DB models from request schemas
- DB models use from_signup() classmethod pattern
- Response models use from_db() classmethod pattern
- Exclude sensitive fields (password, terms_accepted) from DB and response models

# Security:

- Hash passwords with Argon2id
- JWT in response body
- Refresh token as httponly, secure, samesite=strict cookie
- Never expose: is_locked, failed_login_count, hashed_password, raw_token

# Database:

- SQLAlchemy async ORM with asyncpg
- Neon PostgreSQL
- All related writes in a single transaction with flush() for FK ordering
- create_all() on startup (never drop)
- ForeignKeys use ondelete="CASCADE"

# Testing:

- pytest
- One test file per service/handler
- Test DB separate from dev DB

# Tokens:

- JWT expiry: 5 minutes
- Refresh token expiry: from REFRESH_TOKEN_EXPIRE_DAYS env var
- RT stored as hash in DB, raw token only in cookie

# Commit style:

- Conventional commits: feat:, fix:, chore:, refactor:
