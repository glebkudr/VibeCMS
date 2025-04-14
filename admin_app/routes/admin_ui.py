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

router = APIRouter()
templates = Jinja2Templates(directory="admin_app/templates")

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
async def login_get(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})

@router.post("/admin/login", response_class=HTMLResponse)
async def login_post(request: Request, response: Response, username: str = Form(...), password: str = Form(...)):
    db = request.app.state.mongo_db
    # MongoDB motor: нельзя использовать 'if not db', только 'if db is None' (см. design/projectrules.md)
    if db is None or username != "admin" or not await verify_admin_password(db, password):
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
async def articles_list(request: Request, user: str = Depends(get_current_user_ui)):
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
async def article_create_get(request: Request, user: str = Depends(get_current_user_ui)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("admin/article_create.html", {"request": request, "error": None, "user": user})

@router.post("/admin/articles/create", response_class=HTMLResponse)
async def article_create_post(request: Request, title: str = Form(...), slug: str = Form(...), content_md: str = Form(...), status: str = Form("draft"), user: str = Depends(get_current_user_ui)):
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
async def article_view(request: Request, article_id: str, user: str = Depends(get_current_user_ui)):
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
async def change_password_get(request: Request, user: str = Depends(get_current_user_ui)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": None, "success": None})

@router.post("/admin/change-password", response_class=HTMLResponse)
async def change_password_post(request: Request, current_password: str = Form(...), new_password: str = Form(...), user: str = Depends(get_current_user_ui)):
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
async def settings_get(request: Request, user: str = Depends(get_current_user_ui)):
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse("admin/change_password.html", {"request": request, "user": user, "error": None, "success": None, "title": "Settings"})

@router.post("/admin/settings", response_class=HTMLResponse)
async def settings_post(request: Request, current_password: str = Form(...), new_password: str = Form(...), user: str = Depends(get_current_user_ui)):
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