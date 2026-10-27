import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { createHandler } from '../lib/handler.mjs';
import { MemoryStore, RedisStore, productionStore, TTL } from '../lib/store.mjs';
const uuid = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';
async function service(store, fn) {
  const server = createServer(createHandler(store));
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try { await fn(`http://127.0.0.1:${server.address().port}`); }
  finally { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
}
const post = body => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
test('the real client protocol: publish/query/deduplicate/normalize/remove, and serverless rewrites', async () => {
  await service(new MemoryStore(), async base => {
    assert.equal((await fetch(base + '/health')).status, 200);
    assert.deepEqual(await (await fetch(base + '/profiles?ids=' + uuid)).json(), {});
    const result = await fetch(base + '/profile', post({ uuid: uuid.toUpperCase(), cosmetics: ['duckMask', 'chinaHat', 'duckMask'] }));
    assert.equal(result.status, 200); assert.deepEqual(await result.json(), { ok: true });
    assert.deepEqual(await (await fetch(base + '/profiles?ids=' + uuid)).json(), { [uuid]: ['duckMask', 'chinaHat'] });
    assert.deepEqual(await (await fetch(base + '/api/relay?route=profiles&ids=' + uuid)).json(), { [uuid]: ['duckMask', 'chinaHat'] });
    await fetch(base + '/profile', post({ uuid, cosmetics: [] }));
    const response = await fetch(base + '/profiles?ids=' + uuid);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.deepEqual(await response.json(), { [uuid]: [] });
  });
});
test('reject invalid inputs, oversized bodies, unsupported verbs and arbitrary paths', async () => {
  await service(new MemoryStore(), async base => {
    for (const body of [null, {}, { uuid: 'bad', cosmetics: [] }, { uuid, cosmetics: ['../file'] }, { uuid, cosmetics: ['a'.repeat(65)] }, { uuid, cosmetics: [42] }, { uuid, cosmetics: Array(33).fill('duckMask') }]) assert.equal((await fetch(base + '/profile', post(body))).status, 400);
    assert.equal((await fetch(base + '/profile', post({ uuid, cosmetics: [], padding: 'x'.repeat(17000) }))).status, 413);
    assert.equal((await fetch(base + '/profile', { method: 'POST', body: '{}' })).status, 415);
    assert.equal((await fetch(base + '/profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' })).status, 400);
    for (const query of ['', 'ids=', 'ids=bad', 'ids=' + Array(33).fill(uuid).join(','), 'ids=' + uuid + '&ids=' + uuid]) assert.equal((await fetch(base + '/profiles?' + query)).status, 400);
    assert.equal((await fetch(base + '/profile')).status, 405);
    assert.equal((await fetch(base + '/anything')).status, 404);
  });
});
test('honest unavailable status, no disk or memory fallback in production, backend failures contained', async () => {
  assert.equal(productionStore({}), null);
  await service(null, async base => {
    const result = await fetch(base + '/health'); assert.equal(result.status, 503); assert.equal((await result.json()).status, 'unconfigured');
  });
  await service({ allow() { throw new Error('secret credential must not leak'); } }, async base => {
    const result = await fetch(base + '/health'); assert.equal(result.status, 503); assert.ok(!(await result.text()).includes('secret'));
  });
});
test('records expire; rate limiting rejects excess requests', async () => {
  const store = new MemoryStore(); await store.put(uuid, ['duckMask']);
  assert.ok(store.entries.get(uuid).until <= Date.now() + TTL * 1000);
  store.entries.get(uuid).until = Date.now() - 1;
  assert.deepEqual(await store.get([uuid]), {});
  for (let i = 0; i < 600; i++) assert.equal(await store.allow('test'), true);
  assert.equal(await store.allow('test'), false);
  await service({ async allow() { return false; } }, async base => {
    const response = await fetch(base + '/health'); assert.equal(response.status, 429); assert.equal(response.headers.get('retry-after'), '60');
  });
});
test('Redis REST uses shared expiring storage, matching MGET, hashes IP, surfaces failures', async () => {
  const calls = [];
  const store = new RedisStore('https://redis.example', 'test-token', async (url, init) => {
    calls.push({ url, init });
    const commands = JSON.parse(init.body);
    return Response.json(commands.map(([name]) => ({ result: { PING: 'PONG', SET: 'OK', MGET: ['["duckMask"]', null], INCR: 1, EXPIRE: 1 }[name] })));
  });
  assert.equal(await store.health(), true); await store.put(uuid, ['duckMask']);
  assert.deepEqual(await store.get([uuid, '00000000-0000-0000-0000-000000000001']), { [uuid]: ['duckMask'] });
  assert.equal(await store.allow('127.0.0.9'), true);
  assert.equal(calls[0].init.headers.Authorization, 'Bearer test-token');
  assert.deepEqual(JSON.parse(calls[1].init.body), [['SET', `duck:profile:${uuid}`, '["duckMask"]', 'EX', 120]]);
  assert.ok(!calls[3].init.body.includes('127.0.0.9'));
  const broken = new RedisStore('https://redis.example', 'x', async () => Response.json([{ error: 'bad' }]));
  await assert.rejects(() => broken.health());
  assert.throws(() => new RedisStore('http://redis.example', 'x'));
});
