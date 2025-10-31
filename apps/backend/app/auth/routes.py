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

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or form_data.password != "demo":  # Reemplaza con hash real
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    access = create_access_token({"sub": user.id, "role": user.role})
    refresh = create_refresh_token({"sub": user.id, "role": user.role})
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str):
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_access = create_access_token({"sub": payload["sub"], "role": payload["role"]})
    return {"access_token": new_access, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/login/google")
def login_with_google():
    auth_url = (
        f"{settings.GOOGLE_AUTH_ENDPOINT}"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )
    return RedirectResponse(auth_url)

@router.get("/auth/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(settings.GOOGLE_TOKEN_ENDPOINT, data=data)
        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        user_resp = await client.get(
            settings.GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_resp.json()

    user = GoogleUser(**user_info)

    # Aquí puedes crear el usuario en DB si no existe
    payload = {"sub": user.email, "name": user.name, "role": "user"}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)

    return Token(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str):
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = create_access_token({"sub": payload["sub"], "role": payload.get("role")})
    new_refresh = create_refresh_token({"sub": payload["sub"], "role": payload.get("role")})
    return Token(access_token=new_access, refresh_token=new_refresh)

@router.get("/protected", dependencies=[Depends(role_required(["admin"]))])
def protected(current_user=Depends(get_current_user)):
    return {"message": f"Welcome {current_user['sub']}! You have admin access."}