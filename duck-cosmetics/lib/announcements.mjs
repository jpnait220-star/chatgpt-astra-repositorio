import {randomBytes,randomUUID} from 'node:crypto';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export const ownerName='DuckTheKiller';
export function validOwner(v){return v&&typeof v.name==='string'&&v.name.toLowerCase()===ownerName.toLowerCase()&&UUID.test(v.uuid);}
export function validAnnouncement(v){return validOwner(v)&&typeof v.challenge==='string'&&/^[0-9a-f]{40}$/.test(v.challenge)&&typeof v.text==='string'&&v.text.trim().length>0&&v.text.length<=160&&!/[\u0000-\u001f\u007f\u00a7]/.test(v.text);}
export class Announcements {
 constructor(store,request=fetch){this.store=store;this.request=request;this.challenges=new Map();this.rate=new Map();this.latest=null;}
 async challenge(v,ip){
  const now=Date.now();
  if(this.store.commands){const [ok]=await this.store.commands([['SET',`duck:announce-challenge-rate:${ip}`,1,'EX',5,'NX']]);if(ok!=='OK')return null;}
  else{if(now-(this.rate.get(ip)||0)<5000)return null;this.rate.set(ip,now);for(const [k,t] of this.rate)if(now-t>60000)this.rate.delete(k);for(const [k,row] of this.challenges)if(row.until<now)this.challenges.delete(k);}
  const challenge=randomBytes(20).toString('hex'),profile={uuid:v.uuid.toLowerCase(),until:now+60000};
  if(this.store.commands)await this.store.commands([['SET',`duck:announce-proof:${challenge}`,JSON.stringify(profile),'EX',60]]);
  else this.challenges.set(challenge,profile);
  return {challenge};
 }
 async publish(v){
  let row;
  if(this.store.commands){const [value]=await this.store.commands([['GETDEL',`duck:announce-proof:${v.challenge}`]]);if(value)row=JSON.parse(value);}
  else{row=this.challenges.get(v.challenge);this.challenges.delete(v.challenge);}
  if(!row||row.until<Date.now()||row.uuid!==v.uuid.toLowerCase())return false;
  // Presence/nick claims are never sufficient: Mojang must prove ownership of the exact account.
  const url=`https://sessionserver.mojang.com/session/minecraft/hasJoined?username=${ownerName}&serverId=${v.challenge}`;
  const response=await this.request(url,{signal:AbortSignal.timeout(4000),redirect:'error'});
  if(response.status!==200)return false;
  const profile=await response.json();
  if(typeof profile.id!=='string'||profile.id.toLowerCase()!==row.uuid.replaceAll('-','')||profile.name?.toLowerCase()!==ownerName.toLowerCase())return false;
  const message={id:randomUUID(),name:'Duckzin',text:v.text.trim(),time:Date.now()};
  if(this.store.commands){const [ok]=await this.store.commands([['SET','duck:announce-send-rate',1,'EX',10,'NX']]);if(ok!=='OK')return null;await this.store.commands([['SET','duck:announcement',JSON.stringify(message),'EX',120]]);}
  else{if(this.latest&&Date.now()-this.latest.time<10000)return null;this.latest=message;}
  return true;
 }
 async read(){
  let message=this.latest;
  if(this.store.commands){const [value]=await this.store.commands([['GET','duck:announcement']]);message=value?JSON.parse(value):null;}
  if(message&&Date.now()-message.time>=120000)message=null;
  return {announcement:message};
 }
}
