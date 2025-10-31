from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from config import get_db
from models import User
from auth import create_access_token, create_refresh_token, verify_token, get_current_user, role_required
from schemas import Token, GoogleUser
from schemas import settings
import httpx
from urllib.parse import urlencode
from typing import Annotated

router = APIRouter(prefix="/auth", tags=["Auth"])

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: db_dependency):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or form_data.password != "demo":  # Reemplaza con hash real
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access = create_access_token({"sub": user.id, "role": user.role})
    refresh = create_refresh_token({"sub": user.id, "role": user.role})
    return Token(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str) -> Token:
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = create_access_token({"sub": payload["sub"], "role": payload.get("role")})
    
    new_refresh = create_refresh_token({"sub": payload["sub"], "role": payload.get("role")})
    return Token(access_token=new_access, refresh_token=new_refresh)

@router.get("/login/google")
def login_with_google():
    query_params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return RedirectResponse(f"{settings.GOOGLE_AUTH_ENDPOINT}?{urlencode(query_params)}")

@router.get("/auth/callback")
async def google_callback(request: Request, db: db_dependency):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    user_info = await get_google_user_info(code)
    google_user = GoogleUser(**user_info)

    # Buscar o crear usuario
    user_db = db.query(User).filter(User.email == google_user.email).first()
    if not user_db:
        user = User(
            email=google_user.email,
            name=google_user.name,
            role="user",  # Puedes personalizar esto
            email_verified=True,
        )
        db.add(user_db)
        db.commit()
        db.refresh(user_db)

    payload = {
        "sub": user_db.email, 
        "name": user_db.name, 
        "role": "user"
    }
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    return Token(access_token=access, refresh_token=refresh)

@router.get("/protected", dependencies=[Depends(role_required(["admin"]))])
def protected(current_user=Depends(get_current_user)):
    return {"message": f"Welcome {current_user['sub']}! You have admin access."}