from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from schemas import settings

url = URL.create(
    drivername = settings.POSTGRES_DRIVER,
    username = settings.POSTGRES_USER,
    password = settings.POSTGRES_PASSWORD,
    host = settings.POSTGRES_HOST,
    port = settings.POSTGRES_PORT,
    database = settings.POSTGRES_DB
)

engine = create_engine(url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False,bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()