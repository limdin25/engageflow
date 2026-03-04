/**
 * DB proof: for each profile print id, email, cookie_json exists/non-empty/parses/count.
 * No cookie values; only names and counts.
 */
const path = require('path');
const Database = require('better-sqlite3');
const config = require('../config-loader');

const dbPath = config.ENGAGEFLOW_DB_PATH || path.resolve(__dirname, '../../../backend/engageflow.db');
const db = new Database(dbPath, { readonly: true });

const columns = db.prepare("PRAGMA table_info(profiles)").all().map(r => r.name);
if (!columns.includes('cookie_json')) {
  console.log('profiles table has no cookie_json column (schema may be older). Columns:', columns.join(', '));
  db.close();
  process.exit(0);
}
const rows = db.prepare('SELECT id, email, cookie_json FROM profiles').all();
console.log('profiles count:', rows.length);
for (const p of rows) {
  const has = p.cookie_json != null;
  const nonEmpty = has && String(p.cookie_json).trim().length > 0;
  let parses = false;
  let count = 0;
  let firstTwoNames = [];
  if (nonEmpty) {
    try {
      const parsed = JSON.parse(p.cookie_json);
      const list = Array.isArray(parsed) ? parsed : (parsed && parsed.cookies) || [];
      count = list.length;
      firstTwoNames = list.slice(0, 2).map(c => (c && c.name) || '(no name)');
      parses = true;
    } catch (_) {
      parses = false;
    }
  }
  console.log(JSON.stringify({
    id: p.id,
    email: (p.email || '').slice(0, 30),
    cookie_json_exists: has,
    cookie_json_non_empty: nonEmpty,
    cookie_json_parses: parses,
    cookie_count: count,
    first_2_names: firstTwoNames,
  }));
}
db.close();
