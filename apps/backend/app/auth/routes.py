from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging
from sqlalchemy.exc import SQLAlchemyError
from config import get_db
from models import User, Role, AuthCode
from schemas import Token, GoogleUser, settings, UserCreate, UserBase
from auth import get_current_user, get_google_user_info, get_google_user_info_pkce, create_token, verify_token
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
def login_with_google(
    client_type: str = "web",
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    state: str | None = None
):
    """
    Initiate Google OAuth flow

    Args:
        client_type: "web" or "ios" - determines which OAuth client to use
        code_challenge: PKCE code challenge (required for mobile clients)
        code_challenge_method: Should be "S256" for PKCE
        state: CSRF protection token
    """
    # Select appropriate client configuration
    if client_type == "ios":
        client_id = settings.GOOGLE_IOS_CLIENT_ID
        redirect_uri = settings.GOOGLE_IOS_REDIRECT_URI
    else:
        client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = settings.GOOGLE_REDIRECT_URI

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true"
    }

    # Add PKCE parameters for mobile clients (required by Google OAuth2 policies)
    if code_challenge and code_challenge_method:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = code_challenge_method

    # Add state parameter for CSRF protection
    if state:
        params["state"] = state

    return RedirectResponse(f"{settings.GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}")

@router.get("/callback")
async def google_callback(request: Request, db: db_dependency):
    """
    Handle Google OAuth callback

    Accepts authorization code from Google and:
    1. Validates state parameter (CSRF protection)
    2. Exchanges code for user info
    3. Creates or retrieves user
    4. Generates temporary auth_code
    5. Redirects to appropriate client (web or mobile)
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    # Note: In production, validate state parameter against stored value
    # For now, we just pass it through for client-side validation

    user_info = await get_google_user_info(code)
    google_user = GoogleUser(**user_info)

    user = get_or_create_google_user(db, google_user)
    auth_code = create_auth_code(db, user)

    # Return auth_code for mobile to exchange for JWT tokens
    # Mobile will detect custom scheme redirect 
    return RedirectResponse(
        f"{settings.MOBILE_DEEP_LINK_SCHEME}oauth-callback?auth_code={auth_code}"
        + (f"&state={state}" if state else "")
    )

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

@router.post("/mobile/token")
async def mobile_token_exchange(
    db: db_dependency,
    code: str = Body(...),
    code_verifier: str = Body(...)
):
    user_info = await get_google_user_info_pkce(code, code_verifier)
    google_user = GoogleUser(**user_info)
    user = get_or_create_google_user(db, google_user)

    payload = {"sub": user.email, "name": user.name, "role": "user"}
    access = create_token(payload)
    refresh = create_token(payload, "refresh")

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name,
            "role": "user"
        }
    }


# ----- Protected route -----
@router.get("/protected")
def protected(current_user=Depends(get_current_user)):
    return {"message": f"Welcome {current_user.get('email', 'User')}"}

"""@router.get("/protected")
def protected(db: db_dependency, current_user=Depends(get_current_user)):
    user_id = current_user["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    return {"message": f"Welcome {user.name or user.email}!"}"""