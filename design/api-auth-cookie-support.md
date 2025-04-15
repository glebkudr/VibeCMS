# Design Document: API Auth via Cookie Support

## Problem Statement

Currently, API endpoints (such as image upload) require JWT authentication via the `Authorization: Bearer` header. However, the admin UI authenticates users via the `admin_jwt` cookie. As a result, authenticated users in the admin panel cannot use API endpoints (e.g., image upload) without manually providing a Bearer token, leading to 401 Unauthorized errors.

## Goal

Allow API endpoints to accept JWT tokens from either the `Authorization` header or the `admin_jwt` cookie, so that authenticated users in the admin UI can use API endpoints seamlessly.

## Requirements

- API endpoints must accept JWT tokens from:
  - The `Authorization: Bearer` header (current behavior)
  - The `admin_jwt` cookie (new behavior)
- If both are present, the header takes precedence.
- If neither is present or the token is invalid, return 401 Unauthorized.
- No changes to token issuance, expiration, or security model.

## Implementation Plan

1. Update the `get_current_user` dependency in `admin_app/core/auth.py`:
    - Accept an optional `Request` parameter.
    - Try to extract the token from the `Authorization` header (as before).
    - If not found, try to extract the token from the `admin_jwt` cookie.
    - If neither is present, raise 401.
    - Validate the token as before.
2. Update docstrings and add comments for maintainability.
3. Test:
    - Image upload from the admin UI (should succeed if logged in via UI).
    - API access via Swagger UI (should still work with Bearer token).

## Security Considerations

- JWT validation logic remains unchanged.
- No change to token issuance or expiration.
- This approach does not weaken security, as the same JWT is used and validated.

## Rollout

- No migration or client-side changes required.
- No new dependencies.

--- 