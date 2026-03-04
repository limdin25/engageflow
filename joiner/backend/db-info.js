/**
 * DB identification and schema hash for /internal/joiner/debug/db-info.
 * No secrets, no full URLs. Tables and columns only for schema hash.
 */
const path = require('path');
const crypto = require('crypto');

const DB_KIND_SQLITE = 'sqlite';

/**
 * Get schema description (tables and columns only) and a short hash.
 * @param {import('better-sqlite3').Database} db
 * @returns {{ schema_hash: string, tables: Record<string, string[]> }}
 */
function getSchemaInfo(db) {
  const tables = db.prepare(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
  ).all().map(r => r.name);
  const out = {};
  let str = '';
  for (const t of tables) {
    const cols = db.prepare(`PRAGMA table_info(${t})`).all().map(r => r.name);
    out[t] = cols;
    str += `${t}:${cols.join(',')};`;
  }
  const schema_hash = crypto.createHash('sha256').update(str).digest('hex').slice(0, 16);
  return { schema_hash, tables: out };
}

/**
 * Build db-info payload for EngageFlow DB (profiles source of truth).
 * @param {object} opts
 * @param {string} opts.engageflowPath - ENGAGEFLOW_DB_PATH
 * @param {import('better-sqlite3').Database} opts.engageflowDb
 */
function buildDbInfo({ engageflowPath, engageflowDb }) {
  const db_kind = DB_KIND_SQLITE;
  const resolved = path.isAbsolute(engageflowPath) ? engageflowPath : path.resolve(engageflowPath);
  const db_path_basename = path.basename(resolved);
  const { schema_hash, tables } = getSchemaInfo(engageflowDb);
  const profilesColumns = tables.profiles || [];
  const has_cookie_json = profilesColumns.includes('cookie_json');
  return {
    db_kind,
    db_path: db_path_basename,
    resolved_path: resolved,
    schema_hash,
    tables: Object.keys(tables),
    profiles_columns: profilesColumns,
    profiles_has_cookie_json: has_cookie_json,
  };
}

module.exports = { getSchemaInfo, buildDbInfo, DB_KIND_SQLITE };
