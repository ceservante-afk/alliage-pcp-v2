from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Alliage PCP", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────
from app.routers import bom, roteiro, calc, auth

app.include_router(auth.router,    prefix="/api/auth",    tags=["auth"])
app.include_router(bom.router,     prefix="/api/bom",     tags=["bom"])
app.include_router(roteiro.router, prefix="/api/roteiro", tags=["roteiro"])
app.include_router(calc.router,    prefix="/api/calc",    tags=["calc"])

# ── Frontend ──────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}
