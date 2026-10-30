import { test } from 'node:test';import assert from 'node:assert/strict';import { createServer } from 'node:http';import { createHandler } from '../lib/handler.mjs';import { MemoryStore } from '../lib/store.mjs';
const a='00000000-0000-4000-8000-000000000001',b='00000000-0000-4000-8000-000000000002';
test('real presence and global chat HTTP protocol, bounded history, validation and session identity',async()=>{
 const server=createServer(createHandler(new MemoryStore()));await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;
 async function post(path,v){return fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(v)});}
 try{
  let r=await post('/community',{uuid:a,name:'DuckTest'});assert.equal(r.status,200);let first=await r.json();assert.equal(first.online,1);assert.ok(first.token);
  const again=await (await post('/community',{uuid:a,name:'DuckTest'})).json();assert.equal(again.online,1,'two versions of the same account count once');
  const second=await (await post('/community',{uuid:b,name:'OtherDuck'})).json();assert.equal(second.online,2);
  assert.equal((await post('/chat',{token:'00000000-0000-0000-0000-000000000000',text:'spoof'})).status,401);
  assert.equal((await post('/chat',{token:first.token,text:'Ola, Duck!',name:'Spoof'})).status,200);
  const after=await(await post('/community',{uuid:b,name:'OtherDuck',token:second.token})).json();assert.equal(after.messages.length,1);assert.equal(after.messages[0].name,'DuckTest');assert.equal(after.messages[0].uuid,a);assert.equal(after.messages[0].text,'Ola, Duck!');
  assert.equal((await post('/chat',{token:first.token,text:'spam'})).status,429);
  for(const text of ['', ' '.repeat(3),'x'.repeat(161),'hello\nworld','§kbad'])assert.equal((await post('/chat',{token:second.token,text})).status,400);
  for(const value of [{uuid:'bad',name:'Duck'},{uuid:a,name:'<script>'},{uuid:a,name:'Duck',token:'invalid'}])assert.equal((await post('/community',value)).status,400);
  assert.equal((await fetch(base+'/community')).status,405);
  // Expiry removes disconnected clients. No fake fixed online number.
  const store=new MemoryStore();const {Community}=await import('../lib/community.mjs');const community=new Community(store);await community.heartbeat({uuid:a,name:'Duck'});community.present.set(a,Date.now()-66000);assert.equal((await community.heartbeat({uuid:b,name:'Other'})).online,1);
 }finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
test('production Redis protocol uses expiring sessions, unique UUID presence and a bounded shared message list',async()=>{
 const {Community}=await import('../lib/community.mjs');const calls=[];let sent;
 const store={async commands(rows){calls.push(rows);return rows.map(([cmd,key,...args])=>{
  if(cmd==='ZCARD')return 2;if(cmd==='LRANGE')return [];
  if(cmd==='GET')return JSON.stringify({uuid:a,name:'DuckTest'});
  if(cmd==='SET'&&key.startsWith('duck:session:')){sent=args[0];return 'OK';}
  if(cmd==='SET')return 'OK';return 1;
 });}};
 const c=new Community(store);const result=await c.heartbeat({uuid:a,name:'DuckTest'});assert.equal(result.online,2);assert.equal(JSON.parse(sent).uuid,a);
 assert.equal(await c.send({token:result.token,text:'Redis test'},'hashed-ip'),true);
 const all=calls.flat();assert.ok(all.some(x=>x[0]==='ZADD'&&x[3]===a));assert.ok(all.some(x=>x[0]==='ZREMRANGEBYSCORE'));assert.ok(all.some(x=>x[0]==='SET'&&x.at(-2)==='EX'&&x.at(-1)===180));assert.ok(all.some(x=>x[0]==='LTRIM'&&x[3]===39));assert.ok(all.some(x=>x[0]==='EXPIRE'&&x[2]===900));
 const blocked=new Community({commands:async rows=>rows.map(([cmd])=>cmd==='GET'?null:0)});assert.equal(await blocked.send({token:result.token,text:'no session'},'hashed'),false);
});
