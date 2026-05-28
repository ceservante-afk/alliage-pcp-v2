"""
In-memory cache for expensive DB queries.
Loaded once on startup, refreshed on demand.
"""
from app.db import execute
from collections import defaultdict

_cache = {}

def get_cti():
    if 'cti' not in _cache:
        refresh_cti()
    return _cache['cti']

def get_ct_names():
    if 'ct_names' not in _cache:
        refresh_ct_names()
    return _cache['ct_names']

def get_pa_linha():
    if 'pa_linha' not in _cache:
        refresh_pa_linha()
    return _cache['pa_linha']

def refresh_cti():
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
            'mat': r['mat'], 'op': r['op'],
            'desc_op': r['desc_op'],
            'indir': float(r['indir'] or 0),
            'qty_base': float(r['qty_base'] or 1)
        })
    _cache['cti'] = dict(cti)

def refresh_ct_names():
    rows = execute("SELECT ct, nome FROM ct_names ORDER BY ct")
    _cache['ct_names'] = {r['ct']: r['nome'] for r in rows}

def refresh_pa_linha():
    rows = execute("SELECT pa, linha FROM pa_linha")
    _cache['pa_linha'] = {r['pa']: r['linha'] for r in rows}

def preload_all():
    """Call on startup to warm up cache."""
    refresh_ct_names()
    refresh_pa_linha()
    refresh_cti()
    print(f"Cache loaded: {len(_cache['cti'])} CTs, {len(_cache['ct_names'])} CT names")
