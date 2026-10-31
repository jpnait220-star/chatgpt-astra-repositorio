import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { PGlite } from '@electric-sql/pglite';
import { SupabaseStore, productionStore } from '../lib/store.mjs';
import { Community } from '../lib/community.mjs';
import { Announcements } from '../lib/announcements.mjs';

test('Supabase uses real PostgreSQL transactions shared across instances, with private SQL permissions', async () => {
 const db=new PGlite();
 try {
  await db.exec('create role anon;create role authenticated;create role service_role;');
  await db.exec(await readFile(new URL('../supabase/schema.sql',import.meta.url),'utf8'));
  await db.exec(await readFile(new URL('../supabase/schema.sql',import.meta.url),'utf8')); // Re-runnable installation.
  let requests=0;
  const transport=async (url,options)=>{
   requests++;assert.equal(url,'https://fixture.supabase.co/rest/v1/rpc/duck_pipeline');assert.equal(options.headers.apikey,'eyJ.fixture');assert.equal(options.headers.Authorization,'Bearer eyJ.fixture');assert.equal(options.redirect,'error');
   const {p_commands}=JSON.parse(options.body);
   try{const result=await db.query('select public.duck_pipeline($1::jsonb) as data',[JSON.stringify(p_commands)]);return new Response(JSON.stringify(result.rows[0].data));}
   catch{return new Response('{}',{status:400});}
  };
  const a=new SupabaseStore('https://fixture.supabase.co','eyJ.fixture',transport),b=new SupabaseStore('https://fixture.supabase.co','eyJ.fixture',transport);
  const id='00000000-0000-4000-8000-000000000001',other='00000000-0000-4000-8000-000000000002';
  assert.equal(await a.health(),true);
  await a.put(id,['chinaHat','duckMask']);assert.deepEqual(await b.get([id,other]),{[id]:['chinaHat','duckMask']});
  await b.put(id,[]);assert.deepEqual(await a.get([id]),{[id]:[]});
  await db.query("update duck_relay_private.entries set expires_at=now()-interval '1 second' where key=$1",['duck:profile:'+id]);assert.deepEqual(await a.get([id]),{});
  for(let i=0;i<600;i++)assert.equal(await a.allow('rate-test-ip'),true);assert.equal(await b.allow('rate-test-ip'),false);
  await db.exec("update duck_relay_private.entries set expires_at=now()-interval '1 second' where key like 'duck:rate:%'");assert.equal(await b.allow('rate-test-ip'),true);
  const ca=new Community(a),cb=new Community(b);const first=await ca.heartbeat({uuid:id,name:'DuckOne'});const second=await cb.heartbeat({uuid:other,name:'DuckTwo'});assert.equal(second.online,2);
  const same=await cb.heartbeat({uuid:id,name:'DuckOne',token:first.token});assert.equal(same.online,2);
  assert.equal(await ca.send({token:first.token,text:'isolated PostgreSQL fixture'},'chat-test-ip'),true);
  const view=await cb.heartbeat({uuid:other,name:'DuckTwo',token:second.token});assert.equal(view.messages[0].name,'DuckOne');assert.equal(view.messages[0].text,'isolated PostgreSQL fixture');
  assert.equal(await cb.send({token:second.token,text:'rate fixture'},'chat-test-ip'),null);
  assert.equal(await cb.send({token:other,text:'missing session'},'other-ip'),false);
  const owner={uuid:id,name:'DuckTheKiller'};let proofs=0;
  const mojang=async()=>{proofs++;return new Response(JSON.stringify({id:id.replaceAll('-',''),name:'DuckTheKiller'}));};
  const aa=new Announcements(a,mojang),ab=new Announcements(b,mojang);
  const proof=await aa.challenge(owner,'owner-ip');assert.ok(proof.challenge);assert.equal(await ab.publish({...owner,challenge:proof.challenge,text:'isolated announcement fixture'}),true);
  assert.equal((await aa.read()).announcement.text,'isolated announcement fixture');assert.equal(await aa.publish({...owner,challenge:proof.challenge,text:'replay'}),false);assert.equal(proofs,1);
  await db.exec("update duck_relay_private.entries set expires_at=now()-interval '1 second' where key='duck:announcement'");assert.deepEqual(await ab.read(),{announcement:null});
  await assert.rejects(()=>a.commands([['SET','duck:atomic','before'],['FLUSHDB']]));assert.deepEqual(await b.commands([['GET','duck:atomic']]),[null]);
  await assert.rejects(()=>a.commands([['SET','outside:key','no']]));
  for(const role of ['anon','authenticated']){
   await db.exec('set role '+role);
   try{await assert.rejects(()=>db.query('select public.duck_pipeline($1::jsonb)',[JSON.stringify([['PING']])]));await assert.rejects(()=>db.exec('select * from duck_relay_private.entries'));}finally{await db.exec('reset role');}
  }
  await db.exec('set role service_role');try{assert.equal((await db.query('select public.duck_pipeline($1::jsonb) as v',[JSON.stringify([['PING']])])).rows[0].v[0].result,'PONG');}finally{await db.exec('reset role');}
  assert.ok(requests>600);
 }finally{await db.close();}
});

test('Supabase factory validates server configuration and never requires a public client key', async()=>{
 assert.ok(productionStore({SUPABASE_URL:'https://fixture.supabase.co',SUPABASE_SECRET_KEY:'sb_secret_fixture'}) instanceof SupabaseStore);
 assert.equal(productionStore({}),null);
 assert.throws(()=>productionStore({SUPABASE_URL:'https://fixture.supabase.co'}));
 assert.throws(()=>new SupabaseStore('http://fixture.supabase.co','secret'));
 assert.throws(()=>new SupabaseStore('https://fixture.supabase.co/path','secret'));
 assert.throws(()=>new SupabaseStore('https://fixture.supabase.co',' secret'));
 let calls=0;const store=new SupabaseStore('https://fixture.supabase.co','sb_secret_fixture',async(_url,options)=>{calls++;assert.equal(options.headers.Authorization,undefined);assert.equal(options.headers.apikey,'sb_secret_fixture');return new Response('[{"result":"PONG"}]');});assert.equal(await store.health(),true);assert.equal(calls,1);
});
