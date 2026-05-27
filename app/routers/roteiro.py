from fastapi import APIRouter
from app.db import execute
from collections import defaultdict

router = APIRouter()

@router.get("/ct/{ct}")
async def get_by_ct(ct: str):
    rows = execute("""
        SELECT mat, ct, op_num, op_desc, indir, qty_base
        FROM roteiro_ops
        WHERE ct = %s
        ORDER BY mat, op_num
    """, (ct,))
    return rows

@router.get("/mat/{mat}")
async def get_by_mat(mat: str):
    rows = execute("""
        SELECT mat, ct, op_num, op_desc, indir, qty_base
        FROM roteiro_ops
        WHERE mat = %s
        ORDER BY op_num
    """, (mat,))
    return rows

@router.get("/cts")
async def get_cts():
    rows = execute("""
        SELECT ct, COUNT(DISTINCT mat) as mat_count
        FROM roteiro_ops
        GROUP BY ct
        ORDER BY ct
    """)
    return rows

@router.get("/ct_names")
async def get_ct_names():
    """Return CT code -> name mapping."""
    rows = execute("SELECT ct, nome FROM ct_names ORDER BY ct")
    return {r['ct']: r['nome'] for r in rows}

@router.get("/cti")
async def get_cti():
    """Return CT index: {ct: [{mat, op, desc_op, indir, qty_base}]}"""
    rows = execute("""
        SELECT ct, mat, op_num as op, op_desc as desc_op, 
               CAST(indir AS FLOAT) as indir, 
               CAST(qty_base AS FLOAT) as qty_base
        FROM roteiro_ops
        ORDER BY ct, mat, op_num
    """)
    cti = defaultdict(list)
    for r in rows:
        cti[r['ct']].append({
            'mat': r['mat'],
            'op': r['op'],
            'desc_op': r['desc_op'],
            'indir': float(r['indir'] or 0),
            'qty_base': float(r['qty_base'] or 1)
        })
    return dict(cti)
