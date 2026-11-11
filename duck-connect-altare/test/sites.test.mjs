import {test} from 'node:test';
import assert from 'node:assert/strict';
import {request} from 'node:http';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {createService} from '../server.mjs';
test('Original Community files are preserved and served by domain beside Connect and shared API',async()=>{
 const {server}=createService();await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base='http://127.0.0.1:'+server.address().port;
 const get=(path,host,extra={})=>new Promise((resolve,reject)=>{const req=request(base+path,{headers:{host,...extra}},res=>{const chunks=[];res.on('data',c=>chunks.push(c));res.on('end',()=>{const bytes=Buffer.concat(chunks);resolve({status:res.statusCode,headers:res.headers,bytes,text:async()=>bytes.toString(),json:async()=>JSON.parse(bytes)});});});req.on('error',reject);req.end();});
 try{
  const community=await get('/','duckcommunity.go.altare.global');assert.equal(community.status,200);assert.match(await community.text(),/<title>Canto de Duckzin — DuckzinCommunity/);
  const csp=community.headers['content-security-policy'];
  for(const source of ['https://cdn.jsdelivr.net','https://fonts.googleapis.com','https://fonts.gstatic.com','https://meivyvpqsmhsndgafdwy.supabase.co','https://meivyvpqsmhsndgafdwy.storage.supabase.co','wss://meivyvpqsmhsndgafdwy.supabase.co'])assert.ok(csp.includes(source),source);
  const connect=await get('/','duckconnect.go.altare.global');assert.match(await connect.text(),/<title>Duck Connect/);assert.ok(!connect.headers['content-security-policy'].includes('unsafe-inline'));
  const forged=await get('/','duckconnect.go.altare.global',{'x-forwarded-host':'duckcommunity.go.altare.global'});assert.match(await forged.text(),/<title>Duck Connect/);
  const manifest=JSON.parse(await readFile(new URL('./community-original-sha256.json',import.meta.url),'utf8'));
  for(const [name,hash] of Object.entries(manifest)){
   const r=await get(name==='index.html'?'/':'/'+name,'duckcommunity.go.altare.global');assert.equal(r.status,200,name);
   let originalBytes=r.bytes;
   if(name==='discord-app.js'){
    const migrated=r.bytes.toString();assert.equal(migrated.split("if($('v3Messages'))return;").length,2);
    originalBytes=Buffer.from(migrated.replace("async function loadDiscord(){if($('v3Messages'))return;", "async function loadDiscord(){"));
   }
   assert.equal(createHash('sha256').update(originalBytes).digest('hex'),hash,name);
   if(name.endsWith('.avif'))assert.equal(r.headers['content-type'],'image/avif');
  }
  const fallback=await get('/community/','duckconnect.go.altare.global');assert.deepEqual(fallback.bytes,community.bytes);
  assert.match(await(await get('/connect/','duckcommunity.go.altare.global')).text(),/<title>Duck Connect/);
  const config=await(await get('/config.js','duckcommunity.go.altare.global')).text();assert.match(config,/sb_publishable_/);assert.ok(!config.includes('sb_secret_'));
  for(const host of ['duckcommunity.go.altare.global','duckconnect.go.altare.global'])assert.equal((await(await get('/health',host)).json()).status,'online');
  const head=await fetch(base+'/',{method:'HEAD'});assert.equal(head.status,200);assert.equal(await head.text(),'');
  for(const path of ['/server.mjs','/%2e%2e/server.mjs','/community/server.mjs'])assert.equal((await get(path,'duckcommunity.go.altare.global')).status,404,path);
 }finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
