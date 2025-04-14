# JWT Authentication Design for Admin Panel (FastAPI)

## Problem Statement

The admin panel must be protected so that only authorized users can access CRUD endpoints and image upload functionality. Authentication should be based on JWT tokens. The solution must be simple, secure, and easy to integrate with the existing FastAPI structure.

## Requirements

- Only authenticated users can access protected endpoints (articles, images, etc.).
- Authentication is performed via username and password (from environment variables).
- On successful login, the user receives a JWT token.
- All protected endpoints require a valid JWT (via `Authorization: Bearer ...` header).
- JWT token has an expiration time (e.g., 1 hour).
- Swagger UI must support JWT authentication (Authorize button).
- No user registration or password reset is required (single admin user, credentials from env).

## Technology & Dependencies

- **FastAPI** (already used)
- **PyJWT** or **python-jose** for JWT encoding/decoding
- **passlib** (optional, for password hashing)
- No new database tables/collections required

## Architecture Overview

1. **Login Endpoint** (`POST /admin/login`):
    - Accepts username and password (JSON body).
    - Verifies credentials against environment variables.
    - On success, returns a JWT token (access token, optionally refresh token).
    - On failure, returns 401 Unauthorized.

2. **JWT Token**:
    - Encodes user identity (e.g., username) and expiration time.
    - Signed with a secret key (from environment variable, e.g., `JWT_SECRET_KEY`).
    - Uses HS256 algorithm.

3. **Dependency for Protected Endpoints**:
    - Custom FastAPI dependency checks for valid JWT in `Authorization` header.
    - If valid, allows access; if not, returns 401.
    - Applied to all `/admin` routes (articles, images, etc.).

4. **Swagger UI Integration**:
    - FastAPI's `OAuth2PasswordBearer` or custom security scheme enables "Authorize" button in Swagger UI.
    - Allows testing protected endpoints directly from docs.

## Implementation Plan

1. **Add new environment variables:**
    - `JWT_SECRET_KEY` (required)
    - `JWT_ALGORITHM` (default: HS256)
    - `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default: 60)

2. **Install dependencies (if not present):**
    - `python-jose[cryptography]` (preferred for FastAPI)
    - (Optional) `passlib[bcrypt]` for password hashing

3. **Implement login route:**
    - `POST /admin/login` (accepts JSON: `{ "username": ..., "password": ... }`)
    - Verifies credentials
    - Returns `{ "access_token": ..., "token_type": "bearer" }`

4. **JWT utility functions:**
    - Create/verify JWT tokens
    - Handle expiration

5. **Auth dependency:**
    - FastAPI dependency that extracts and validates JWT from header
    - Raises HTTP 401 if invalid/expired

6. **Apply dependency to all protected routes:**
    - Use `Depends(get_current_user)` in all `/admin` routers

7. **Update Swagger UI security scheme:**
    - Add `Bearer` auth to OpenAPI config

## Security Considerations

- Use strong, random `JWT_SECRET_KEY` in production
- Store credentials and secret only in environment variables
- Do not log sensitive data
- Set reasonable token expiration (1 hour by default)

## Example .env.dev additions

```dotenv
# JWT Auth
JWT_SECRET_KEY=your-very-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## References
- [FastAPI Security Docs](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [python-jose](https://python-jose.readthedocs.io/en/latest/)

---

*This document describes the design and implementation plan for JWT-based authentication in the admin panel. All implementation should follow this design for consistency and security.* 