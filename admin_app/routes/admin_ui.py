from fastapi import APIRouter, Request, Form, Response, status, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from admin_app.core.auth import create_access_token, authenticate_user, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, JWT_ALGORITHM
from jose import jwt, JWTError
from datetime import timedelta, datetime
import os
from admin_app.models import ArticleRead, ArticleStatus
from bson import ObjectId
from admin_app.core.admin_password import verify_admin_password, change_admin_password
import asyncio
import sys # Added for subprocess
import logging
from admin_app.main import get_templates

logger = logging.getLogger(__name__) # Added for logging

router = APIRouter()

COOKIE_NAME = "admin_jwt"
COOKIE_MAX_AGE = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

# Dependency for UI routes: check JWT in cookie
def get_current_user_ui(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return RedirectResponse(url="/admin/login", status_code=302)
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/admin/login", status_code=302)
        return username
    except JWTError:
        return RedirectResponse(url="/admin/login", status_code=302)

@router.get("/admin/login", response_class=HTMLResponse)
async def login_get(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})

@router.post("/admin/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    db = request.app.state.mongo_db
    # MongoDB motor: нельзя использовать 'if not db', только 'if db is None' (см. design/projectrules.md)
    if db is None or username != "admin" or not await verify_admin_password(db, password):
        # Use the injected templates instance
        return templates.TemplateResponse("admin/login.html", {"request": request, "error": "Invalid username or password"}, status_code=401)
    access_token = create_access_token({"sub": username}, expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    response = RedirectResponse(url="/admin/articles", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=COOKIE_MAX_AGE,
        expires=COOKIE_MAX_AGE,
        samesite="lax",
        secure=False # Set to True in production with HTTPS
    )
    return response

@router.get("/admin/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(COOKIE_NAME)
    return response

@router.get("/admin/articles", response_class=HTMLResponse)
async def articles_list(
    request: Request,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    articles = []
    if db is not None:
        cursor = db.articles.find().sort("created_at", -1)
        articles = await cursor.to_list(length=100)
    for a in articles:
        a["id"] = str(a["_id"])
        a["created_at"] = a["created_at"].strftime("%Y-%m-%d %H:%M") if "created_at" in a else ""
        a["updated_at"] = a["updated_at"].strftime("%Y-%m-%d %H:%M") if "updated_at" in a else ""
    return templates.TemplateResponse("admin/articles_list.html", {"request": request, "articles": articles, "user": user})

@router.get("/admin/articles/create", response_class=HTMLResponse)
async def article_create_get(
    request: Request,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("admin/article_create.html", {"request": request, "error": None, "user": user})

@router.post("/admin/articles/create", response_class=HTMLResponse)
async def article_create_post(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    content_md: str = Form(...),
    status: str = Form("draft"),
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    if db is None:
        return templates.TemplateResponse("admin/article_create.html", {"request": request, "error": "Database not available", "user": user}, status_code=500)
    now = datetime.utcnow()
    article_doc = {
        "title": title,
        "slug": slug,
        "content_md": content_md,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "versions": []
    }
    try:
        result = await db.articles.insert_one(article_doc)
        return RedirectResponse(url=f"/admin/articles/{result.inserted_id}", status_code=302)
    except Exception as e:
        return templates.TemplateResponse("admin/article_create.html", {"request": request, "error": str(e), "user": user}, status_code=500)

@router.get("/admin/articles/{article_id}", response_class=HTMLResponse)
async def article_view(
    request: Request,
    article_id: str,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    if db is None:
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": "Database not available", "user": user}, status_code=500)
    try:
        oid = ObjectId(article_id)
        doc = await db.articles.find_one({"_id": oid})
        if not doc:
            return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": "Article not found", "user": user}, status_code=404)
        doc["id"] = str(doc["_id"])
        doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M") if "created_at" in doc else ""
        doc["updated_at"] = doc["updated_at"].strftime("%Y-%m-%d %H:%M") if "updated_at" in doc else ""
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "article": doc, "user": user})
    except Exception as e:
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": str(e), "user": user}, status_code=400)

@router.post("/admin/articles/{article_id}/delete")
async def article_delete(request: Request, article_id: str, user: str = Depends(get_current_user_ui)):
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    if db is None:
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": "Database not available", "user": user}, status_code=500)
    try:
        oid = ObjectId(article_id)
        await db.articles.delete_one({"_id": oid})
        return RedirectResponse(url="/admin/articles", status_code=302)
    except Exception as e:
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": str(e), "user": user}, status_code=400)

@router.get("/", include_in_schema=False)
async def root(request: Request):
    user = get_current_user_ui(request)
    if isinstance(user, RedirectResponse):
        return RedirectResponse(url="/admin/login", status_code=302)
    return RedirectResponse(url="/admin/articles", status_code=302)

@router.get("/admin/change-password", response_class=HTMLResponse)
async def change_password_get(
    request: Request,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": None, "success": None})

@router.post("/admin/change-password", response_class=HTMLResponse)
async def change_password_post(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    # MongoDB motor: нельзя использовать 'if not db', только 'if db is None' (см. design/projectrules.md)
    if db is None:
        return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": "Database not available", "success": None}, status_code=500)
    ok = await change_admin_password(db, current_password, new_password)
    if not ok:
        return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": "Current password is incorrect", "success": None}, status_code=401)
    return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": None, "success": "Password changed successfully"})

@router.get("/admin/settings", response_class=HTMLResponse)
async def settings_get(
    request: Request,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": None, "success": None, "title": "Settings"})

@router.post("/admin/settings", response_class=HTMLResponse)
async def settings_post(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    # MongoDB motor: нельзя использовать 'if not db', только 'if db is None' (см. design/projectrules.md)
    if db is None:
        return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": "Database not available", "success": None, "title": "Settings"}, status_code=500)
    ok = await change_admin_password(db, current_password, new_password)
    if not ok:
        return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": "Current password is incorrect", "success": None, "title": "Settings"}, status_code=401)
    return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": None, "success": "Password changed successfully", "title": "Settings"})

async def run_generator_script():
    """Run the static site generator script as a subprocess."""
    logger.info("Starting generator script execution...")
    try:
        # Correct path to generator script assuming it's one level up
        generator_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../generator/generate.py'))
        logger.info(f"Generator script path: {generator_script_path}")

        # Ensure the script exists
        if not os.path.exists(generator_script_path):
            logger.error(f"Generator script not found at {generator_script_path}")
            return {"status": "error", "message": "Generator script not found."}

        # Execute the script using the same Python interpreter
        # Run in a separate process to avoid blocking the FastAPI event loop
        process = await asyncio.create_subprocess_exec(
            sys.executable, generator_script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info("Generator script finished successfully.")
            logger.info(f"stdout:\n{stdout.decode()}")
            return {"status": "success", "message": "Static site generated successfully."}
        else:
            logger.error(f"Generator script failed with code {process.returncode}.")
            logger.error(f"stderr:\n{stderr.decode()}")
            return {"status": "error", "message": f"Generator script failed: {stderr.decode()}"}

    except Exception as e:
        logger.exception("Failed to run generator script")
        return {"status": "error", "message": f"Failed to run generator script: {str(e)}"}

@router.post("/admin/generate-site", status_code=202) # Use 202 Accepted
async def trigger_generation(request: Request, user: str = Depends(get_current_user_ui)):
    if isinstance(user, RedirectResponse):
        return user # Redirect if not logged in
    logger.info(f"User '{user}' triggered site generation.")
    # Run the generator script in the background without waiting for it to finish
    # Note: This means the response returns immediately, and generation happens async.
    # For better feedback, consider using background tasks or a task queue.
    asyncio.create_task(run_generator_script())
    return {"message": "Static site generation process started."}

@router.get("/admin/articles/{article_id}/edit", response_class=HTMLResponse)
async def article_edit_get(
    request: Request,
    article_id: str,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates)
):
    """Displays the form to edit an existing article."""
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    if db is None:
        # Handle error appropriately, maybe redirect or show error page
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        oid = ObjectId(article_id)
        doc = await db.articles.find_one({"_id": oid})
        if not doc:
            raise HTTPException(status_code=404, detail="Article not found")

        # Prepare article data for the template
        article_data = {
            "id": str(doc["_id"]),
            "title": doc.get("title", ""),
            "slug": doc.get("slug", ""),
            "content_md": doc.get("content_md", ""),
            "status": doc.get("status", ArticleStatus.DRAFT.value), # Ensure status is a string value
            # Add other fields if needed by the template
        }

        return templates.TemplateResponse(
            "admin/article_edit.html",
            {
                "request": request,
                "article": article_data,
                "error": None,
                "user": user
            }
        )
    except ValueError: # Catch invalid ObjectId format
        raise HTTPException(status_code=400, detail="Invalid article ID format")
    except Exception as e:
        logger.error(f"Error fetching article {article_id} for edit: {e}", exc_info=True)
        # Handle error appropriately
        raise HTTPException(status_code=500, detail="Error fetching article for editing")

@router.post("/admin/articles/{article_id}/edit", response_class=HTMLResponse)
async def article_edit_post(
    request: Request,
    article_id: str,
    title: str = Form(...),
    slug: str = Form(...),
    content_md: str = Form(...), # This comes from the hidden input updated by Milkdown
    status: str = Form(...),
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates)
):
    """Handles the submission of the article edit form."""
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        oid = ObjectId(article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID format")

    try:
        # Find the existing document first to save its state for versioning (if enabled)
        existing_doc = await db.articles.find_one({"_id": oid})
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Article not found for update")

        # --- Versioning Logic (Optional - Mirroring PUT /api/admin/articles/{id}) ---
        # prev_version = {
        #     "title": existing_doc.get("title"),
        #     "slug": existing_doc.get("slug"),
        #     "content_md": existing_doc.get("content_md"),
        #     "status": existing_doc.get("status", ArticleStatus.DRAFT.value),
        #     "updated_at": existing_doc.get("updated_at")
        # }
        # --------------------------------------------------------------------------

        update_data = {
            "title": title,
            "slug": slug,
            "content_md": content_md,
            "status": status,
            "updated_at": datetime.utcnow()
        }

        update_operation = {
            "$set": update_data,
            # "$push": {"versions": prev_version} # Uncomment if using versioning
        }

        result = await db.articles.update_one({"_id": oid}, update_operation)

        if result.matched_count == 0:
            logger.error(f"Update failed: Article {article_id} found but not matched for update.")
            # Maybe show error on edit page?
            raise HTTPException(status_code=404, detail="Article not found during update")

        # Redirect to the view page after successful update
        return RedirectResponse(url=f"/admin/articles/{article_id}", status_code=302)

    except Exception as e:
        logger.error(f"Error updating article {article_id}: {e}", exc_info=True)
        # Re-render edit form with error
        article_data = {
            "id": article_id,
            "title": title,
            "slug": slug,
            "content_md": content_md,
            "status": status,
        }
        return templates.TemplateResponse(
            "admin/article_edit.html",
            {
                "request": request,
                "article": article_data,
                "error": f"Failed to update article: {str(e)}",
                "user": user
            },
            status_code=500
        ) 