## Prompt Instructions:

# Naming conventions:

- snake_case = functions, files_names
- CapCase = applies to classes

# Timestamps:

int(utc_now_timestamp)

# Guide:

- Core logic goes into app/core
- Services goes into app/services
- Api's goes into app/apis
- Schemas goes into app/schemas
  -- Requests and Response Schemas using Pydantic v2
  --- Request Schemas goes into schemas/request
  --- Response Schemas goes into schemas/response
- Utils go into app/utils
- Tests fo into tests
  -- tests use pytest
