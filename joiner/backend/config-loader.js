/**
 * Config loader — Railway vs VPS.
 * When RAILWAY=true, use config.railway.js (env-based).
 * Otherwise use config.js (VPS, unchanged behavior).
 */
if (process.env.RAILWAY === 'true') {
  module.exports = require('./config.railway');
} else {
  module.exports = require('./config');
}
