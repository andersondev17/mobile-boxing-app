from fastapi import APIRouter, Depends
from app.auth.dependencies import role_required

router = APIRouter(prefix="/user", tags=["Users"])

@router.get("/me")
def get_me(user=Depends(role_required(["admin", "trainer", "user"]))):
    return {"message": f"Hola {user['sub']}", "role": user["role"]}

@router.get("/admin-only")
def admin_dashboard(user=Depends(role_required(["admin"]))):
    return {"message": f"Bienvenido administrador {user['sub']}"}
