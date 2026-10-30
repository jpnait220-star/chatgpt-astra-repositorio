import { Community, validPresence, validMessage } from './community.mjs';
import { createHash } from 'node:crypto';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ITEM = /^[A-Za-z0-9_]{1,64}$/;
class BadRequest extends Error { constructor(status = 400) { super('Bad request'); this.status = status; } }
function reply(res, code, body) {
  res.statusCode = code; res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store'); res.setHeader('X-Content-Type-Options', 'nosniff');
  res.end(JSON.stringify(body));
}
async function body(req) {
  if (!String(req.headers['content-type'] || '').toLowerCase().startsWith('application/json')) throw new BadRequest(415);
  const length = Number(req.headers['content-length']);
  if (length > 16384) throw new BadRequest(413);
  if (req.body !== undefined) {
    const raw = typeof req.body === 'string' || Buffer.isBuffer(req.body) ? req.body.toString() : JSON.stringify(req.body);
    if (Buffer.byteLength(raw) > 16384) throw new BadRequest(413);
    try { return JSON.parse(raw); } catch { throw new BadRequest(); }
  }
  let bytes = 0; const chunks = [];
  for await (const chunk of req) { const data = Buffer.from(chunk); bytes += data.length; if (bytes > 16384) throw new BadRequest(413); chunks.push(data); }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch { throw new BadRequest(); }
}
export function createHandler(store) {
  const community=store?new Community(store):null;
  return async (req, res) => {
    try {
      const url = new URL(req.url, 'http://localhost');
      const route = url.pathname === '/api/relay' ? url.searchParams.get('route') : url.pathname.slice(1);
      if (!['health', 'profile', 'profiles', 'community', 'chat'].includes(route)) return reply(res, 404, { error: 'Not found' });
      const expected = ['profile','community','chat'].includes(route) ? 'POST' : 'GET';
      if (req.method !== expected) { res.setHeader('Allow', expected); return reply(res, 405, { error: 'Method not allowed' }); }
      if (!store) return reply(res, 503, { status: 'unconfigured', service: 'duck-cosmetics' });
      const ip = String(req.headers['x-vercel-forwarded-for'] || req.socket?.remoteAddress || 'unknown').split(',')[0].trim();
      if (!(await store.allow(ip))) { res.setHeader('Retry-After', '60'); return reply(res, 429, { error: 'Too many requests' }); }
      if (route === 'health') {
        const ok = await store.health();
        return reply(res, ok ? 200 : 503, { status: ok ? 'online' : 'unavailable', service: 'duck-cosmetics', protocol: 1 });
      }
      if(route==='community'){
        const value=await body(req);if(!validPresence(value))throw new BadRequest();
        return reply(res,200,await community.heartbeat(value));
      }
      if(route==='chat'){
        const value=await body(req);if(!validMessage(value))throw new BadRequest();
        const result=await community.send(value,createHash('sha256').update(ip).digest('hex').slice(0,32));
        return reply(res,result===false?401:result===null?429:200,{ok:result===true});
      }
      if (route === 'profile') {
        const value = await body(req);
        if (!value || typeof value !== 'object' || typeof value.uuid !== 'string' || !UUID.test(value.uuid) || !Array.isArray(value.cosmetics) || value.cosmetics.length > 32 || value.cosmetics.some(id => typeof id !== 'string' || !ITEM.test(id))) throw new BadRequest();
        await store.put(value.uuid.toLowerCase(), [...new Set(value.cosmetics)]);
        return reply(res, 200, { ok: true });
      }
      if (req.url.length > 4096 || url.searchParams.getAll('ids').length !== 1) throw new BadRequest();
      const ids = url.searchParams.get('ids').split(',');
      if (ids.length > 32 || ids.some(id => !UUID.test(id))) throw new BadRequest();
      return reply(res, 200, await store.get([...new Set(ids.map(id => id.toLowerCase()))]));
    } catch (error) {
      if (error instanceof BadRequest) return reply(res, error.status, { error: 'Invalid request' });
      return reply(res, 503, { status: 'unavailable', service: 'duck-cosmetics' });
    }
  };
}
