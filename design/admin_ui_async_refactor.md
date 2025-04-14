# Async Refactor Design: admin_ui.py

## Goal

Refactor the FastAPI admin UI routes in `admin_ui.py` to use asynchronous handlers (`async def`) for proper compatibility with the Motor async MongoDB driver. This will resolve runtime errors when accessing MongoDB collections and ensure the application is scalable and non-blocking.

## Motivation

- The current implementation uses synchronous route handlers, but interacts with Motor's async cursor, causing `TypeError: 'AsyncIOMotorCursor' object is not iterable`.
- FastAPI is designed for async I/O; using async handlers is best practice for performance and correctness.

## Scope

- Refactor all route handlers in `admin_ui.py` that interact with MongoDB to be `async def`.
- Use `await` and async methods (e.g., `to_list()`, `find_one()`, `insert_one()`, etc.).
- Ensure Jinja2 template rendering is compatible with async handlers (FastAPI's `Jinja2Templates` supports this since v0.95+).
- Test the `/admin/articles` page as the first step, then proceed to other endpoints.

## Steps

1. Identify all route handlers in `admin_ui.py` that access MongoDB.
2. Change their definitions to `async def`.
3. Replace blocking DB calls with their async equivalents:
   - Use `await db.articles.find().sort(...).to_list(length=100)` for lists (set a reasonable limit).
   - Use `await db.articles.find_one({...})` for single documents.
   - Use `await db.articles.insert_one({...})`, etc.
4. Ensure all template responses are returned correctly from async handlers.
5. Test `/admin/articles` page for correct rendering and absence of errors.
6. Gradually refactor and test other handlers.

## Risks & Considerations

- Jinja2Templates: FastAPI supports async template rendering, but if any custom template logic is blocking, it may need adjustment.
- All DB access must be awaited; missing `await` will cause runtime errors.
- If any dependencies or middlewares are not async-compatible, they may need refactoring.

## Rollout Plan

- Refactor and test one handler at a time (start with `/admin/articles`).
- Commit and test after each handler.
- Roll back if any issues are found.

## References
- [FastAPI async docs](https://fastapi.tiangolo.com/async/)
- [Motor async driver](https://motor.readthedocs.io/en/stable/)
- [Jinja2Templates async support](https://fastapi.tiangolo.com/advanced/templates/)

## Mandatory Requirement

All admin panel (FastAPI) routes that interact with MongoDB **must be implemented as asynchronous handlers** (`async def`).
This is required for correct operation with the Motor async MongoDB driver and to avoid runtime errors (such as 'AsyncIOMotorCursor object is not iterable' or '_asyncio.Future object is not subscriptable'). 