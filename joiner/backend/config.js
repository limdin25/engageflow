const path = require('path');

// Allow Docker/Coolify to override paths via env (defaults for local/Contabo)
const defaultEngageflowDb = path.resolve(__dirname, '../../backend/engageflow.db');
const defaultJoinerDb = path.resolve(__dirname, 'joiner.db');

module.exports = {
    // EngageFlow DB — READ ONLY for profiles + READ/WRITE for browser_locks
    ENGAGEFLOW_DB_PATH: process.env.ENGAGEFLOW_DB_PATH || defaultEngageflowDb,

    // Joiner's own DB — join_queue, discovery, logs
    JOINER_DB_PATH: process.env.JOINER_DB_PATH || defaultJoinerDb,

    // Shared browser profiles
    BROWSER_PROFILES_DIR: process.env.BROWSER_PROFILES_DIR || path.resolve(__dirname, '../../backend/skool_accounts'),

    // EngageFlow API for webhook (Docker: backend:8000)
    ENGAGEFLOW_API: process.env.ENGAGEFLOW_API || 'http://127.0.0.1:3103',
};
