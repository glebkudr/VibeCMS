from fastapi import APIRouter, Request, Form, Response, status as http_status, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from admin_app.core.auth import create_access_token, authenticate_user, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, JWT_ALGORITHM
from jose import jwt, JWTError
from datetime import timedelta, datetime
import os
from admin_app.models import ArticleRead, ArticleStatus, TagRead, ArticleUpdate
from bson import ObjectId
from admin_app.core.admin_password import verify_admin_password, change_admin_password
import asyncio
import sys # Added for subprocess
import logging
from admin_app.main import get_templates
# Remove bleach import
# import bleach
# Import Sanitizer and constants
from html_sanitizer import Sanitizer
from admin_app.core.html_sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES, passthrough_url
from admin_app.core.utils import convert_objectid_to_str
from typing import Optional, List

logger = logging.getLogger(__name__) # Added for logging

router = APIRouter()

COOKIE_NAME = "admin_jwt"
COOKIE_MAX_AGE = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

# Dependency for UI routes: check JWT in cookie
def get_current_user_ui(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return RedirectResponse(url="/admin/login", status_code=http_status.HTTP_302_FOUND)
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/admin/login", status_code=http_status.HTTP_302_FOUND)
        return username
    except JWTError:
        return RedirectResponse(url="/admin/login", status_code=http_status.HTTP_302_FOUND)

# --- Tags UI --- #

@router.get("/admin/tags", response_class=HTMLResponse)
async def tags_list(
    request: Request,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates),
    create_error: Optional[str] = None # Add error param for create form
):
    """Renders the list of tags page."""
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    tags_list = []
    error_message = None
    if db is not None:
        try:
            # Fetch tags from the API route using request internally (or call DB directly)
            # Let's call DB directly for simplicity here
            tags_cursor = db.get_collection("tags").find().sort("slug", 1)
            raw_tags = await tags_cursor.to_list(length=None)
            tags_list = [convert_objectid_to_str(tag, TagRead) for tag in raw_tags]
            logger.info(f"Loaded {len(tags_list)} tags for UI list.")
        except Exception as e:
            logger.error(f"Error fetching tags for UI list: {e}", exc_info=True)
            error_message = "Could not load tags from database."
    else:
        error_message = "Database not available."

    return templates.TemplateResponse("admin/tags_list.html", {
        "request": request,
        "tags": tags_list,
        "user": user,
        "error": error_message,
        "create_error": create_error # Pass create error to template
    })

@router.post("/admin/tags/create")
async def create_tag_ui(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    description: Optional[str] = Form(None),
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates)
):
    """Handles the creation of a new tag from the UI form."""
    if isinstance(user, RedirectResponse):
        return user # Redirect if not logged in

    db = request.app.state.mongo_db
    if db is None:
        # Re-render the list page with an error
        return await tags_list(request, user, templates, create_error="Database not available")

    tags_collection = db.get_collection("tags")

    # Basic validation (slug format is handled by HTML pattern)
    if not name or not slug:
        return await tags_list(request, user, templates, create_error="Name and Slug are required.")

    # Check if slug already exists
    existing_tag = await tags_collection.find_one({"slug": slug})
    if existing_tag:
        logger.warning(f"UI attempt to create tag with existing slug '{slug}'.")
        return await tags_list(request, user, templates, create_error=f"Tag with slug '{slug}' already exists.")

    # Prepare tag data (non-system)
    tag_data = {
        "name": name,
        "slug": slug,
        "description": description,
        "required_fields": [], # Non-system tags don't have required fields initially
        "is_system": False
    }

    try:
        await tags_collection.insert_one(tag_data)
        logger.info(f"User '{user}' successfully created tag '{slug}' via UI.")
        # Redirect back to the tags list on success
        return RedirectResponse(url="/admin/tags", status_code=http_status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.error(f"Error creating tag '{slug}' via UI: {e}", exc_info=True)
        # Re-render the list page with a generic error
        return await tags_list(request, user, templates, create_error=f"Failed to create tag: {e}")

@router.post("/admin/tags/{tag_slug}/delete")
async def delete_tag_ui(
    request: Request,
    tag_slug: str,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates)
):
    """Handles the deletion of a non-system tag from the UI."""
    if isinstance(user, RedirectResponse):
        return user

    db = request.app.state.mongo_db
    if db is None:
        # Redirect back with a general error (or flash message if implemented)
        # For now, just log and redirect
        logger.error("Database not available during tag deletion attempt.")
        return RedirectResponse(url="/admin/tags?error=db_error", status_code=http_status.HTTP_303_SEE_OTHER)

    tags_collection = db.get_collection("tags")
    articles_collection = db.get_collection("articles")

    # Find the tag
    existing_tag = await tags_collection.find_one({"slug": tag_slug})

    if not existing_tag:
        logger.warning(f"UI attempt to delete non-existent tag '{tag_slug}'.")
        # Redirect back with error
        return RedirectResponse(url="/admin/tags?error=not_found", status_code=http_status.HTTP_303_SEE_OTHER)

    if existing_tag.get("is_system", False):
        logger.warning(f"UI attempt to delete system tag '{tag_slug}'.")
        # Redirect back with error
        return RedirectResponse(url="/admin/tags?error=system_tag", status_code=http_status.HTTP_303_SEE_OTHER)

    # Delete the tag document
    try:
        delete_result = await tags_collection.delete_one({"slug": tag_slug})
        if delete_result.deleted_count == 0:
            logger.error(f"Tag '{tag_slug}' found but failed to delete via UI.")
            return RedirectResponse(url="/admin/tags?error=delete_failed", status_code=http_status.HTTP_303_SEE_OTHER)
        logger.info(f"User '{user}' successfully deleted tag document '{tag_slug}' via UI.")
    except Exception as e:
        logger.error(f"Error deleting tag document '{tag_slug}' via UI: {e}", exc_info=True)
        return RedirectResponse(url="/admin/tags?error=delete_error", status_code=http_status.HTTP_303_SEE_OTHER)

    # Remove the tag slug from all articles
    try:
        update_result = await articles_collection.update_many(
            {"tags": tag_slug},
            {"$pull": {"tags": tag_slug}}
        )
        logger.info(f"Removed tag '{tag_slug}' from {update_result.modified_count} articles via UI delete.")
    except Exception as e:
        # Log the error but continue, as the tag doc is deleted.
        logger.error(f"Error removing tag '{tag_slug}' from articles via UI delete: {e}", exc_info=True)

    # Redirect back to the tags list on success
    return RedirectResponse(url="/admin/tags?success=deleted", status_code=http_status.HTTP_303_SEE_OTHER)

# TODO: Add route for viewing articles associated with a tag (/admin/tags/{slug}/articles)

# --- End Tags UI --- #

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
        return templates.TemplateResponse("admin/login.html", {"request": request, "error": "Invalid username or password"}, status_code=http_status.HTTP_401_UNAUTHORIZED)
    access_token = create_access_token({"sub": username}, expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    response = RedirectResponse(url="/admin/articles", status_code=http_status.HTTP_302_FOUND)
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
    response = RedirectResponse(url="/admin/login", status_code=http_status.HTTP_302_FOUND)
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
    content_html: str = Form(...),
    status_form: str = Form("draft", alias="status"), # Rename parameter, keep form name
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates) # Add dependency
):
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    if db is None:
        return templates.TemplateResponse("admin/article_create.html", {"request": request, "error": "Database not available", "user": user}, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    now = datetime.utcnow()
    article_doc = {
        "title": title,
        "slug": slug,
        "content_html": content_html,
        "status": status_form, # Use renamed parameter
        "created_at": now,
        "updated_at": now,
        "versions": []
    }
    # Create a reusable sanitizer instance
    sanitizer_config = {
        'tags': set(ALLOWED_TAGS),
        'attributes': ALLOWED_ATTRIBUTES, # Use original attributes
        'empty': {'hr', 'br', 'img', 'span'},  # Add 'span' to allowed empty tags
        'sanitize_href': passthrough_url,
        'element_preprocessors': [], # Disable default preprocessors (like span to strong/em)
        # 'sanitize_src': passthrough_url, # This param doesn't exist
        # Add other html-sanitizer specific settings if needed
    }
    sanitizer = Sanitizer(sanitizer_config)

    try:
        # Log FULL HTML before sanitization
        logger.info(f"Received content_html for create (UI):\n{article_doc.get('content_html', '')}") # Log full content
        # Use html-sanitizer
        sanitized_html = sanitizer.sanitize(article_doc.get('content_html', ''))
        article_doc['content_html'] = sanitized_html
        # Log HTML AFTER sanitization
        logger.info(f"Sanitized content_html for create (UI):\n{sanitized_html}")
    except Exception as e:
        logger.error(f"Error sanitizing HTML content during UI article creation: {e}", exc_info=True)
        return templates.TemplateResponse("admin/article_create.html", {"request": request, "error": "Failed to process article content", "user": user}, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        result = await db.articles.insert_one(article_doc)
        return RedirectResponse(url=f"/admin/articles/{result.inserted_id}", status_code=http_status.HTTP_302_FOUND)
    except Exception as e:
        return templates.TemplateResponse("admin/article_create.html", {"request": request, "error": str(e), "user": user}, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": "Database not available", "user": user}, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        oid = ObjectId(article_id)
        doc = await db.articles.find_one({"_id": oid})
        if not doc:
            return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": "Article not found", "user": user}, status_code=http_status.HTTP_404_NOT_FOUND)
        doc["id"] = str(doc["_id"])
        doc["created_at"] = doc["created_at"].strftime("%Y-%m-%d %H:%M") if "created_at" in doc else ""
        doc["updated_at"] = doc["updated_at"].strftime("%Y-%m-%d %H:%M") if "updated_at" in doc else ""
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "article": doc, "user": user})
    except Exception as e:
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": str(e), "user": user}, status_code=http_status.HTTP_400_BAD_REQUEST)

@router.post("/admin/articles/{article_id}/delete")
async def article_delete(request: Request, article_id: str, user: str = Depends(get_current_user_ui)):
    if isinstance(user, RedirectResponse):
        return user
    db = request.app.state.mongo_db
    if db is None:
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": "Database not available", "user": user}, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        oid = ObjectId(article_id)
        await db.articles.delete_one({"_id": oid})
        return RedirectResponse(url="/admin/articles", status_code=http_status.HTTP_302_FOUND)
    except Exception as e:
        return templates.TemplateResponse("admin/article_view.html", {"request": request, "error": str(e), "user": user}, status_code=http_status.HTTP_400_BAD_REQUEST)

@router.get("/", include_in_schema=False)
async def root(request: Request):
    user = get_current_user_ui(request)
    if isinstance(user, RedirectResponse):
        return RedirectResponse(url="/admin/login", status_code=http_status.HTTP_302_FOUND)
    return RedirectResponse(url="/admin/articles", status_code=http_status.HTTP_302_FOUND)

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
        return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": "Database not available", "success": None}, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    ok = await change_admin_password(db, current_password, new_password)
    if not ok:
        return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": "Current password is incorrect", "success": None}, status_code=http_status.HTTP_401_UNAUTHORIZED)
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
        return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": "Database not available", "success": None}, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    ok = await change_admin_password(db, current_password, new_password)
    if not ok:
        return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": "Current password is incorrect", "success": None}, status_code=http_status.HTTP_401_UNAUTHORIZED)
    return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": None, "success": "Password changed successfully"})

async def run_generator_script():
    """Runs the static site generator script as a subprocess."""
    logger.info("Starting static site generation...")
    try:
        # Assuming the generator script is runnable with python and is in the generator/ directory
        script_path = os.path.join(os.path.dirname(__file__), "..", "..", "generator", "generate.py")
        logger.info(f"Generator script path: {script_path}")

        # Determine the Python interpreter to use
        # On Windows, it might be 'python', on Linux/macOS 'python3' or sys.executable
        python_executable = sys.executable # Use the same interpreter running FastAPI
        logger.info(f"Using Python executable: {python_executable}")

        # Ensure the script path is absolute
        script_path = os.path.abspath(script_path)

        # Run the script in the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
        logger.info(f"Running script in directory: {project_root}")

        process = await asyncio.create_subprocess_exec(
            python_executable,
            script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_root # Set the current working directory
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info("Static site generation completed successfully.")
            logger.info(f"Generator stdout:\n{stdout.decode()}")
        else:
            logger.error(f"Static site generation failed with return code {process.returncode}.")
            logger.error(f"Generator stderr:\n{stderr.decode()}")
    except FileNotFoundError:
        logger.error(f"Generator script not found at {script_path} or python executable {python_executable} not found.")
    except Exception as e:
        logger.error(f"An error occurred during static site generation: {e}", exc_info=True)

@router.post("/admin/generate-site", status_code=http_status.HTTP_202_ACCEPTED) # Use http_status
async def trigger_generation(request: Request, user: str = Depends(get_current_user_ui)):
    """Triggers the static site generation script asynchronously."""
    if isinstance(user, RedirectResponse):
        return user
    # Run the script in the background
    asyncio.create_task(run_generator_script())
    # Return immediately with 202 Accepted
    return {"message": "Static site generation started."}

@router.get("/admin/articles/{article_id}/edit", response_class=HTMLResponse)
async def article_edit_get(
    request: Request,
    article_id: str,
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates)
):
    """Renders the article edit page."""
    if isinstance(user, RedirectResponse):
        return user

    db = request.app.state.mongo_db
    if db is None:
        raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available")

    try:
        obj_id = ObjectId(article_id)
    except Exception:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid article ID format")

    articles_collection = db.get_collection("articles")
    article_data = await articles_collection.find_one({"_id": obj_id})

    if not article_data:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Article not found")

    # Fetch all tags
    tags_collection = db.get_collection("tags")
    all_tags_cursor = tags_collection.find().sort("slug", 1)
    all_tags_raw = await all_tags_cursor.to_list(length=None)
    all_tags = [convert_objectid_to_str(tag, TagRead) for tag in all_tags_raw]

    # Ensure article data has 'tags' key, default to empty list if missing
    article_data['tags'] = article_data.get('tags', [])

    # Convert article data for template
    article_for_template = convert_objectid_to_str(article_data, ArticleRead)

    return templates.TemplateResponse("admin/article_edit.html", {
        "request": request,
        "article": article_for_template,
        "statuses": [s.value for s in ArticleStatus], # Pass available statuses
        "all_tags": all_tags, # Pass all tags
        "user": user,
        "error": None # Or pass potential error messages
    })

@router.post("/admin/articles/{article_id}/edit", response_class=HTMLResponse)
async def article_edit_post(
    request: Request,
    article_id: str,
    title: str = Form(...),
    slug: str = Form(...),
    content_html: str = Form(...),
    status_form: str = Form(..., alias="status"), # Renamed parameter, maps to form field "status"
    tags_form: List[str] = Form([], alias="tags"), # Receive list of tag slugs
    user: str = Depends(get_current_user_ui),
    templates: Jinja2Templates = Depends(get_templates)
):
    """Handles the submission of the edited article form."""
    if isinstance(user, RedirectResponse):
        return user

    db = request.app.state.mongo_db
    if db is None:
        # How to handle error? Re-render form with error?
        # For now, raise HTTPException, but maybe redirect or re-render is better UI
        raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not available")

    try:
        obj_id = ObjectId(article_id)
    except Exception:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid article ID format")

    articles_collection = db.get_collection("articles")

    # Fetch the existing article to preserve fields not in the form
    existing_article = await articles_collection.find_one({"_id": obj_id})
    if not existing_article:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Article not found")

    # Sanitize HTML content before saving
    sanitizer = Sanitizer({
        'tags': ALLOWED_TAGS,
        'attributes': ALLOWED_ATTRIBUTES,
        'strip': False,
        'allow_comments': False,
        'allow_empty': True,
        # Add passthrough_url if needed for certain attributes like iframe src
        # 'element_preprocessors': [lambda element: passthrough_url(element, 'src')],
    })
    sanitized_content = sanitizer.sanitize(content_html)

    # Prepare update data
    try:
        article_status = ArticleStatus(status_form)
    except ValueError:
        # Handle invalid status value - re-render form with error?
        # For now, default to draft or raise error
        # Let's re-render the form with an error
        logger.error(f"Invalid status value submitted: {status_form}")
        # Need to refetch data to re-render the form correctly
        article_for_template = convert_objectid_to_str(existing_article, ArticleRead)
        # Fetch tags again
        tags_collection = db.get_collection("tags")
        all_tags_cursor = tags_collection.find().sort("slug", 1)
        all_tags_raw = await all_tags_cursor.to_list(length=None)
        all_tags = [convert_objectid_to_str(tag, TagRead) for tag in all_tags_raw]

        return templates.TemplateResponse("admin/article_edit.html", {
            "request": request,
            "article": article_for_template, # Use existing data for re-render
            "statuses": [s.value for s in ArticleStatus],
            "all_tags": all_tags,
            "user": user,
            "error": f"Invalid status value: '{status_form}'. Allowed values are: {[s.value for s in ArticleStatus]}"
        }, status_code=http_status.HTTP_400_BAD_REQUEST)

    article_data = {
        "title": title,
        "slug": slug,
        "content_html": sanitized_content, # Use sanitized HTML
        "status": article_status,
        "tags": tags_form, # Add the received tags
        "updated_at": datetime.utcnow() # Update timestamp
    }

    # Validate with Pydantic model (optional, but good practice)
    # Note: ArticleUpdate allows partial updates, so we might need ArticleCreate model or a specific Edit model
    # For now, we directly update the fields. Consider validation later.

    try:
        update_result = await articles_collection.update_one(
            {"_id": obj_id},
            {"$set": article_data}
        )

        if update_result.matched_count == 0:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Article not found during update")

        logger.info(f"Article '{article_id}' updated successfully by user '{user}'.")
        # Redirect to the article view page on success
        return RedirectResponse(url=f"/admin/articles/{article_id}", status_code=http_status.HTTP_303_SEE_OTHER)

    except Exception as e:
        logger.error(f"Error updating article {article_id}: {e}", exc_info=True)
        # Re-render form with error message
        article_for_template = convert_objectid_to_str(existing_article, ArticleRead)
        # Fetch tags again
        tags_collection = db.get_collection("tags")
        all_tags_cursor = tags_collection.find().sort("slug", 1)
        all_tags_raw = await all_tags_cursor.to_list(length=None)
        all_tags = [convert_objectid_to_str(tag, TagRead) for tag in all_tags_raw]

        return templates.TemplateResponse("admin/article_edit.html", {
            "request": request,
            "article": article_for_template, # Use existing data
            "statuses": [s.value for s in ArticleStatus],
            "all_tags": all_tags,
            "user": user,
            "error": f"Failed to update article: {e}"
        }, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- End Article CRUD UI --- # 