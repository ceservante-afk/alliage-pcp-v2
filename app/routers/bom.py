from fastapi import APIRouter
from app.db import execute

router = APIRouter()

@router.get("/pas")
async def get_pas():
    """Return all PAs (root level nodes)."""
    rows = execute("""
        SELECT mat, descricao as desc, tipo
        FROM bom_nodes
        WHERE depth = 1
        ORDER BY descricao
    """)
    return [dict(r) for r in rows]

@router.get("/tree/{pa_mat}")
async def get_tree(pa_mat: str):
    """Return full BOM tree for a PA as nested JSON."""
    rows = execute("""
        SELECT mat, descricao as desc, tipo, qty, umd, parent_mat, depth
        FROM bom_nodes
        WHERE pa_root = %s
        ORDER BY depth, mat
    """, (pa_mat,))
    if not rows:
        return {}

    nodes = {r['mat']: {**dict(r), 'children': []} for r in rows}
    root = None
    for r in rows:
        if r['depth'] == 1:
            root = nodes[r['mat']]
        elif r['parent_mat'] and r['parent_mat'] in nodes:
            nodes[r['parent_mat']]['children'].append(nodes[r['mat']])
    return root or {}
