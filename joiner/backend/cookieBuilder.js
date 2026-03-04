/**
 * Build Cookie header from cookie_json. Handles array or object shapes.
 * Never logs cookie values; only names and counts.
 * Returns deterministic error codes: NO_COOKIE_JSON, EMPTY_COOKIE_LIST.
 */

const ERROR_CODES = {
  NO_COOKIE_JSON: 'NO_COOKIE_JSON',
  EMPTY_COOKIE_LIST: 'EMPTY_COOKIE_LIST',
};

/**
 * Normalize cookie_json to an array of { name, value }.
 * @param {string|object} cookieJson - JSON string or parsed object
 * @returns {{ cookies: Array<{name:string,value:string}>, error?: string, code?: string }}
 */
function parseCookieJson(cookieJson) {
  if (cookieJson == null || (typeof cookieJson === 'string' && cookieJson.trim() === '')) {
    return { error: 'Missing or empty cookie_json', code: ERROR_CODES.NO_COOKIE_JSON };
  }
  let parsed;
  if (typeof cookieJson === 'string') {
    try {
      parsed = JSON.parse(cookieJson);
    } catch (e) {
      return { error: 'Invalid JSON', code: ERROR_CODES.NO_COOKIE_JSON };
    }
  } else {
    parsed = cookieJson;
  }
  let list = Array.isArray(parsed) ? parsed : null;
  if (!list && parsed && Array.isArray(parsed.cookies)) list = parsed.cookies;
  if (!list || list.length === 0) {
    return { error: 'No cookies in list', code: ERROR_CODES.EMPTY_COOKIE_LIST };
  }
  const cookies = [];
  for (const c of list) {
    const name = c && (c.name != null ? String(c.name) : c.key);
    const value = c && (c.value != null ? String(c.value) : c.val);
    if (name != null && name !== '' && value != null) {
      cookies.push({ name, value });
    }
  }
  if (cookies.length === 0) {
    return { error: 'No valid name/value cookies', code: ERROR_CODES.EMPTY_COOKIE_LIST };
  }
  return { cookies };
}

/**
 * Build Cookie header string and metadata. Logs counts and first 2 names only (no values).
 * @param {string|object} cookieJson
 * @param {{ profileId?: string, email?: string, context?: string }} meta - for debug log only
 * @returns {{ header: string, count: number, cookieNames: string[], error?: string, code?: string }}
 */
function buildCookieHeader(cookieJson, meta = {}) {
  const rawLen = typeof cookieJson === 'string' ? cookieJson.length : (cookieJson ? JSON.stringify(cookieJson).length : 0);
  const parsed = parseCookieJson(cookieJson);
  if (parsed.error) {
    if (meta.profileId != null || meta.email != null) {
      console.warn('[cookieBuilder]', meta.profileId || '', meta.email || '', parsed.code || parsed.error, 'cookie_json_len:', rawLen);
    }
    return { header: '', count: 0, cookieNames: [], error: parsed.error, code: parsed.code };
  }
  const { cookies } = parsed;
  const header = cookies.map(c => `${c.name}=${c.value}`).join('; ');
  const cookieNames = cookies.map(c => c.name);
  const firstTwo = cookieNames.slice(0, 2);
  console.log('[cookieBuilder] cookie_json_len:', rawLen, 'cookie_count:', cookies.length, 'first_2_names:', firstTwo.join(', '));
  return { header, count: cookies.length, cookieNames, error: undefined, code: undefined };
}

module.exports = { buildCookieHeader, parseCookieJson, ERROR_CODES };
