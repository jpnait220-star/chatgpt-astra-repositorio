import {test} from 'node:test';import assert from 'node:assert/strict';
import {createService,readConfig,DedicatedStore} from '../server.mjs';
const id='11111111-2222-4333-8444-555555555555';
test('Altare public binding and allocated-port validation',()=>{
 assert.deepEqual(readConfig({SERVER_PORT:'43210'}),{host:'0.0.0.0',port:43210});
 assert.equal(readConfig({PORT:'12345',SERVER_PORT:'43210'}).port,12345);
 for(const value of ['0','NaN','65536','-1','3.5'])assert.throws(()=>readConfig({PORT:value}));
 assert.throws(()=>readConfig({HOST:'example.com'}));
});
test('Dedicated HTTP cosmetics and community work on all-interface binding; restart state is honest',async()=>{
 const {server}=createService();await new Promise(r=>server.listen(0,'0.0.0.0',r));
 assert.equal(server.address().address,'0.0.0.0');const base='http://127.0.0.1:'+server.address().port;
 const post=value=>({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
 try{
  assert.equal((await fetch(base)).status,200);assert.equal((await fetch(base+'/health')).status,200);
  assert.equal((await fetch(base+'/profile',post({uuid:id,cosmetics:['duckMask']}))).status,200);
  assert.deepEqual(await(await fetch(base+'/profiles?ids='+id)).json(),{[id]:['duckMask']});
  const session=await(await fetch(base+'/community',post({uuid:id,name:'DuckTest'}))).json();
  assert.equal(session.online,1);assert.equal((await fetch(base+'/chat',post({token:session.token,text:'Local test only'}))).status,200);
  assert.deepEqual(await createService().store.get([id]),{});
 }finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
test('Dedicated profile cap is bounded and expired slots are reclaimed',async()=>{
 const store=new DedicatedStore(1);await store.put(id,['duckMask']);await store.put(id,['chinaHat']);
 await assert.rejects(()=>store.put('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',['duckMask']));
 assert.equal(store.entries.size,1);store.entries.get(id).until=0;
 await store.put('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',[]);assert.equal(store.entries.size,1);
});
test('Dedicated hosting ignores forged Vercel source-IP headers',async()=>{
 const seen=[];const {server}=createService({async allow(ip){seen.push(ip);return true;},async health(){return true;}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 try{
  const r=await fetch('http://127.0.0.1:'+server.address().port+'/health',{headers:{'x-vercel-forwarded-for':'198.51.100.9'}});
  assert.equal(r.status,200);assert.equal(seen.length,1);assert.equal(seen[0],'127.0.0.1');
 }finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
