from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.db import execute
from collections import defaultdict

router = APIRouter()

class PAItem(BaseModel):
    pa: str
    qty: int

class ProgramRequest(BaseModel):
    items: List[PAItem]

@router.post("/explode")
async def explode_program(req: ProgramRequest):
    if not req.items:
        return {}

    pa_list = [item.pa for item in req.items]
    qty_map = {item.pa: item.qty for item in req.items}

    placeholders = ','.join(['%s'] * len(pa_list))
    bom_rows = execute(f"""
        SELECT mat, descricao as desc, tipo, qty, pa_root, parent_mat, depth
        FROM bom_nodes
        WHERE pa_root IN ({placeholders})
        ORDER BY pa_root, depth, mat
    """, pa_list)

    if not bom_rows:
        return {}

    mats = list({r['mat'] for r in bom_rows})
    mat_placeholders = ','.join(['%s'] * len(mats))
    rot_rows = execute(f"""
        SELECT mat, ct, op_num, op_desc, indir, qty_base
        FROM roteiro_ops
        WHERE mat IN ({mat_placeholders})
    """, mats)

    # Build roteiro lookup
    rot_map = defaultdict(list)
    for r in rot_rows:
        rot_map[r['mat']].append(r)

    # Build BOM node lookup per PA
    pa_nodes = defaultdict(dict)
    for r in bom_rows:
        pa_nodes[r['pa_root']][r['mat']] = {
            'qty': float(r['qty'] or 1),
            'desc': r['desc'] or '',
        }

    # Calculate CT load using direct qty (no cascade)
    ct_map = defaultdict(float)
    ct_comp = defaultdict(dict)

    for item in req.items:
        pa = item.pa
        qty_pa = item.qty
        nodes = pa_nodes.get(pa, {})

        for mat, node in nodes.items():
            if mat not in rot_map:
                continue
            direct_qty = float(qty_pa) * float(node['qty'])
            desc = node['desc']

            for op in rot_map[mat]:
                ct = op['ct']
                indir_unit = float(op['indir'] or 0) / float(op['qty_base'] or 1)
                mins = direct_qty * indir_unit
                ct_map[ct] += mins

                if mat not in ct_comp[ct]:
                    ct_comp[ct][mat] = {
                        'mat': mat, 'desc': desc,
                        'qty_total': direct_qty,
                        'indir_unit': indir_unit,
                        'mins': mins
                    }
                else:
                    ct_comp[ct][mat]['qty_total'] += direct_qty
                    ct_comp[ct][mat]['mins'] += mins

    result = {}
    for ct, load in ct_map.items():
        comps = sorted(ct_comp[ct].values(), key=lambda x: -x['mins'])
        result[ct] = {
            'load_min': round(load, 2),
            'components': [{
                'mat': c['mat'], 'desc': c['desc'],
                'qty_total': round(float(c['qty_total'])),
                'indir_unit': round(c['indir_unit'], 4),
                'mins': round(c['mins'], 2)
            } for c in comps]
        }

    return result
