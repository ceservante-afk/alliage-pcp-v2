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
    """
    Given a list of PAs with quantities, explode BOM and calculate
    CT load using direct qty (not cascaded).
    Returns: {ct: {load_min, components: [{mat, desc, qty_total, indir_unit, mins}]}}
    """
    if not req.items:
        return {}

    pa_list = [item.pa for item in req.items]
    qty_map = {item.pa: item.qty for item in req.items}

    # Load BOM nodes for all requested PAs
    placeholders = ','.join(['%s'] * len(pa_list))
    bom_rows = execute(f"""
        SELECT mat, desc, tipo, qty, pa_root, parent_mat, depth
        FROM bom_nodes
        WHERE pa_root IN ({placeholders})
        ORDER BY pa_root, depth, mat
    """, pa_list)

    # Load roteiro for all materials in these BOMs
    mats = list({r['mat'] for r in bom_rows})
    if not mats:
        return {}

    mat_placeholders = ','.join(['%s'] * len(mats))
    rot_rows = execute(f"""
        SELECT mat, ct, op_num, op_desc, indir, qty_base
        FROM roteiro_ops
        WHERE mat IN ({mat_placeholders})
    """, mats)

    # Build roteiro lookup
    rot_map = defaultdict(list)
    for r in rot_rows:
        rot_map[r['mat']].append(dict(r))

    # Build parent lookup per PA
    # {pa_root: {mat: {parent_mat, qty}}}
    pa_nodes = defaultdict(dict)
    for r in bom_rows:
        pa_nodes[r['pa_root']][r['mat']] = {
            'parent': r['parent_mat'],
            'qty': float(r['qty']) if r['qty'] else 1.0,
            'desc': r['desc'],
            'depth': r['depth']
        }

    # Calculate CT load
    ct_map = defaultdict(float)
    ct_comp_map = defaultdict(lambda: defaultdict(lambda: {
        'mat': '', 'desc': '', 'qty_total': 0.0, 'indir_unit': 0.0, 'mins': 0.0
    }))

    for item in req.items:
        pa = item.pa
        qty_pa = item.qty
        nodes = pa_nodes.get(pa, {})

        for mat, node in nodes.items():
            if mat not in rot_map:
                continue
            # Direct qty = qty_pa * node['qty'] (no cascade)
            direct_qty = qty_pa * node['qty']
            desc = node['desc']

            for op in rot_map[mat]:
                ct = op['ct']
                indir_unit = op['indir'] / (op['qty_base'] or 1)
                mins = direct_qty * indir_unit
                ct_map[ct] += mins

                key = mat
                if ct_comp_map[ct][key]['mat'] == '':
                    ct_comp_map[ct][key] = {
                        'mat': mat,
                        'desc': desc,
                        'qty_total': direct_qty,
                        'indir_unit': indir_unit,
                        'mins': mins
                    }
                else:
                    ct_comp_map[ct][key]['qty_total'] += direct_qty
                    ct_comp_map[ct][key]['mins'] += mins

    # Format result
    result = {}
    for ct, load in ct_map.items():
        comps = sorted(ct_comp_map[ct].values(), key=lambda x: -x['mins'])
        result[ct] = {
            'load_min': round(load, 2),
            'components': [{
                'mat': c['mat'],
                'desc': c['desc'],
                'qty_total': round(c['qty_total'], 0),
                'indir_unit': round(c['indir_unit'], 4),
                'mins': round(c['mins'], 2)
            } for c in comps]
        }

    return result
