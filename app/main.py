from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Alliage PCP", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import bom, roteiro, calc, auth

app.include_router(auth.router,    prefix="/api/auth",    tags=["auth"])
app.include_router(bom.router,     prefix="/api/bom",     tags=["bom"])
app.include_router(roteiro.router, prefix="/api/roteiro", tags=["roteiro"])
app.include_router(calc.router,    prefix="/api/calc",    tags=["calc"])

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    return FileResponse(frontend_path)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "trace": traceback.format_exc()[-500:]}
    )
