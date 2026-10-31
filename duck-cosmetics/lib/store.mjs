import { createHash } from 'node:crypto';
import { supabaseTransport } from './supabase.mjs';
export const TTL = 120;
export class MemoryStore {
  entries = new Map(); limits = new Map();
  async health() { return true; }
  async put(id, items) { this.entries.set(id, { items, until: Date.now() + TTL * 1000 }); this.prune(); }
  prune() { for (const [id, row] of this.entries) if (row.until <= Date.now()) this.entries.delete(id); }
  async get(ids) { this.prune(); return Object.fromEntries(ids.filter(id => this.entries.has(id)).map(id => [id, this.entries.get(id).items])); }
  async allow(ip) {
    const now = Date.now();
    for (const [key, row] of this.limits) if (row.until <= now) this.limits.delete(key);
    const row = this.limits.get(ip) ?? { count: 0, until: now + 60000 };
    row.count++; this.limits.set(ip, row); return row.count <= 600;
  }
}
export class RedisStore {
  constructor(url, token, request = fetch) {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password || parsed.search || parsed.hash) throw new Error('Invalid Redis URL');
    this.url = url.replace(/\/$/, ''); this.token = token; this.request = request;
  }
  async commands(commands) {
    const result = await this.request(this.url + '/pipeline', {
      method: 'POST', headers: { Authorization: `Bearer ${this.token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(commands), signal: AbortSignal.timeout(1000), redirect: 'error'
    });
    if (!result.ok) throw new Error('Storage unavailable');
    const rows = await result.json();
    if (!Array.isArray(rows) || rows.length !== commands.length || rows.some(row => row.error)) throw new Error('Storage unavailable');
    return rows.map(row => row.result);
  }
  async health() { return (await this.commands([['PING']]))[0] === 'PONG'; }
  async put(id, items) { await this.commands([['SET', `duck:profile:${id}`, JSON.stringify(items), 'EX', TTL]]); }
  async get(ids) {
    if (!ids.length) return {};
    const [values] = await this.commands([['MGET', ...ids.map(id => `duck:profile:${id}`)]]);
    if (!Array.isArray(values) || values.length !== ids.length) throw new Error('Storage unavailable');
    const output = {};
    values.forEach((value, i) => { if (value !== null) { const parsed = JSON.parse(value); if (Array.isArray(parsed) && parsed.length <= 32 && parsed.every(x => typeof x === 'string' && /^[A-Za-z0-9_]{1,64}$/.test(x))) output[ids[i]] = parsed; } });
    return output;
  }
  async allow(ip) {
    const key = 'duck:rate:' + createHash('sha256').update(ip).digest('hex').slice(0, 32);
    const [count] = await this.commands([['INCR', key], ['EXPIRE', key, 60, 'NX']]);
    return Number.isSafeInteger(count) && count <= 600;
  }
}
export class SupabaseStore extends RedisStore {
  constructor(url, key, request = fetch) { super(url, key, supabaseTransport(url, key, request)); }
}
export function productionStore(env = process.env) {
  const supabaseUrl = env.SUPABASE_URL;
  const supabaseKey = env.SUPABASE_SERVICE_ROLE_KEY || env.SUPABASE_SECRET_KEY;
  if (supabaseUrl || supabaseKey) return new SupabaseStore(supabaseUrl, supabaseKey);
  const url = env.UPSTASH_REDIS_REST_URL || env.KV_REST_API_URL;
  const token = env.UPSTASH_REDIS_REST_TOKEN || env.KV_REST_API_TOKEN;
  return url && token ? new RedisStore(url, token) : null;
}
