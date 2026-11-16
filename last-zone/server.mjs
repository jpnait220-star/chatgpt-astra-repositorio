import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
import {randomBytes} from 'node:crypto';
const root=dirname(fileURLToPath(import.meta.url));
let settings={};try{settings=JSON.parse(readFileSync(join(root,'server-config.json'),'utf8'))}catch(e){if(e.code!=='ENOENT')throw Error('server-config.json inválido')}
const port=Number(process.env.PORT||process.env.SERVER_PORT||settings.port||8080),host=process.env.HOST||'0.0.0.0';
if(!Number.isInteger(port)||port<1||port>65535)throw Error('Porta inválida: use a porta TCP atribuída no painel.');
const rooms=new Map(),tokens=new Map(),limits=new Map();
const secret=()=>randomBytes(24).toString('hex');
function json(res,status,obj){res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(obj));}
async function body(req,max=262144){let bytes=0,chunks=[];for await(const c of req){bytes+=c.length;if(bytes>max){const err=new Error('Mensagem muito grande');err.status=413;throw err}chunks.push(c)}try{return JSON.parse(Buffer.concat(chunks).toString()||'{}')}catch{const err=new Error('JSON inválido');err.status=400;throw err}}
function send(client,type,data){if(client?.stream&&!client.stream.destroyed){if(client.stream.writableLength>1048576){client.stream.destroy();return}client.stream.write(`event: ${type}\ndata: ${JSON.stringify(data)}\n\n`);}}
function rate(req,res,key,max=45){const now=Date.now(),id=key+':'+(req.socket.remoteAddress||''),record=limits.get(id)||{at:now,n:0};if(now-record.at>1000){record.n=0;record.at=now}record.n++;limits.set(id,record);if(record.n>max){json(res,429,{error:'Muitas mensagens'});return false}return true}
function closeRoom(room){if(!rooms.has(room.id))return;send(room.host,'closed',{reason:'O anfitrião saiu.'});send(room.guest,'closed',{reason:'O anfitrião saiu.'});room.host.stream?.end();room.guest?.stream?.end();tokens.delete(room.host.token);if(room.guest)tokens.delete(room.guest.token);rooms.delete(room.id)}
function sanitizeInput(data){const number=(v,min,max)=>typeof v==='number'&&Number.isFinite(v)?Math.max(min,Math.min(max,v)):0;const keys={};for(const k of ['KeyW','KeyA','KeyS','KeyD','ShiftLeft','ShiftRight','ControlLeft','ControlRight','Space'])keys[k]=!!data.keys?.[k];const actions=Array.isArray(data.actions)?data.actions.filter(a=>['reload','heal25','heal100','grenade','ice','vault','vehicle','loot','slide','jump','weapon0','weapon1','weapon2'].includes(a)).slice(0,8):[];const look={};for(const k of ['hair','mask','chest','pants','boots'])if(typeof data.look?.[k]==='string'&&/^[A-Za-z0-9_-]{1,32}$/.test(data.look[k]))look[k]=data.look[k];return {keys,actions,look,yaw:number(data.yaw,-10000,10000),pit:number(data.pit,-1,1.1),fire:!!data.fire,aim:!!data.aim,stamp:Date.now()};}
const server=http.createServer(async(req,res)=>{res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');const url=new URL(req.url,'http://localhost');try{
 if(req.method==='GET'&&url.pathname==='/health'){json(res,200,{ok:true,game:'last-zone',protocol:3,rooms:rooms.size});return}
 if(req.method==='POST'&&url.pathname==='/api/rooms'){
  if(!rate(req,res,'create',3))return;if(rooms.size>=100){json(res,503,{error:'Servidor cheio'});return}await body(req,1024);let id;do{id=randomBytes(3).toString('hex').toUpperCase()}while(rooms.has(id));const token=secret(),client={token,role:'host',stream:null};const room={id,host:client,guest:null,snapshot:null,last:Date.now()};rooms.set(id,room);tokens.set(token,{room,client});json(res,201,{id,token,role:'host'});return;
 }
 const match=url.pathname.match(/^\/api\/rooms\/([A-Fa-f0-9]{6})\/(join|events|input|state|leave)$/);if(match){const room=rooms.get(match[1].toUpperCase()),action=match[2];if(!room){json(res,404,{error:'Sala não encontrada ou encerrada'});return}
  if(action==='join'&&req.method==='POST'){if(!rate(req,res,'join',4))return;await body(req,1024);if(room.guest){json(res,409,{error:'Esta sala já tem dois jogadores'});return}const client={token:secret(),role:'guest',stream:null};room.guest=client;tokens.set(client.token,{room,client});room.last=Date.now();send(room.host,'peer',{joined:true});json(res,200,{id:room.id,token:client.token,role:'guest'});return}
  const token=(req.headers.authorization||'').replace(/^Bearer /,'')||url.searchParams.get('token'),binding=tokens.get(token);if(!binding||binding.room!==room){json(res,403,{error:'Acesso à sala negado'});return}const client=binding.client;room.last=Date.now();
  if(action==='events'&&req.method==='GET'){res.writeHead(200,{'Content-Type':'text/event-stream','Cache-Control':'no-cache, no-transform','Connection':'keep-alive','X-Accel-Buffering':'no'});res.flushHeaders();clearTimeout(client.cleanup);client.stream?.end();client.stream=res;res.write(': connected\n\n');send(client,'ready',{role:client.role,peer:!!room.guest});if(client.role==='guest'&&room.snapshot)send(client,'state',room.snapshot);const heart=setInterval(()=>{if(!res.destroyed)res.write(': heartbeat\n\n')},10000);req.on('close',()=>{clearInterval(heart);if(client.stream===res){client.stream=null;client.cleanup=setTimeout(()=>{if(client.stream)return;if(client.role==='host')closeRoom(room);else if(room.guest===client){tokens.delete(client.token);room.guest=null;send(room.host,'peer',{joined:false})}},15000);client.cleanup.unref()}});return}
  if(action==='input'&&req.method==='POST'&&client.role==='guest'){if(!rate(req,res,'input:'+room.id,35))return;const data=sanitizeInput(await body(req,4096));send(room.host,'input',data);json(res,200,{ok:true});return}
  if(action==='state'&&req.method==='POST'&&client.role==='host'){if(!rate(req,res,'state:'+room.id,20))return;const data=await body(req);if(!data||!Array.isArray(data.players)||data.players.length>32||!Array.isArray(data.items)||data.items.length>300){json(res,400,{error:'Estado inválido'});return}room.snapshot=data;send(room.guest,'state',data);json(res,200,{ok:true});return}
  if(action==='leave'&&req.method==='POST'){if(client.role==='host')closeRoom(room);else{send(room.host,'peer',{joined:false});client.stream?.end();tokens.delete(client.token);room.guest=null}json(res,200,{ok:true});return}
  json(res,405,{error:'Operação indisponível'});return;
 }
 if(req.method!=='GET'&&req.method!=='HEAD'){json(res,405,{error:'Método indisponível'});return}
 const files={'/':'LAST ZONE Duo.html','/index.html':'LAST ZONE Duo.html','/game.html':'LAST ZONE Duo.html'};const name=files[url.pathname];if(!name){json(res,404,{error:'Página não encontrada'});return}const html=await readFile(join(root,name));res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-cache'});res.end(req.method==='HEAD'?undefined:html);
 }catch(err){if(!res.headersSent)json(res,err.status||500,{error:err.status?err.message:'Falha no servidor'});else res.end()}});
const cleanup=setInterval(()=>{const now=Date.now();for(const room of rooms.values())if(now-room.last>15*60*1000)closeRoom(room);for(const[k,v]of limits)if(now-v.at>60000)limits.delete(k)},30000);cleanup.unref();
server.listen(port,host,()=>console.log(`LAST ZONE Duo disponível na porta ${port}`));
