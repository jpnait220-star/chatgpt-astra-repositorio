/** Server-only PostgreSQL RPC transport. Existing bounded relay commands stay unchanged. */
export function supabaseTransport(url, key, request = fetch) {
  const parsed = new URL(url);
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password || parsed.search || parsed.hash || !['', '/'].includes(parsed.pathname)) throw new Error('Invalid Supabase URL');
  if (typeof key !== 'string' || !key.trim() || key !== key.trim()) throw new Error('Missing Supabase server key');
  const headers = { apikey: key, 'Content-Type': 'application/json' };
  if (key.startsWith('eyJ')) headers.Authorization = `Bearer ${key}`;
  return async (_url, options) => request(parsed.origin + '/rest/v1/rpc/duck_pipeline', {
    method: 'POST', headers, body: JSON.stringify({ p_commands: JSON.parse(options.body) }),
    signal: AbortSignal.timeout(2500), redirect: 'error'
  });
}
