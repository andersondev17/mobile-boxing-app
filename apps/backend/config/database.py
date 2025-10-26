from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionMaker
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os

load_dotenv()

url = URL.create(
    drivername = os.getenv("POSTGRES_DRIVER"),
    username = os.getenv("POSTGRES_USER"),
    password = os.getenv("POSTGRES_PASSWORD"),
    host = os.getenv("POSTGRES_HOST"),
    port = os.getenv("POSTGRES_PORT"),
    database = os.getenv("POSTGRES_DB")
)

engine = create_engine(url)
SessionLocal = sessionMaker(autocommit=False, autoflush=False,bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()