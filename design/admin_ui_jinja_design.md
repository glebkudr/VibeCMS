# Admin Panel UI Design (Server-side, FastAPI + Jinja2)

## Problem Statement

The admin panel must provide a simple, secure, and user-friendly web interface for managing articles in the static site generator system. The UI should be rendered server-side using Jinja2 templates, with FastAPI handling routing and MongoDB as the data store.

## Main Features

1. **Authentication**
    - Login page (`/admin/login`): username/password form, sets JWT in cookie (or session cookie)
    - Logout endpoint (`/admin/logout`): clears cookie/session
    - All admin pages require authentication

2. **Article Management (CRUD)**
    - List page (`/admin/articles`): shows all articles (title, status, created/updated date, actions)
    - Create article (`/admin/articles/create`): form for new article (title, slug, content, status)
    - View article (`/admin/articles/{id}`): details of article, "Edit" and "Delete" buttons
    - Delete article (`/admin/articles/{id}/delete`): POST endpoint (with CSRF protection)
    - Edit article (`/admin/articles/{id}/edit`): (to be implemented later)

## UI Flow

- User lands on `/admin/login` (if not authenticated)
- After login, user is redirected to `/admin/articles`
- User can create, view, or delete articles from the list
- Clicking an article navigates to `/admin/articles/{id}` (view)
- On the view page, user can click "Edit" (navigates to `/admin/articles/{id}/edit`, not implemented yet)
- User can logout from any page

## Technology

- **FastAPI** (routes, form handling)
- **Jinja2** (HTML templates)
- **MongoDB** (article data)
- **Authentication**: JWT in HttpOnly cookie (preferred for statelessness) or server-side session (if easier for forms)
- **CSRF protection**: for POST/DELETE actions (can use a simple token in forms)

## Security

- All admin pages require authentication
- JWT or session cookie must be HttpOnly
- CSRF protection for all state-changing actions
- No registration or password reset (admin credentials from env)

## Out of Scope (for now)

- Article editor UI (to be implemented later)
- User management (only one admin user)
- Image upload UI (can be added later)

## References
- [JWT Auth Design](jwt_auth_design.md)

---

*This document describes the UI/UX and main flows for the admin panel server-side web interface. Implementation should follow this design for consistency and usability.* 