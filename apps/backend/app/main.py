from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from config import engine, Base, seed_roles, get_db
from routes import (
    boxing_router,
    kafka_router,
    training_router,
    user_router,
)
from auth import auth_router
import logging
from pathlib import Path

from ml_service.baseline_builder import ensure_baseline

#Base.metadata.drop_all(bind=engine)  # elimina todas las tablas
Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.include_router(user_router)
app.include_router(training_router)
app.include_router(auth_router)
app.include_router(boxing_router)
app.include_router(kafka_router)

origins = [
    "http://localhost:5173", 
    "http://host.docker.internal:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    expose_headers=["*"]
)

@app.on_event("startup")
def on_startup():
    db = next(get_db())
    seed_roles(db)
    try:
        ensure_baseline()
    except Exception as exc:
        logging.warning("No se pudo generar baseline automaticamente: %s", exc)

@app.get("/")
async def root():
    return {"message":"Welcome to fastAPI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
