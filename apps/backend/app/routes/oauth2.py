from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from jose import jwt

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

users= {
    "pablo": {"username":"pablo", "email":"pablo@gmail.com", "password":"fakepass"},
    "user2": {"username":"user2", "email":"user2@gmail.com", "password":"user2"}
}

def encode_token(payload: dict) -> str:
    token = jwt.encode(payload, "my-secret", algorithm="HS256")
    return token

def decode_token(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    data = jwt.decode(token, "my-secret", algorithms=["HS256"])
    user = users.get(data["username"])
    return user

@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = users.get(form_data.username)
    if not user or form_data.password != user["password"]:
        raise HTTPException(status_code = 400, detail="Incorrect username or password")
    token = encode_token({"username": user["username"], "email":user["email"]})
    
    return {"access_token": token}

@router.get("/user/profile")
async def profile(user: Annotated[dict, Depends(decode_token)]):
    return user