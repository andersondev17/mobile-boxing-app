import httpx
from fastapi import HTTPException
from schemas import settings

async def get_google_user_info(code: str):
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(settings.GOOGLE_TOKEN_ENDPOINT, data=data)
        if token_resp.status_code != 200:
            raise HTTPException(status_code=token_resp.status_code, detail=token_resp.text)
        
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token")

        user_resp = await client.get(
            settings.GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_resp.status_code != 200:
            raise HTTPException(status_code=user_resp.status_code, detail="Failed to fetch user info")
        
        return user_resp.json()
