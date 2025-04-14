# Admin Panel UI Design (SPA)

## Problem Statement

The admin panel must provide a simple, secure, and user-friendly web interface for managing articles in the static site generator system. The UI should support authentication (JWT), CRUD operations for articles, and allow navigation to an article editing view (the editor itself will be implemented later).

## Main Features

1. **Authentication**
    - Login page (username/password, receives JWT on success)
    - Logout functionality (removes JWT, redirects to login)
    - All other pages require authentication (JWT in localStorage/cookie)

2. **Article Management (CRUD)**
    - List page: shows all articles (title, status, created/updated date, actions)
    - Create article: button to open a form for new article (title, slug, content, status)
    - View article: click on article in list to see details (title, content, status, etc.)
    - Delete article: action in list or view
    - Edit article: action in list or view (navigates to edit page — editor implementation is a separate task)

3. **Article View & Edit**
    - Article view page: shows all article fields, with an "Edit" button
    - Edit page: (to be implemented later)

## UI Flow

- User lands on `/login` (if not authenticated)
- After login, user is redirected to `/articles` (list)
- User can create, view, or delete articles from the list
- Clicking an article navigates to `/articles/:id` (view)
- On the view page, user can click "Edit" (navigates to `/articles/:id/edit`, not implemented yet)
- User can logout from any page

## Technology

- SPA (React, Vue, Svelte, or similar — to be decided)
- Uses the existing FastAPI backend (JWT auth, REST API)
- JWT stored in localStorage or cookie (for API requests)

## Security

- All API requests must include JWT in Authorization header
- Logout must clear JWT
- No registration or password reset (admin credentials from env)

## Out of Scope (for now)

- Article editor UI (to be implemented later)
- User management (only one admin user)
- Image upload UI (can be added later)

## References
- [JWT Auth Design](jwt_auth_design.md)

---

*This document describes the UI/UX and main flows for the admin panel SPA. Implementation should follow this design for consistency and usability.* 