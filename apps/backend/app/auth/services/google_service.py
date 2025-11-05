# auth/services/google_service.py
from models import User, Role, AuthCode
from auth import create_token
from datetime import datetime, timedelta
import uuid

def get_or_create_google_user(db, google_user):
    role = db.query(Role).filter(Role.name=="user").one_or_none()
    user_db = db.query(User).filter(User.email==google_user.email).first()
    if not user_db:
        user_db = User(
            email=google_user.email,
            name=google_user.name,
            role=role.id if role else None,
            email_verified=True
        )
        db.add(user_db)
        db.commit()
        db.refresh(user_db)
    return user_db

def create_auth_code(db, user):
    auth_code = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=2)
    db.add(AuthCode(code=auth_code, user_email=user.email, expires_at=expires_at))
    db.commit()
    return auth_code
