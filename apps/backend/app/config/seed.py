from fastapi import Depends
from sqlalchemy.orm import Session
from config import get_db
from models import Role
from typing import Annotated
from sqlalchemy.exc import SQLAlchemyError

db_dependency = Annotated[Session, Depends(get_db)]

def seed_roles(db: db_dependency):
    base_roles = [
        {"id": "admin", "name": "Administrador"},
        {"id": "trainer", "name": "Entrenador"},
        {"id": "user", "name": "Usuario estándar"},
    ]

    try:
        for role_data in base_roles:
            role = db.query(Role).filter_by(id=role_data["id"]).first()
            if not role:
                db.add(Role(**role_data))
        db.commit()
    except SQLAlchemyError as e:
        print(f"[ERROR] Database error seeding roles: {e}")
        db.rollback()


