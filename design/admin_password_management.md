# Admin Password Management Design

## Overview

This document describes the design for secure admin password management in the FastAPI admin panel. The system uses a hybrid approach: on first launch, the admin password is taken from an environment variable; after the password is changed via the UI, the new password is stored as a hash in MongoDB. If the hash is deleted from the database, the system falls back to using the environment variable password. Changing the password requires entering the current password for verification.

## Data Model

- The password hash is stored in a dedicated MongoDB collection, e.g., `admin_settings`.
- The collection contains a single document with a unique identifier (e.g., `_id: "admin"`).
- Example document:
  ```json
  {
    "_id": "admin",
    "password_hash": "$2b$12$..."
  }
  ```

## Authentication Logic

- **On login:**
  - If a password hash exists in the database, verify the provided password using the hash (with passlib/bcrypt).
  - If no hash exists, verify the password against the value from the environment variable (plain text).
- **On password change:**
  - Require the user to enter the current password.
  - Verify the current password using the same logic as above (hash or env).
  - If correct, hash the new password and store it in the database (overwriting any previous hash).
- **On hash deletion:**
  - If the password hash is deleted from the database, the system automatically falls back to using the environment variable password for authentication.

## API Changes

- **New endpoint:** `POST /admin/change-password`
  - Request body: `{ "current_password": "...", "new_password": "..." }`
  - Logic:
    - Verify `current_password` as described above.
    - If valid, hash `new_password` and store in DB.
    - Return success or error message.

## Security Considerations

- Use `passlib` (bcrypt) for password hashing.
- Never store or log plain-text passwords.
- Advise users to set a strong initial password in the environment variable and to change it after first login.
- If the password hash is deleted from the database, recommend changing the environment variable password as well.

## Migration and Backward Compatibility

- On first launch (no hash in DB), the system uses the environment variable password.
- After password change, only the hash in DB is used.
- Deleting the hash from DB resets authentication to the environment variable password.

## Example Usage

- **Resetting password:**
  - An admin can manually delete the password hash document from the `admin_settings` collection (e.g., via MongoDB shell or admin UI).
  - The system will then use the environment variable password for authentication.

---

*This design ensures secure, flexible, and user-friendly admin password management, supporting both initial setup and ongoing security best practices.* 