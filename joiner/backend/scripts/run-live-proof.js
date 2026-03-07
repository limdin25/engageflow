#!/usr/bin/env node
/**
 * Run live proof bundle for Joiner (joiner-dev.up.railway.app).
 * Requires ENGAGEFLOW_JOINER_SECRET in env for db-info.
 * No secrets in output; db-info and headers only.
 */
const base = 'https://joiner-dev.up.railway.app';
const secret = process.env.ENGAGEFLOW_JOINER_SECRET || '';

async function run() {
  console.log('=== 1) Fingerprint (curl -i /) ===');
  const r1 = await fetch(base + '/', { redirect: 'follow' });
  const headers1 = Object.fromEntries(r1.headers.entries());
  const xSha = headers1['x-joiner-git-sha'] || headers1['X-Joiner-Git-Sha'] || '(absent)';
  console.log('X-Joiner-Git-Sha:', xSha);
  console.log('Status:', r1.status);
  console.log('Body:', await r1.text());

  console.log('\n=== 2) db-info ===');
  const r2 = await fetch(base + '/internal/joiner/debug/db-info', {
    headers: { 'X-JOINER-SECRET': secret },
  });
  const text2 = await r2.text();
  if (r2.status === 401) {
    console.log('401 Unauthorized (set ENGAGEFLOW_JOINER_SECRET)');
  } else if (r2.status === 404) {
    console.log('404 — route not present (build not from dev?)');
  } else {
    try {
      const j = JSON.parse(text2);
      console.log(JSON.stringify({ ...j, resolved_path: j.resolved_path ? '[redacted]' : undefined }, null, 2));
    } catch {
      console.log(text2.slice(0, 300));
    }
  }

  console.log('\n=== 3) Failing profile skool-auth ===');
  const r3 = await fetch(base + '/api/profiles/d56f73d2-08bc-4412-a018-960fe89362ad/skool-auth');
  console.log(await r3.text());

  console.log('\n=== 4) With-cookies profile skool-auth ===');
  const r4 = await fetch(base + '/api/profiles/716e152e-eb1b-4282-9e9a-7eb8714a579d/skool-auth');
  const t4 = await r4.text();
  console.log(t4.slice(0, 250) + (t4.length > 250 ? '...' : ''));
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
