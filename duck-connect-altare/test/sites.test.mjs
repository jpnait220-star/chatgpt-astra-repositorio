import {test} from 'node:test';
import assert from 'node:assert/strict';
import {request} from 'node:http';
import {createService} from '../server.mjs';
test('Both domain homepages, static assets and shared API remain independent',async()=>{
 const {server}=createService();await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base='http://127.0.0.1:'+server.address().port;
 const get=(path,host,extra={})=>new Promise((resolve,reject)=>{const req=request(base+path,{headers:{host,...extra}},res=>{const chunks=[];res.on('data',c=>chunks.push(c));res.on('end',()=>{const text=Buffer.concat(chunks).toString();resolve({status:res.statusCode,text:async()=>text,json:async()=>JSON.parse(text)});});});req.on('error',reject);req.end();});
 try{
  const community=await get('/','duckcommunity.go.altare.global');assert.equal(community.status,200);assert.match(await community.text(),/<title>Duck Community/);
  const connect=await get('/','duckconnect.go.altare.global');assert.match(await connect.text(),/<title>Duck Connect/);
  const forged=await get('/','duckconnect.go.altare.global',{'x-forwarded-host':'duckcommunity.go.altare.global'});assert.match(await forged.text(),/<title>Duck Connect/);
  for(const path of ['/community/','/connect/','/style.css','/community.css','/app.js','/community.js','/duck.svg','/releases.json'])assert.equal((await get(path,'duckcommunity.go.altare.global')).status,200,path);
  const rows=await(await get('/releases.json','duckcommunity.go.altare.global')).json();assert.ok(rows.length>=138);
  for(const row of rows){assert.ok(row.url.startsWith('https://raw.githubusercontent.com/jpnait220-star/chatgpt-astra-repositorio/asasa/downloads/DuckClientZ-'));assert.ok(row.url.endsWith('.jar'));}
  for(const host of ['duckcommunity.go.altare.global','duckconnect.go.altare.global'])assert.equal((await(await get('/health',host)).json()).status,'online');
  const head=await fetch(base+'/',{method:'HEAD',headers:{host:'duckcommunity.go.altare.global'}});assert.equal(head.status,200);assert.equal(await head.text(),'');
  assert.equal((await get('/server.mjs','duckcommunity.go.altare.global')).status,404);
  assert.equal((await get('/%2e%2e/server.mjs','duckcommunity.go.altare.global')).status,404);
 }finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
