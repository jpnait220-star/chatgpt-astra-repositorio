import {test} from 'node:test';import assert from 'node:assert/strict';import {createService} from '../server.mjs';
test('Standalone Connect excludes Community website and keeps the client API',async()=>{
 const {server}=createService();await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 try{
  assert.match(await(await fetch(base+'/')).text(),/<title>Duck Connect/);
  assert.deepEqual(await(await fetch(base+'/health')).json(),{status:'online',service:'duck-cosmetics',protocol:1});
  for(const path of ['/community/','/config.js','/discord-app.js','/duckzin-v3.js','/boia.avif','/server.mjs'])assert.equal((await fetch(base+path)).status,404,path);
  for(const path of ['/app.js','/style.css','/duck.svg'])assert.equal((await fetch(base+path)).status,200,path);
 }finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
