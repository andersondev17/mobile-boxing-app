from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging
from sqlalchemy.exc import SQLAlchemyError
from config import get_db
from models import User, Role, AuthCode
from schemas import Token, GoogleUser, settings, UserCreate, UserBase
from auth import get_current_user, get_google_user_info, create_token, verify_token
from .services.auth_service import login_user, refresh_user_token, register_user
from .services.google_service import get_or_create_google_user, create_auth_code  
from typing import Annotated
from datetime import datetime
from urllib.parse import urlencode

router = APIRouter(prefix="/auth", tags=["Auth"])

db_dependency = Annotated[Session, Depends(get_db)]

# ----- Local Login -----
@router.post("/login", response_model=Token)
def login(db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()):
    tokens = login_user(db, form_data.username, form_data.password)
    if not tokens:
        raise HTTPException(400, "Invalid credentials")
    return tokens

@router.post("/refresh", response_model=Token)
def refresh_endpoint(refresh_token: str = Body(..., embed=True)):
    payload = verify_token(refresh_token, token_type="refresh")
    return refresh_user_token(payload)

@router.post("/register", response_model=UserBase)
def register(db: db_dependency, user: UserCreate):
    new_user = register_user(db, user)
    if not new_user:
        raise HTTPException(400, "Email already registered")

    return new_user

# ----- Google OAuth -----
@router.get("/login/google")
def login_with_google():
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true"
    }
    return RedirectResponse(f"{settings.GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}")

@router.get("/callback")
async def google_callback(request: Request, db: db_dependency):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    user_info = await get_google_user_info(code)
    google_user = GoogleUser(**user_info)

    user = get_or_create_google_user(db, google_user)
    auth_code = create_auth_code(db, user)

    return RedirectResponse(f"{settings.FRONTEND_URL}/oauth-callback?auth_code={auth_code}")

# ----- Exchange code -----
@router.post("/exchange-token")
def exchange_token(db: db_dependency, auth_code: str = Body(..., embed=True)):
    # Buscar el auth_code
    record = db.query(AuthCode).filter_by(code=auth_code).first()

    # Si no existe o expiró
    if not record or record.expires_at < datetime.utcnow():
        # Borrado seguro solo si existe
        if record:
            try:
                db.delete(record)
                db.commit()
            except Exception:
                db.rollback()
        # Retornar mensaje idempotente
        raise HTTPException(400, "Invalid or expired auth code")

    # Buscar usuario
    user = db.query(User).filter_by(email=record.user_email).first()
    if not user:
        raise HTTPException(404, "User not found")

    # Generar tokens JWT
    payload = {"sub": user.email, "name": user.name, "role": "user"}
    access = create_token(payload)
    refresh = create_token(payload, "refresh")

    # Eliminar auth_code de manera segura
    try:
        db.delete(record)
        db.commit()
    except Exception:
        db.rollback()

    # Retornar tokens
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


# ----- Protected route -----
@router.get("/protected")
def protected(current_user=Depends(get_current_user)):
    return {"message": f"Welcome {current_user['name']}!"}