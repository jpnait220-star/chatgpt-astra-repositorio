import {test} from 'node:test';import assert from 'node:assert/strict';import {createServer} from 'node:http';
import {Announcements,validOwner,validAnnouncement} from '../lib/announcements.mjs';import {MemoryStore} from '../lib/store.mjs';import {createHandler} from '../lib/handler.mjs';
const uuid='12345678-1234-4234-8234-123456789012',identity={uuid,name:'DuckTheKiller'};
test('announcement owner requires Mojang nonce proof, not a nickname/presence claim; proof is consumed once',async()=>{
 const store=new MemoryStore();let calls=0;
 const a=new Announcements(store,async(url,options)=>{calls++;assert.ok(url.startsWith('https://sessionserver.mojang.com/session/minecraft/hasJoined?username=DuckTheKiller&serverId='));assert.equal(options.redirect,'error');return{status:200,json:async()=>({id:uuid.replaceAll('-',''),name:'DuckTheKiller'})};});
 assert.ok(validOwner(identity));assert.equal(validOwner({...identity,name:'Other'}),false);
 const {challenge}=await a.challenge(identity,'ip');const value={...identity,challenge,text:'Teste privado'};
 assert.ok(validAnnouncement(value));assert.equal(await a.publish(value),true);assert.equal(await a.publish(value),false);assert.equal(calls,1);
 const received=await a.read();assert.equal(received.announcement.name,'Duckzin');assert.equal(received.announcement.text,'Teste privado');
 a.latest.time=Date.now()-121000;assert.equal((await a.read()).announcement,null);
});
test('forged/wrong Mojang account, replay, expired and missing challenges cannot announce',async()=>{
 for(const profile of [{id:'0'.repeat(32),name:'DuckTheKiller'},{id:uuid.replaceAll('-',''),name:'SomeoneElse'},null]){
  const a=new Announcements(new MemoryStore(),async()=>({status:profile?200:204,json:async()=>profile}));const {challenge}=await a.challenge(identity,'ip');
  assert.equal(await a.publish({...identity,challenge,text:'fake'}),false);assert.equal((await a.read()).announcement,null);
 }
 const a=new Announcements(new MemoryStore(),async()=>{throw new Error('Mojang should not be contacted');});
 const {challenge}=await a.challenge(identity,'ip');assert.equal(await a.challenge(identity,'ip'),null);
 assert.equal(await a.publish({...identity,uuid:'00000000-0000-4000-8000-000000000001',challenge,text:'fake'}),false);
 const c=await a.challenge(identity,'different-ip');a.challenges.get(c.challenge).until=0;
 assert.equal(await a.publish({...identity,challenge:c.challenge,text:'expired'}),false);
 for(const text of ['', 'x'.repeat(161),'bad\ntext','§kspoof'])assert.equal(validAnnouncement({...identity,challenge,text}),false);
});
test('Redis proof is atomic and broadcasts expire; public reads require no identity or profile',async()=>{
 const calls=[];const cache=new Map();const store={commands:async rows=>rows.map(([cmd,key,value,...args])=>{calls.push([cmd,key,value,...args]);if(cmd==='SET'){if(args.includes('NX')&&cache.has(key))return null;cache.set(key,value);return 'OK';}if(cmd==='GET')return cache.get(key)??null;if(cmd==='GETDEL'){const found=cache.get(key);cache.delete(key);return found??null;}})};
 const a=new Announcements(store,async()=>({status:200,json:async()=>({id:uuid.replaceAll('-',''),name:'DuckTheKiller'})}));
 const {challenge}=await a.challenge(identity,'hashed-ip');assert.equal(await a.publish({...identity,challenge,text:'redis'}),true);assert.equal((await a.read()).announcement.text,'redis');
 assert.equal(await a.publish({...identity,challenge,text:'replay'}),false);
 assert.ok(calls.some(r=>r[0]==='GETDEL'));assert.ok(calls.some(r=>r[0]==='SET'&&r[1]==='duck:announcement'&&r.at(-2)==='EX'&&r.at(-1)===120));
});
test('HTTP announcement endpoint rejects other users, invalid payloads and wrong methods without broadcasting',async()=>{
 const server=createServer(createHandler(new MemoryStore()));await new Promise(r=>server.listen(0,'127.0.0.1',r));const base=`http://127.0.0.1:${server.address().port}`;
 const post=(route,value)=>fetch(base+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
 try{assert.deepEqual(await(await fetch(base+'/announcements')).json(),{announcement:null});assert.equal((await post('/announcement-challenge',{...identity,name:'Other'})).status,403);assert.equal((await post('/announcement-challenge',identity)).status,200);assert.equal((await post('/announce',{...identity,challenge:'0'.repeat(40),text:'no proof'})).status,401);assert.equal((await fetch(base+'/announce')).status,405);assert.equal((await post('/announcements',{})).status,405);}finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
