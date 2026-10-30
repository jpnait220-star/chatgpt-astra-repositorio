import { randomUUID } from 'node:crypto';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function validPresence(v){return v&&UUID.test(v.uuid)&&typeof v.name==='string'&&/^[A-Za-z0-9_]{1,16}$/.test(v.name)&&(!v.token||UUID.test(v.token));}
export function validMessage(v){return v&&UUID.test(v.token)&&typeof v.text==='string'&&v.text.trim().length>0&&v.text.length<=160&&!/[\u0000-\u001f\u007f\u00a7]/.test(v.text);}
export class Community {
 constructor(store){this.store=store;this.sessions=new Map();this.present=new Map();this.messages=[];this.rate=new Map();}
 async heartbeat(v){
  const now=Date.now(),token=v.token||randomUUID(),profile={uuid:v.uuid.toLowerCase(),name:v.name};
  if(this.store.commands){
   // Count distinct player UUIDs; reconnecting and two game versions never double-count.
   const rows=await this.store.commands([['SET',`duck:session:${token}`,JSON.stringify(profile),'EX',180],['ZADD','duck:online',now,profile.uuid],['ZREMRANGEBYSCORE','duck:online','-inf',now-65000],['ZCARD','duck:online'],['LRANGE','duck:chat',0,39]]);
   return {token,online:Number(rows[3]),messages:rows[4].map(x=>JSON.parse(x)).filter(x=>now-x.time<900000).reverse()};
  }
  this.sessions.set(token,{...profile,until:now+180000});this.present.set(profile.uuid,now);
  for(const [k,t] of this.present)if(now-t>=65000)this.present.delete(k);
  for(const [k,s] of this.sessions)if(s.until<=now)this.sessions.delete(k);
  for(const [k,t] of this.rate)if(now-t>60000)this.rate.delete(k);
  this.messages=this.messages.filter(x=>now-x.time<900000).slice(-40);
  return {token,online:this.present.size,messages:this.messages};
 }
 async send(v,ip){
  const now=Date.now();let profile;
  if(this.store.commands){
   const [value]=await this.store.commands([['GET',`duck:session:${v.token}`]]);if(!value)return false;profile=JSON.parse(value);
   const [lock]=await this.store.commands([['SET',`duck:chat-rate:${ip}`,1,'PX',3000,'NX']]);if(lock!=='OK')return null;
  }else{
   profile=this.sessions.get(v.token);if(!profile||profile.until<=now)return false;
   if(now-(this.rate.get(ip)||0)<3000)return null;this.rate.set(ip,now);
  }
  const message={id:randomUUID(),uuid:profile.uuid,name:profile.name,text:v.text.trim(),time:now};
  if(this.store.commands)await this.store.commands([['LPUSH','duck:chat',JSON.stringify(message)],['LTRIM','duck:chat',0,39],['EXPIRE','duck:chat',900]]);
  else this.messages=[...this.messages,message].slice(-40);
  return true;
 }
}
