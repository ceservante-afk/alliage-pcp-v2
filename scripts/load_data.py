"""
Populate Supabase from local JSON files.
Run once after creating the schema.

Usage:
    pip install psycopg2-binary
    DATABASE_URL="postgresql://..." python scripts/load_data.py
"""
import json, os, sys
from itertools import islice
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.environ["DATABASE_URL"]

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# ── Load BOM ─────────────────────────────────────────────────────────
def load_bom(conn, bom_path="bom_compact.json"):
    print("Loading BOM...")
    with open(bom_path, encoding="utf-8") as f:
        bom = json.load(f)

    rows = []
    def traverse(node, pa_root, parent_mat, depth):
        mat   = node[0]
        desc  = node[1]
        tipo  = node[2]
        qty   = float(node[3]) if node[3] else 1.0
        umd   = node[4]
        rows.append((mat, desc, tipo, qty, umd, parent_mat, pa_root, depth))
        for child in node[5]:
            traverse(child, pa_root, mat, depth + 1)

    for pa in bom:
        traverse(pa, pa[0], None, 1)

    print(f"  {len(rows)} BOM nodes to insert...")

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE bom_nodes RESTART IDENTITY CASCADE")
        for chunk in chunks(rows, 1000):
            execute_values(cur, """
                INSERT INTO bom_nodes (mat, desc, tipo, qty, umd, parent_mat, pa_root, depth)
                VALUES %s
                ON CONFLICT ON CONSTRAINT uq_bom_node DO NOTHING
            """, chunk)
    conn.commit()
    print(f"  BOM loaded: {len(rows)} rows")

# ── Load Roteiro ──────────────────────────────────────────────────────
def load_roteiro(conn, rot_path="roteiro_compact.json"):
    print("Loading Roteiro...")
    with open(rot_path, encoding="utf-8") as f:
        rot = json.load(f)

    rows = []
    for mat, ops in rot.items():
        for op in ops:
            # op = [ct, op_num, op_desc, setup, indir, mod, qty_base]
            rows.append((mat, op[0], op[1], op[2], op[3], op[4], op[5], op[6]))

    print(f"  {len(rows)} roteiro ops to insert...")

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE roteiro_ops RESTART IDENTITY CASCADE")
        for chunk in chunks(rows, 1000):
            execute_values(cur, """
                INSERT INTO roteiro_ops (mat, ct, op_num, op_desc, setup, indir, mod, qty_base)
                VALUES %s
                ON CONFLICT ON CONSTRAINT uq_rot_op DO NOTHING
            """, chunk)
    conn.commit()
    print(f"  Roteiro loaded: {len(rows)} rows")

# ── Load CT Names ─────────────────────────────────────────────────────
def load_ct_names(conn, ct_path="ct_names.json"):
    if not os.path.exists(ct_path):
        print("  ct_names.json not found, skipping")
        return
    print("Loading CT names...")
    with open(ct_path, encoding="utf-8") as f:
        ct_names = json.load(f)
    rows = [(ct, name) for ct, name in ct_names.items()]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ct_names")
        execute_values(cur, """
            INSERT INTO ct_names (ct, name) VALUES %s
            ON CONFLICT (ct) DO UPDATE SET name = EXCLUDED.name
        """, rows)
    conn.commit()
    print(f"  CT names loaded: {len(rows)}")

# ── Load PA→Linha ─────────────────────────────────────────────────────
def load_pa_linha(conn, path="pa_linha.json"):
    if not os.path.exists(path):
        print("  pa_linha.json not found, skipping")
        return
    print("Loading PA→Linha...")
    with open(path, encoding="utf-8") as f:
        mapping = json.load(f)
    rows = [(pa, linha) for pa, linha in mapping.items()]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE pa_linha")
        execute_values(cur, """
            INSERT INTO pa_linha (pa, linha) VALUES %s
            ON CONFLICT (pa) DO UPDATE SET linha = EXCLUDED.linha
        """, rows)
    conn.commit()
    print(f"  PA→Linha loaded: {len(rows)}")

if __name__ == "__main__":
    print(f"Connecting to database...")
    conn = get_conn()
    try:
        load_bom(conn)
        load_roteiro(conn)
        load_ct_names(conn)
        load_pa_linha(conn)
        print("\n✓ All data loaded successfully")
    finally:
        conn.close()
