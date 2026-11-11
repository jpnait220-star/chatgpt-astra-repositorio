import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';

const files=new Map([
 ['index.html','text/html; charset=utf-8'],
 ['boia.avif','image/avif'],['duck-logo.avif','image/avif'],
 ...['config.js','discord-app.js','duckzin-download-versions.js','duckzin-enhance.js','duckzin-jelly-particles.js','duckzin-markdown-card-order.js','duckzin-v3.js'].map(name=>[name,'text/javascript; charset=utf-8']),
 ...['discord-style.css','duckzin-enhance.css','duckzin-v3.css'].map(name=>[name,'text/css; charset=utf-8'])
]);
const csp="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https:; media-src 'self' blob: https:; connect-src 'self' https://meivyvpqsmhsndgafdwy.supabase.co https://meivyvpqsmhsndgafdwy.storage.supabase.co wss://meivyvpqsmhsndgafdwy.supabase.co https://cdn.jsdelivr.net; worker-src 'self' blob:; base-uri 'self'; frame-ancestors 'none'; form-action 'self'";
export function readConfig(env=process.env){
 const port=Number(env.PORT||env.SERVER_PORT||3000);
 if(!Number.isInteger(port)||port<1||port>65535)throw new Error('PORT/SERVER_PORT deve ser a porta alocada para esta nova host (1..65535).');
 return {host:'0.0.0.0',port};
}
export function createSite(){
 const server=createServer(async(req,res)=>{
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Cache-Control','no-cache');
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,{'Allow':'GET, HEAD'});res.end();return;}
  let url;try{url=new URL(req.url,'http://localhost');}catch{res.writeHead(400);res.end();return;}
  // This host serves only Community: no hostname or proxy-header selection.
  if(url.pathname==='/health'){
   res.writeHead(200,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});
   res.end(req.method==='HEAD'?undefined:JSON.stringify({status:'online',service:'duck-community'}));return;
  }
  const name=['/','/community/'].includes(url.pathname)?'index.html':url.pathname.slice(1),type=files.get(name);
  if(!type){res.writeHead(404);res.end('Not found');return;}
  try{
   const data=await readFile(new URL('./public/'+name,import.meta.url));
   res.writeHead(200,{'Content-Type':type,'Content-Length':data.length,'Content-Security-Policy':csp});res.end(req.method==='HEAD'?undefined:data);
  }catch{res.writeHead(503);res.end('Unavailable');}
 });
 server.requestTimeout=10000;server.headersTimeout=8000;server.keepAliveTimeout=5000;server.maxConnections=1024;
 return server;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const {host,port}=readConfig(),server=createSite();
 server.on('error',err=>{console.error('Duck Community falhou:',err.code||'startup');process.exitCode=1;});
 server.listen(port,host,()=>console.log(`Duck Community original em ${host}:${port}. Host exclusiva da Community; dados no Supabase existente.`));
 const stop=()=>{server.close(()=>process.exit(0));setTimeout(()=>process.exit(0),5000).unref();};
 process.once('SIGTERM',stop);process.once('SIGINT',stop);
}
