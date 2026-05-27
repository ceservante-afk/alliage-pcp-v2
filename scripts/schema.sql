-- ═══════════════════════════════════════════════════════════
-- ALLIAGE PCP — Supabase Schema
-- Run this in Supabase SQL Editor
-- ═══════════════════════════════════════════════════════════

-- ── BOM nodes ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bom_nodes (
    id          SERIAL PRIMARY KEY,
    mat         VARCHAR(30) NOT NULL,
    desc        TEXT,
    tipo        VARCHAR(10),
    qty         NUMERIC(12,4),
    umd         VARCHAR(10),
    parent_mat  VARCHAR(30),
    pa_root     VARCHAR(30) NOT NULL,
    depth       INTEGER NOT NULL,
    CONSTRAINT uq_bom_node UNIQUE (pa_root, mat, parent_mat, depth)
);

CREATE INDEX IF NOT EXISTS idx_bom_pa_root  ON bom_nodes(pa_root);
CREATE INDEX IF NOT EXISTS idx_bom_mat      ON bom_nodes(mat);
CREATE INDEX IF NOT EXISTS idx_bom_depth    ON bom_nodes(depth);

-- ── Roteiro operations ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roteiro_ops (
    id          SERIAL PRIMARY KEY,
    mat         VARCHAR(30) NOT NULL,
    ct          VARCHAR(20) NOT NULL,
    op_num      VARCHAR(10),
    op_desc     TEXT,
    setup       NUMERIC(10,4) DEFAULT 0,
    indir       NUMERIC(10,4) DEFAULT 0,
    mod         NUMERIC(10,4) DEFAULT 0,
    qty_base    NUMERIC(10,4) DEFAULT 1,
    CONSTRAINT uq_rot_op UNIQUE (mat, ct, op_num)
);

CREATE INDEX IF NOT EXISTS idx_rot_mat ON roteiro_ops(mat);
CREATE INDEX IF NOT EXISTS idx_rot_ct  ON roteiro_ops(ct);

-- ── CT names ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ct_names (
    ct      VARCHAR(20) PRIMARY KEY,
    name    TEXT
);

-- ── PA to Linha mapping ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS pa_linha (
    pa      VARCHAR(30) PRIMARY KEY,
    linha   TEXT
);

-- ── CT settings (capacity params per user/session) ───────────
CREATE TABLE IF NOT EXISTS ct_settings (
    ct      VARCHAR(20) PRIMARY KEY,
    turnos  INTEGER DEFAULT 1,
    hturno  NUMERIC(4,1) DEFAULT 8,
    dias    INTEGER DEFAULT 5,
    efic    NUMERIC(5,2) DEFAULT 85
);
