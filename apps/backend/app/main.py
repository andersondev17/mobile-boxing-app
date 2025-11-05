from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import engine, Base, seed_roles, get_db
from routes import user_router, training_router, auth_router
from auth import google_router

#Base.metadata.drop_all(bind=engine)  # elimina todas las tablas
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(user_router)
app.include_router(training_router)
app.include_router(auth_router)
app.include_router(google_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

@app.on_event("startup")
def on_startup():
    db = next(get_db())
    seed_roles(db)

@app.get("/")
async def root():
    return {"message":"Welcome to fastAPI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)