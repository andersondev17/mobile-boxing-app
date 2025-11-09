import httpx
from fastapi import HTTPException
from schemas import settings

async def _exchange_google_code(token_data: dict) -> str:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(settings.GOOGLE_TOKEN_ENDPOINT, data=token_data)
        if token_resp.status_code != 200:
            raise HTTPException(status_code=token_resp.status_code, detail=token_resp.text)
        
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        return access_token

async def _fetch_google_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            settings.GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_resp.status_code != 200:
            raise HTTPException(status_code=user_resp.status_code, detail="Failed to fetch user info")
        
        return user_resp.json()

async def get_google_user_info(code: str):
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    access_token = await _exchange_google_code(token_data)
    return await _fetch_google_user_info(access_token)

async def get_google_user_info_pkce(code: str, code_verifier: str):
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_IOS_CLIENT_ID,
        "code_verifier": code_verifier,
        "redirect_uri": settings.GOOGLE_IOS_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    access_token = await _exchange_google_code(token_data)
    return await _fetch_google_user_info(access_token)
