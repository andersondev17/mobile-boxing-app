"""
Authentication routes: local login, registration, Google OAuth,
and token exchange endpoints.
"""

from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse

from models.postgres import User
from models.model import AuthCode
from app.config.database import get_pg_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import Token, GoogleUser, settings, UserCreate, UserBase
from app.auth import (
    get_current_user,
    get_google_user_info,
    get_google_user_info_pkce,
    create_token,
    verify_token,
)
from services.auth.auth_service import login_user, refresh_user_token, register_user
from services.auth.google_service import get_or_create_google_user, create_auth_code

router = APIRouter(prefix="/auth", tags=["Auth"])


# ─── Local Login ─────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_pg_session)):
    """Authenticate with email/password and receive JWT tokens."""
    tokens = await login_user(form_data.username, form_data.password, db)
    if not tokens:
        raise HTTPException(400, "Invalid credentials")
    return tokens


@router.post("/refresh", response_model=Token)
def refresh_endpoint(refresh_token: str = Body(..., embed=True)):
    """Refresh an expired access token."""
    payload = verify_token(refresh_token, token_type="refresh")
    return refresh_user_token(payload)


@router.post("/register", response_model=UserBase)
async def register(user: UserCreate, db: AsyncSession = Depends(get_pg_session)):
    """Register a new user with email/password."""
    new_user = await register_user(user, db)
    if not new_user:
        raise HTTPException(400, "Email already registered")
    return UserBase(
        id=str(new_user.id),
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        email_verified=new_user.email_verified,
        created_at=new_user.created_at,
    )


# ─── Google OAuth ────────────────────────────────────────────

@router.get("/login/google")
def login_with_google(
    client_type: str = "web",
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    state: str | None = None,
):
    """Initiate Google OAuth flow.

    Args:
        client_type: "web" or "ios"
        code_challenge: PKCE challenge (required for mobile)
        code_challenge_method: Should be "S256"
        state: CSRF protection token
    """
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
        "include_granted_scopes": "true",
    }

    if code_challenge and code_challenge_method:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = code_challenge_method

    if state:
        params["state"] = state

    return RedirectResponse(f"{settings.GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}")


@router.get("/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_pg_session)):
    """Handle Google OAuth callback and redirect to mobile app."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    user_info = await get_google_user_info(code)
    google_user = GoogleUser(**user_info)

    user = await get_or_create_google_user(google_user, db)
    auth_code = await create_auth_code(user)

    return RedirectResponse(
        f"{settings.MOBILE_DEEP_LINK_SCHEME}oauth-callback?auth_code={auth_code}"
        + (f"&state={state}" if state else "")
    )


# ─── Exchange Code ───────────────────────────────────────────

@router.post("/exchange-token")
async def exchange_token(auth_code: str = Body(..., embed=True), db: AsyncSession = Depends(get_pg_session)):
    """Exchange a temporary auth code for JWT tokens."""
    record = await AuthCode.find_one({"code": auth_code})

    if not record or record.expires_at < datetime.now(timezone.utc):
        if record:
            await record.delete()
        raise HTTPException(400, "Invalid or expired auth code")

    result = await db.execute(select(User).where(User.email == record.user_email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(404, "User not found")

    payload = {"sub": str(user.id), "email": user.email, "name": user.name, "role": "user"}
    access = create_token(payload)
    refresh = create_token(payload, "refresh")

    await record.delete()

    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/mobile/token")
async def mobile_token_exchange(
    code: str = Body(...),
    code_verifier: str = Body(...),
    db: AsyncSession = Depends(get_pg_session)
):
    """Exchange a Google authorization code + PKCE verifier for JWT tokens."""
    user_info = await get_google_user_info_pkce(code, code_verifier)
    google_user = GoogleUser(**user_info)
    user = await get_or_create_google_user(google_user, db)

    payload = {"sub": str(user.id), "email": user.email, "name": user.name, "role": "user"}
    access = create_token(payload)
    refresh = create_token(payload, "refresh")

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name,
            "role": "user",
        },
    }


# ─── Protected Route ────────────────────────────────────────

@router.get("/protected")
def protected(current_user=Depends(get_current_user)):
    """Test endpoint requiring authentication."""
    return {"message": f"Welcome {current_user.get('email', 'User')}"}





