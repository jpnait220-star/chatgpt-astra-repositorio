import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { createHandler } from './lib/handler.mjs';
import { MemoryStore, productionStore } from './lib/store.mjs';
const local = process.env.NODE_ENV !== 'production';
const handler = createHandler(productionStore() || (local ? new MemoryStore() : null));
const files = { '/': ['index.html', 'text/html; charset=utf-8'], '/style.css': ['style.css', 'text/css'], '/app.js': ['app.js', 'text/javascript'], '/duck.svg': ['duck.svg', 'image/svg+xml'] };
createServer(async (req, res) => {
  const path = new URL(req.url, 'http://localhost').pathname;
  if (!files[path]) return handler(req, res);
  try { const [name, type] = files[path]; const contents = await readFile(new URL('./public/' + name, import.meta.url)); res.setHeader('Content-Type', type); res.end(contents); }
  catch { res.statusCode = 500; res.end('Unavailable'); }
}).listen(Number(process.env.PORT || 3000), '127.0.0.1', () => console.log(`Duck cosmetics: http://localhost:${process.env.PORT || 3000} (${local ? 'local test mode' : 'production'})`));
