import {test} from 'node:test';import assert from 'node:assert/strict';import {request} from 'node:http';import {readFile,readdir} from 'node:fs/promises';import {createSite,readConfig} from '../server.mjs';
test('New host uses its allocated port and binds publicly',()=>{
 assert.deepEqual(readConfig({SERVER_PORT:'31999'}),{host:'0.0.0.0',port:31999});assert.equal(readConfig({PORT:'30222',SERVER_PORT:'31999'}).port,30222);
 for(const PORT of ['NaN','0','-1','65536','1.5'])assert.throws(()=>readConfig({PORT}));
});
test('Every domain serves original Community; all original assets and API boundaries work',async()=>{
 const server=createSite();await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const get=(path,host)=>new Promise((resolve,reject)=>{const req=request(base+path,{headers:{host}},res=>{const chunks=[];res.on('data',c=>chunks.push(c));res.on('end',()=>resolve({status:res.statusCode,headers:res.headers,body:Buffer.concat(chunks)}));});req.on('error',reject);req.end();});
 try{
  const original=await readFile(new URL('../public/index.html',import.meta.url));
  for(const host of ['duckcommunity.go.altare.global','localhost:31999','internal.altare.global','duckconnect.go.altare.global']){
   const r=await get('/',host);assert.equal(r.status,200);assert.deepEqual(r.body,original);assert.match(r.body.toString(),/Canto de Duckzin — DuckzinCommunity/);
  }
  for(const name of await readdir(new URL('../public/',import.meta.url))){const r=await get('/'+name,'internal.altare.global');assert.equal(r.status,200,name);assert.deepEqual(r.body,await readFile(new URL('../public/'+name,import.meta.url)));if(name.endsWith('.avif'))assert.equal(r.headers['content-type'],'image/avif');}
  assert.deepEqual((await get('/community/','localhost')).body,original);
  assert.equal((await fetch(base+'/',{method:'HEAD'})).status,200);assert.equal(await(await fetch(base+'/',{method:'HEAD'})).text(),'');
  assert.equal((await fetch(base+'/',{method:'POST'})).status,405);
  for(const path of ['/server.mjs','/.env','/%2e%2e/server.mjs','/profiles','/connect/'])assert.equal((await fetch(base+path)).status,404,path);
  assert.deepEqual(await(await fetch(base+'/health')).json(),{status:'online',service:'duck-community'});
 }finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
