from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import os, hashlib, secrets
from app.db import execute

router = APIRouter()

# ── Token store (in-memory, resets on deploy — aceitável para opção A) ──
# { token: {user_id, username, role} }
_sessions: dict = {}

# ── Helpers ──────────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def _make_token(username: str) -> str:
    return secrets.token_hex(32)

def _get_session(authorization: str = "") -> dict:
    token = authorization.replace("Bearer ", "").strip()
    session = _sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return session

def _require_admin(authorization: str = ""):
    s = _get_session(authorization)
    if s["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return s

# ── Ensure table exists on first use ─────────────────────────────────────

def _ensure_table():
    execute("""
        CREATE TABLE IF NOT EXISTS pcp_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(64) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            role VARCHAR(16) NOT NULL DEFAULT 'viewer',
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """, fetch=False)
    # Seed admin from env if table is empty
    count = execute("SELECT COUNT(*) as n FROM pcp_users")
    if count and count[0]["n"] == 0:
        admin_user = os.environ.get("ADMIN_USER", "carlos")
        admin_pass = os.environ.get("ADMIN_PASS", "alliage2025")
        execute(
            "INSERT INTO pcp_users (username, password_hash, role, status) VALUES (%s, %s, 'admin', 'active')",
            (admin_user, _hash(admin_pass)),
            fetch=False
        )

try:
    _ensure_table()
except Exception as e:
    print(f"[auth] table init error: {e}")

# ── Models ───────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = "viewer"
    status: Optional[str] = "pending"

class PatchUserRequest(BaseModel):
    status: Optional[str] = None   # 'active' | 'pending' | 'blocked'
    role: Optional[str] = None     # 'admin' | 'viewer'

# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("/login")
async def login(req: LoginRequest):
    rows = execute(
        "SELECT id, username, role, status FROM pcp_users WHERE username = %s AND password_hash = %s",
        (req.username.strip().lower(), _hash(req.password))
    )
    if not rows:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    user = rows[0]
    if user["status"] == "pending":
        raise HTTPException(status_code=403, detail="Conta aguardando aprovação do administrador")
    if user["status"] == "blocked":
        raise HTTPException(status_code=403, detail="Conta bloqueada. Entre em contato com o administrador")
    token = _make_token(user["username"])
    _sessions[token] = {"user_id": user["id"], "username": user["username"], "role": user["role"]}
    return {"token": token, "username": user["username"], "role": user["role"]}


@router.post("/register")
async def register(req: RegisterRequest, authorization: str = Header("")):
    username = req.username.strip().lower()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Usuário deve ter ao menos 3 caracteres")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Senha deve ter ao menos 4 caracteres")
    # If caller is admin, allow setting role/status directly
    token = authorization.replace("Bearer ", "").strip()
    caller = _sessions.get(token)
    role = req.role if (caller and caller["role"] == "admin") else "viewer"
    status = req.status if (caller and caller["role"] == "admin") else "pending"
    try:
        execute(
            "INSERT INTO pcp_users (username, password_hash, role, status) VALUES (%s, %s, %s, %s)",
            (username, _hash(req.password), role, status),
            fetch=False
        )
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Usuário já existe")
        raise HTTPException(status_code=500, detail=str(e))
    return {"detail": "ok"}


@router.post("/logout")
async def logout(authorization: str = Header("")):
    token = authorization.replace("Bearer ", "").strip()
    _sessions.pop(token, None)
    return {"detail": "ok"}


@router.get("/me")
async def me(authorization: str = Header("")):
    return _get_session(authorization)


@router.get("/users")
async def list_users(authorization: str = Header("")):
    _require_admin(authorization)
    rows = execute(
        "SELECT id, username, role, status, created_at FROM pcp_users ORDER BY created_at DESC"
    )
    return rows


@router.patch("/users/{user_id}")
async def patch_user(user_id: int, body: PatchUserRequest, authorization: str = Header("")):
    _require_admin(authorization)
    if body.status and body.status not in ("active", "pending", "blocked"):
        raise HTTPException(status_code=400, detail="Status inválido")
    if body.role and body.role not in ("admin", "viewer"):
        raise HTTPException(status_code=400, detail="Role inválido")
    sets, params = [], []
    if body.status:
        sets.append("status = %s"); params.append(body.status)
    if body.role:
        sets.append("role = %s"); params.append(body.role)
    if not sets:
        raise HTTPException(status_code=400, detail="Nada para atualizar")
    params.append(user_id)
    execute(f"UPDATE pcp_users SET {', '.join(sets)} WHERE id = %s", params, fetch=False)
    return {"detail": "ok"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, authorization: str = Header("")):
    _require_admin(authorization)
    execute("DELETE FROM pcp_users WHERE id = %s", (user_id,), fetch=False)
    return {"detail": "ok"}
