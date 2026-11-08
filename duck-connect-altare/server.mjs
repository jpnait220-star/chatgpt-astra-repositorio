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
  if(url.pathname==='/'&&req.method==='GET'){
   try{const html=await readFile(new URL('./public/index.html',import.meta.url));res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'public, max-age=60','X-Content-Type-Options':'nosniff'});res.end(html);}
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
