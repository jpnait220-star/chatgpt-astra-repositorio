import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {createHandler} from './lib/handler.mjs';
import {MemoryStore} from './lib/store.mjs';
export function readConfig(env=process.env){
 const port=Number(env.PORT||env.SERVER_PORT||3000),host=env.HOST||'0.0.0.0';
 if(!Number.isInteger(port)||port<1||port>65535)throw new Error('Use a porta PORT/SERVER_PORT realmente alocada pela Altare (1..65535).');
 if(!['0.0.0.0','127.0.0.1','::'].includes(host))throw new Error('HOST invalido. Use 0.0.0.0 na Altare.');
 return {port,host};
}
export class DedicatedStore extends MemoryStore{
 constructor(maxProfiles=10000){super();this.maxProfiles=maxProfiles;}
 async put(id,items){this.prune();if(!this.entries.has(id)&&this.entries.size>=this.maxProfiles)throw new Error('Temporary profile capacity reached');return super.put(id,items);}
}
export function createService(store=new DedicatedStore()){
 // Deliberate, single-process dedicated state; never a serverless fallback.
 const handler=createHandler(store,{clientIp:req=>req.socket?.remoteAddress||'unknown'});
 const server=createServer(async(req,res)=>{
  let url;try{url=new URL(req.url,'http://localhost');}catch{res.writeHead(400);res.end();return;}
  const hostname=String(req.headers.host||'').toLowerCase().split(':')[0];
  // Host selects only the homepage. Both domains retain the same API/store.
  // Do not trust forwarded host headers or construct external redirects from them.
  const homepage=hostname==='duckcommunity.go.altare.global'?'community/index.html':'index.html';
  const assets=new Map([
   ['/',[homepage,'text/html; charset=utf-8']],
   ['/community/', ['community/index.html','text/html; charset=utf-8']],
   ['/connect/', ['index.html','text/html; charset=utf-8']],
   ['/style.css',['style.css','text/css; charset=utf-8']],
   ['/app.js',['app.js','text/javascript; charset=utf-8']],
   ['/duck.svg',['duck.svg','image/svg+xml']],
   ['/boia.avif',['community/boia.avif','image/avif']],
   ['/config.js',['community/config.js','text/javascript; charset=utf-8']],
   ['/discord-app.js',['community/discord-app.js','text/javascript; charset=utf-8']],
   ['/discord-style.css',['community/discord-style.css','text/css; charset=utf-8']],
   ['/duck-logo.avif',['community/duck-logo.avif','image/avif']],
   ['/duckzin-download-versions.js',['community/duckzin-download-versions.js','text/javascript; charset=utf-8']],
   ['/duckzin-enhance.css',['community/duckzin-enhance.css','text/css; charset=utf-8']],
   ['/duckzin-enhance.js',['community/duckzin-enhance.js','text/javascript; charset=utf-8']],
   ['/duckzin-jelly-particles.js',['community/duckzin-jelly-particles.js','text/javascript; charset=utf-8']],
   ['/duckzin-markdown-card-order.js',['community/duckzin-markdown-card-order.js','text/javascript; charset=utf-8']],
   ['/duckzin-v3.css',['community/duckzin-v3.css','text/css; charset=utf-8']],
   ['/duckzin-v3.js',['community/duckzin-v3.js','text/javascript; charset=utf-8']]
  ]);
  const asset=assets.get(url.pathname);
  if(asset&&['GET','HEAD'].includes(req.method)){
   try{const data=await readFile(new URL('./public/'+asset[0],import.meta.url));res.writeHead(200,{
    'Content-Type':asset[1],'Cache-Control':'no-cache','X-Content-Type-Options':'nosniff',
    'Content-Security-Policy':asset[0].startsWith('community/')
     ? "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https:; media-src 'self' blob: https:; connect-src 'self' https://meivyvpqsmhsndgafdwy.supabase.co https://meivyvpqsmhsndgafdwy.storage.supabase.co wss://meivyvpqsmhsndgafdwy.supabase.co https://cdn.jsdelivr.net; worker-src 'self' blob:; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
     : "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'",
    'Content-Length':data.length
   });res.end(req.method==='HEAD'?undefined:data);}
   catch{res.writeHead(503);res.end('Unavailable');}return;
  }return handler(req,res);
 });
 server.requestTimeout=10000;server.headersTimeout=8000;server.keepAliveTimeout=5000;server.maxConnections=1024;
 return {server,store};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const {port,host}=readConfig(),{server}=createService();
 server.on('error',err=>{console.error('Duck Connect falhou:',err.code||'startup');process.exitCode=1;});
 server.listen(port,host,()=>console.log(`Duck Connect + Community em ${host}:${port}. Uma instancia, estado temporario em RAM; HTTPS pelo App hosting.`));
 const stop=()=>{server.close(()=>process.exit(0));setTimeout(()=>process.exit(0),5000).unref();};
 process.once('SIGTERM',stop);process.once('SIGINT',stop);
}
