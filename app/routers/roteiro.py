from fastapi import APIRouter
from app.db import execute
from app.cache import get_cti, get_ct_names

router = APIRouter()

@router.get("/ct/{ct}")
async def get_by_ct(ct: str):
    rows = execute("""
        SELECT mat, ct, op_num, op_desc, indir, qty_base
        FROM roteiro_ops WHERE ct = %s ORDER BY mat, op_num
    """, (ct,))
    return rows

@router.get("/mat/{mat}")
async def get_by_mat(mat: str):
    rows = execute("""
        SELECT mat, ct, op_num, op_desc, indir, qty_base
        FROM roteiro_ops WHERE mat = %s ORDER BY op_num
    """, (mat,))
    return rows

@router.get("/cts")
async def get_cts():
    rows = execute("""
        SELECT ct, COUNT(DISTINCT mat) as mat_count
        FROM roteiro_ops GROUP BY ct ORDER BY ct
    """)
    return rows

@router.get("/ct_names")
async def get_ct_names_endpoint():
    """Return CT code -> name mapping (cached)."""
    return get_ct_names()

@router.get("/cti")
async def get_cti_endpoint():
    """Return CT index (cached on startup)."""
    return get_cti()
