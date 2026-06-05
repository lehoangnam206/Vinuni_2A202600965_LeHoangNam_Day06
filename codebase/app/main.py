from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from .auth import login_user, register_user
from .chatbot import build_chat_response, get_user_memory
from .chat_ui import CHAT_HTML
from .csv_importer import import_csv_to_mongo
from .db import close_client, get_db
from .ingredient_search import search_ingredients
from .recipe_search import search_recipes


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    close_client()


app = FastAPI(
    title="Recipe Search API",
    description="Import CSV vao MongoDB va search mon an theo ten mon, tag hoac nguyen lieu.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(PyMongoError)
async def mongo_exception_handler(_request, exc: PyMongoError):
    close_client()
    return JSONResponse(
        status_code=503,
        content={
            "detail": "MongoDB dang khong ket noi duoc. Kiem tra mongo_url/IP whitelist Atlas roi thu lai.",
            "error": exc.__class__.__name__,
        },
    )


@app.get("/")
def root():
    return {
        "message": "Recipe Search API",
        "docs": "/docs",
        "chat": "/chat",
        "recipeSearchExample": "/api/search?q=trung",
        "foodSearchExample": "/api/ingredients/search?q=thit",
        "chatbotExample": "/api/chat?message=toi%20muon%20an%20dau%20phu%20sot%20ca%20chua",
    }


@app.get("/chat", response_class=HTMLResponse)
def chat_page():
    return HTMLResponse(CHAT_HTML)


@app.get("/healthz")
def healthz():
    try:
        db = get_db()
        db.command("ping")
        return {"status": "ok", "database": db.name}
    except Exception as exc:
        close_client()
        return {"status": "degraded", "error": exc.__class__.__name__}


@app.post("/api/import-csv")
def import_csv(reset: bool = Query(default=True)):
    return import_csv_to_mongo(get_db(), reset=reset)


@app.get("/api/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(default=20, ge=1, le=50)):
    results = search_recipes(get_db(), q, limit=limit)
    if not results:
        raise HTTPException(status_code=404, detail="Khong tim thay mon an phu hop")
    return {"q": q, "total": len(results), "results": results}


@app.get("/api/recipes/search")
def search_recipes_alias(q: str = Query(..., min_length=1), limit: int = Query(default=20, ge=1, le=50)):
    return search(q=q, limit=limit)


@app.get("/api/ingredients/search")
def search_foods(q: str = Query(..., min_length=1), limit: int = Query(default=20, ge=1, le=50)):
    results = search_ingredients(get_db(), q, limit=limit)
    if not results:
        raise HTTPException(status_code=404, detail="Khong tim thay thuc pham phu hop")
    return {"q": q, "total": len(results), "results": results}


@app.get("/api/foods/search")
def search_foods_alias(q: str = Query(..., min_length=1), limit: int = Query(default=20, ge=1, le=50)):
    return search_foods(q=q, limit=limit)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = Field(default="default", min_length=1)


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=40)
    password: str = Field(..., min_length=6, max_length=128)


def _auth_response(user: dict[str, str]):
    memory = get_user_memory(get_db(), user["userId"])
    return {"user": user, "memory": memory}


@app.post("/api/auth/register")
def auth_register(payload: AuthRequest):
    try:
        return _auth_response(register_user(get_db(), payload.username, payload.password))
    except ValueError as exc:
        code = str(exc)
        if code == "USERNAME_EXISTS":
            raise HTTPException(status_code=409, detail="Ten dang nhap da ton tai") from exc
        if code == "USERNAME_TOO_SHORT":
            raise HTTPException(status_code=400, detail="Ten dang nhap can it nhat 3 ky tu") from exc
        if code == "PASSWORD_TOO_SHORT":
            raise HTTPException(status_code=400, detail="Mat khau can it nhat 6 ky tu") from exc
        raise HTTPException(status_code=400, detail="Khong tao duoc tai khoan") from exc


@app.post("/api/auth/login")
def auth_login(payload: AuthRequest):
    try:
        return _auth_response(login_user(get_db(), payload.username, payload.password))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Sai ten dang nhap hoac mat khau") from exc


@app.post("/api/chat")
def chat(payload: ChatRequest):
    return build_chat_response(get_db(), payload.message, user_id=payload.user_id)


@app.get("/api/chat")
def chat_get(message: str = Query(..., min_length=1), user_id: str = Query(default="default", min_length=1)):
    return build_chat_response(get_db(), message, user_id=user_id)


@app.get("/api/memory")
def memory_get(user_id: str = Query(default="default", min_length=1)):
    return get_user_memory(get_db(), user_id)


@app.delete("/api/user/allergies")
def clear_user_allergies(user_id: str = Query(..., min_length=1)):
    get_db().user_memories.update_one(
        {"userId": user_id},
        {"$set": {"allergies": [], "allergyNote": "", "allergySourceNote": ""}}
    )
    return {"status": "success"}


@app.delete("/api/user/chat_history")
def clear_chat_history(user_id: str = Query(..., min_length=1)):
    get_db().user_memories.update_one(
        {"userId": user_id},
        {"$set": {"chatHistory": []}}
    )
    return {"status": "success"}
