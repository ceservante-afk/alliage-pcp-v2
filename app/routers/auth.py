from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, hashlib, hmac

router = APIRouter()

USERS = {
    "pcp_admin": os.environ.get("ADMIN_PASS_HASH", ""),
}

class LoginRequest(BaseModel):
    username: str
    password: str

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

@router.post("/login")
async def login(req: LoginRequest):
    stored = USERS.get(req.username)
    if not stored or stored != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return {"token": hash_password(req.username + req.password + "alliage_pcp_2025")}
