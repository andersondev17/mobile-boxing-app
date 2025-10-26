from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import engine, get_db
from models import Base
from routes import user_route

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(user_route)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

@app.get("/")
async def root():
    return {"message":"Welcome to fastAPI"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)