/**
 * Railway-only configuration.
 * Used when RAILWAY=true. All values from environment variables.
 */
const path = require('path');

module.exports = {
  ENGAGEFLOW_DB_PATH: process.env.ENGAGEFLOW_DB_PATH || '/data/engageflow.db',
  JOINER_DB_PATH: process.env.JOINER_DB_PATH || '/data/joiner.db',
  BROWSER_PROFILES_DIR: process.env.BROWSER_PROFILES_DIR || '/data/skool_accounts',
  ENGAGEFLOW_API: process.env.ENGAGEFLOW_API_URL || 'http://127.0.0.1:3103',
  ENGAGEFLOW_INTERNAL_URL: (process.env.ENGAGEFLOW_INTERNAL_URL || process.env.ENGAGEFLOW_API_URL || '').replace(/\/$/, ''),
  ENGAGEFLOW_JOINER_SECRET: (process.env.ENGAGEFLOW_JOINER_SECRET || '').trim(),
};
