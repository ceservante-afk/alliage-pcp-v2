from fastapi import APIRouter
from app.db import execute

router = APIRouter()

@router.get("/ct/{ct}")
async def get_by_ct(ct: str):
    """Return all operations for a given CT."""
    rows = execute("""
        SELECT mat, ct, op_num, op_desc, indir, qty_base
        FROM roteiro_ops
        WHERE ct = %s
        ORDER BY mat, op_num
    """, (ct,))
    return [dict(r) for r in rows]

@router.get("/mat/{mat}")
async def get_by_mat(mat: str):
    """Return all operations for a given material."""
    rows = execute("""
        SELECT mat, ct, op_num, op_desc, indir, qty_base
        FROM roteiro_ops
        WHERE mat = %s
        ORDER BY op_num
    """, (mat,))
    return [dict(r) for r in rows]

@router.get("/cts")
async def get_cts():
    """Return all unique CTs with operation count."""
    rows = execute("""
        SELECT ct, COUNT(DISTINCT mat) as mat_count
        FROM roteiro_ops
        GROUP BY ct
        ORDER BY ct
    """)
    return [dict(r) for r in rows]
