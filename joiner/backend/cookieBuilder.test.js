/**
 * Tests for cookieBuilder: non-empty Cookie header from valid cookie_json,
 * deterministic error codes for missing/invalid cookie_json.
 * No cookie values in assertions; only names and counts.
 */
const assert = require('assert');
const { buildCookieHeader, parseCookieJson, ERROR_CODES } = require('./cookieBuilder');

function test(name, fn) {
  try {
    fn();
    console.log('  ✓', name);
  } catch (e) {
    console.error('  ✗', name, e.message);
    throw e;
  }
}

console.log('cookieBuilder tests');

test('valid array cookie_json returns non-empty Cookie header', () => {
  const cookieJson = JSON.stringify([
    { name: 'a', value: 'v1' },
    { name: 'b', value: 'v2' },
  ]);
  const r = buildCookieHeader(cookieJson);
  assert.strictEqual(r.error, undefined);
  assert.strictEqual(r.code, undefined);
  assert.strictEqual(r.count, 2);
  assert.ok(r.header.length > 0);
  assert.ok(r.header.includes('a='));
  assert.ok(r.header.includes('b='));
  assert.deepStrictEqual(r.cookieNames, ['a', 'b']);
});

test('valid object with cookies array returns non-empty header', () => {
  const cookieJson = JSON.stringify({ cookies: [{ name: 'x', value: 'y' }] });
  const r = buildCookieHeader(cookieJson);
  assert.strictEqual(r.code, undefined);
  assert.strictEqual(r.count, 1);
  assert.ok(r.header.includes('x='));
});

test('missing cookie_json returns NO_COOKIE_JSON', () => {
  const r = buildCookieHeader(null);
  assert.strictEqual(r.code, ERROR_CODES.NO_COOKIE_JSON);
  assert.strictEqual(r.count, 0);
  assert.strictEqual(r.header, '');
});

test('empty string cookie_json returns NO_COOKIE_JSON', () => {
  const r = buildCookieHeader('');
  assert.strictEqual(r.code, ERROR_CODES.NO_COOKIE_JSON);
  assert.strictEqual(r.count, 0);
});

test('empty array returns EMPTY_COOKIE_LIST', () => {
  const r = buildCookieHeader('[]');
  assert.strictEqual(r.code, ERROR_CODES.EMPTY_COOKIE_LIST);
  assert.strictEqual(r.count, 0);
});

test('invalid JSON returns NO_COOKIE_JSON', () => {
  const r = buildCookieHeader('not json');
  assert.strictEqual(r.code, ERROR_CODES.NO_COOKIE_JSON);
});

test('parseCookieJson exposes codes', () => {
  assert.strictEqual(parseCookieJson(null).code, ERROR_CODES.NO_COOKIE_JSON);
  assert.strictEqual(parseCookieJson('[]').code, ERROR_CODES.EMPTY_COOKIE_LIST);
  assert.ok(parseCookieJson('[{"name":"n","value":"v"}]').cookies);
});

console.log('All cookieBuilder tests passed.');
