// Frontier: upgrades layered over the original game, no external models or accounts.
const FRONTIER={autoLoot:true,quality:2,time:0,kills:0,wallCD:0};
const cover=[],crates=[];let hintClock=0;
Object.assign(WP,{
 mp40:{n:'MP40',mag:32,rate:.065,rl:1.9,sp:.045,auto:1,len:.7,col:0x293b47,dm:23,zm:58},
 m1014:{n:'M1014',mag:6,rate:.8,rl:2.6,sp:.065,auto:0,len:1.1,col:0x553638,dm:14,zm:55,pellets:6},
 scar:{n:'SCAR',mag:30,rate:.12,rl:2.3,sp:.018,auto:1,len:1.2,col:0xc3a16b,dm:30,zm:42}
});
Object.assign(IC,{mp40:0x48c9c0,m1014:0xef8a58,scar:0xe3c474,armor:0x5bafff,ice:0x8deaf8});
Object.assign(SD,{mp40:[.07,2800,.7],m1014:[.3,1400,1.2],scar:[.13,2100,1]});
Object.assign(CHEST,{tactical:['Vanguarda • tático',0x28464c],sunset:['Eclipse • cobre',0xab5b3d],arctic:['Polar • branco',0xbddcde]});
Object.assign(HAIR,{silver:['Prata noturna',0xc3d5df,1,0x63edda]});
// Water: inexpensive vertex waves and Fresnel shading in one draw call.
wat.geometry.dispose();wat.geometry=new T.PlaneGeometry(1200,1200,100,100);
wat.material=new T.ShaderMaterial({uniforms:{time:{value:0}},vertexShader:`uniform float time;varying vec3 world;varying float wave;void main(){vec3 p=position;wave=sin(p.x*.10+time)*.13+cos(p.y*.14+time*.8)*.10;p.z+=wave;world=(modelMatrix*vec4(p,1.)).xyz;gl_Position=projectionMatrix*viewMatrix*vec4(world,1.);}`,fragmentShader:`varying vec3 world;varying float wave;void main(){vec3 v=normalize(cameraPosition-world);float f=pow(1.-max(v.y,0.),3.);vec3 col=mix(vec3(.025,.23,.28),vec3(.26,.59,.65),f);col+=wave*.16;float glint=pow(max(0.,sin(world.x*.8+wave*6.)*cos(world.z*.7)),20.);gl_FragColor=vec4(col+glint*.12,1.);#include <tonemapping_fragment>\n#include <encodings_fragment>}`.replace(';#include',';\n#include')});
sc.background.setHex(0x91bac3);sc.fog.color.setHex(0x91bac3);sc.fog.near=65;sc.fog.far=245;
const skySun=new T.Mesh(new T.SphereGeometry(9,16,12),new T.MeshBasicMaterial({color:0xffe6a3,fog:false}));skySun.position.set(-145,170,-210);sc.add(skySun);
const rim=new T.DirectionalLight(0x8ad9ff,.35);rim.position.set(-60,30,-50);sc.add(rim);
function setQuality(n){FRONTIER.quality=n;rd.setPixelRatio(n===0?.7:Math.min(devicePixelRatio,n===1?1:1.5));rd.shadowMap.enabled=n>0;RN.visible=n===2;$('quality').textContent='QUALIDADE: '+['LEVE','MÉDIA','ALTA'][n];}
$('quality').onclick=()=>setQuality((FRONTIER.quality+1)%3);
// Mesh disposal only for uniquely owned geometries; cached materials are retained.
function release(root){const gs=new Set(),ms=new Set();root.traverse(o=>{if(o.geometry)gs.add(o.geometry);if(o.material&&!Object.values(mats).includes(o.material))ms.add(o.material)});gs.forEach(g=>g.dispose());ms.forEach(m=>m.dispose());if(root.parent)root.parent.remove(root);}
const oldChar=mkChar;
mkChar=function(col,o){const q=oldChar(col,o);q.legs=q.body.filter(m=>m.geometry.type==='CylinderGeometry'&&Math.abs(m.position.y-.31)<.01);q.legPhase=0;
 const add=(geo,c,x,y,z)=>{const m=new T.Mesh(geo,mt(c));m.position.set(x,y,z);m.castShadow=true;q.g.add(m);q.body.push(m);return m};
 add(new T.BoxGeometry(.36,.4,.17),0x1b303b,0,1.16,-.22);add(new T.BoxGeometry(.29,.07,.03),0x69e8cc,0,1.36,.22);
 [-.19,.19].forEach(x=>add(new T.BoxGeometry(.09,.15,.065),0x263a40,x,1.07,.23));
 // Distinct canopy panels and suspension lines; canopy follows player yaw.
 q.ch.geometry.dispose();q.ch.geometry=new T.SphereGeometry(2.5,24,12,0,PI*2,0,PI*.48);
 q.ch.material=mt(0x239a99);const ropeMat=mt(0xb8d5d8);
 for(let k=0;k<8;k++){const a=k*PI/4,from=new T.Vector3(Math.cos(a)*2.45,-.1,Math.sin(a)*2.45),to=new T.Vector3(Math.cos(a)*.32,-2.1,Math.sin(a)*.32),d=to.clone().sub(from),rope=new T.Mesh(new T.CylinderGeometry(.012,.012,d.length(),4),ropeMat);rope.position.copy(from).add(to).multiplyScalar(.5);rope.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());q.ch.add(rope)}
 q.g.traverse(m=>{if(m.isMesh)m.frustumCulled=true});return q;};
const oldGun=setGun;
setGun=function(q,t){q.gm.children.forEach(m=>m.geometry?.dispose());if(['mp40','m1014','scar'].includes(t)){oldGun(q,t==='mp40'?'ump':t==='scar'?'ak':'awm');q.gm.scale.set(t==='m1014'?1.25:1,1,t==='mp40'?.7:1);q.gm.children.forEach((m,i)=>{if(i===0)m.material=mt(WP[t].col)});}else{q.gm.scale.setScalar(1);oldGun(q,t)}};
function initGear(p){p.armor=0;p.ice=2;p.stamina=100;p.vault=null;p.kills=0;for(const t in WP){p.mag[t]??=0;p.ammo[t]??=0}}
const oldNew=newGame;
newGame=function(){[...pl.map(p=>p.g),...items.map(i=>i.m),...fx.map(f=>f.m),...GR.map(g=>g.m),...veh.map(v=>v.g),...cover.map(w=>w.m),...crates.map(c=>c.m)].forEach(release);for(const w of cover){obs.splice(obs.indexOf(w.ob),1);solids.splice(solids.indexOf(w.m),1)}cover.length=0;crates.length=0;fx.length=0;GR.length=0;FRONTIER.kills=0;FRONTIER.wallCD=0;fh=fc=aim=0;for(const k in K)K[k]=0;oldNew();pl.forEach(initGear);};
$('bplay').onclick=newGame;$('bagain').onclick=newGame;
const oldLoot=loot;
loot=function(x,z,y=0){const roll=R();if(roll>.42){oldLoot(x,z,y);return}const types=['mp40','m1014','scar','armor','ice'],t=types[Math.floor(R()*types.length)],m=new T.Mesh(new T.BoxGeometry(t==='armor'?.7:.55,.25,.7),mt(IC[t]));m.position.set(x,y+.6,z);sc.add(m);items.push({t,m,x,z,y});};
const oldPick=pick;
pick=function(p,it){if(it.t==='armor'){p.armor=Math.min(100,(p.armor||0)+60);if(p.h)msg('Colete reforçado: '+p.armor);}else if(it.t==='ice'){p.ice=Math.min(8,(p.ice||0)+2);if(p.h)msg('+2 coberturas de gelo');}else{oldPick(p,it);if(it.t==='ammo')for(const t of ['mp40','m1014','scar'])p.ammo[t]+=t==='m1014'?12:40;}if(p.h&&WP[it.t]&&!['pistol','ump','ak','awm'].includes(it.t))msg('Equipou '+WP[it.t].n);};
const oldDmg=dmg;
dmg=function(v,a,part,n){if(v.armor>0&&part==='body'){const absorbed=Math.min(v.armor,n*.5);v.armor-=absorbed;n-=absorbed}oldDmg(v,a,part,n);};
const oldDie=die;
die=function(v,a,part){if(!v.alive)return;if(a&&a!==v){a.kills++;if(a.h)FRONTIER.kills++}const m=new T.Mesh(new T.BoxGeometry(.85,.55,.65),mt(0xdab95c));m.position.set(v.x,v.y+.28,v.z);sc.add(m);crates.push({m,x:v.x,z:v.z,y:v.y,gear:{w:[...v.w],ammo:{...v.ammo},k25:v.k25+1,ice:1}});oldDie(v,a,part)};
function collectCrate(p,c){for(const t of c.gear.w)if(t!=='pistol')pick(p,{t});for(const t in WP)p.ammo[t]+=c.gear.ammo[t]||0;p.k25+=c.gear.k25;p.ice=Math.min(8,p.ice+c.gear.ice);release(c.m);crates.splice(crates.indexOf(c),1);msg('Caixa coletada: equipamentos, munição e kits');}
function nearby(p){let best=null,d=2.8;for(const it of [...items,...crates]){const n=Math.hypot(it.x-p.x,it.z-p.z);if(n<d&&Math.abs(it.y-p.y)<1.8){d=n;best=it}}return best}
function blocked(x,z,y,height=1.8){return obs.some(o=>x>o.x0-.4&&x<o.x1+.4&&z>o.z0-.4&&z<o.z1+.4&&y<(o.y1??9)&&y+height>(o.y0||0));}
function vault(p){if(!p.on||p.st!=='ground'||p.veh||p.vault)return false;const dx=Math.sin(p.yaw),dz=Math.cos(p.yaw),x=p.x+dx*1.1,z=p.z+dz*1.1;const sill=obs.find(o=>x>o.x0-.3&&x<o.x1+.3&&z>o.z0-.3&&z<o.z1+.3&&(o.y1||9)-p.y<=1.25&&(o.y1||0)>p.y+.35);if(!sill)return false;const tx=p.x+dx*2.7,tz=p.z+dz*2.7;if(blocked(tx,tz,p.y)||blocked(x,z,p.y+1,1.2))return false;p.vault={x:p.x,z:p.z,y:p.y,tx,tz,t:0};p.hl=0;return true;}
function iceWall(p){if(!p.alive||p.st!=='ground'||!p.on||p.veh||p.ice<=0||FRONTIER.wallCD>0)return;const x=p.x+Math.sin(p.yaw)*3.4,z=p.z+Math.cos(p.yaw)*3.4;if(blocked(x,z,p.y))return msg('Local obstruído');const width=4,depth=.5,alongX=Math.abs(Math.cos(p.yaw))>.7,w=alongX?width:depth,d=alongX?depth:width,ob={x0:x-w/2,x1:x+w/2,z0:z-d/2,z1:z+d/2,y0:p.y,y1:p.y+2.5};if(pl.some(e=>e.alive&&e.x>ob.x0-.5&&e.x<ob.x1+.5&&e.z>ob.z0-.5&&e.z<ob.z1+.5))return;const m=new T.Mesh(new T.BoxGeometry(w,2.5,d),new T.MeshStandardMaterial({color:0x91e5ed,roughness:.24,metalness:.28}));m.position.set(x,p.y+1.25,z);m.castShadow=true;sc.add(m);const wall={m,ob,hp:300,t:30};m.userData.wall=wall;cover.push(wall);obs.push(ob);solids.push(m);m.updateMatrixWorld(true);p.ice--;FRONTIER.wallCD=1;msg('Cobertura criada · 300 HP · 30 segundos');}
const oldFire=fire;
fire=function(p,o,d){const w=WP[p.w[p.cur]];if(p.cd>0||p.rl>0||p.st!=='ground'||p.veh||p.vault)return;if(p.mag[p.w[p.cur]]<=0){reload(p);return}sc.updateMatrixWorld(true);const rays=w.pellets||1;for(let i=0;i<rays;i++){if(i){p.mag[p.w[p.cur]]++;p.cd=0;p.rl=0}oldFire(p,o,d);}};
// A shotgun pellet cannot inherit the original game's instant head elimination.
const baseDamage=dmg;dmg=function(v,a,part,n){if(a&&WP[a.w[a.cur]]?.pellets)n=WP[a.w[a.cur]].dm*(part==='head'?1.6:1);baseDamage(v,a,part,n)};
const oldMove=mv;
mv=function(p,dt,input){if(p.vault){const v=p.vault;v.t+=dt;const k=Math.min(1,v.t/.5),s=k*k*(3-2*k);p.x=v.x+(v.tx-v.x)*s;p.z=v.z+(v.tz-v.z)*s;p.y=v.y+Math.sin(k*PI)*1.25;p.g.rotation.x=-Math.sin(k*PI)*.3;if(k===1){p.vault=null;p.y=v.y;p.vy=0}return}const i={...input};p.stamina=100;if(i.j&&p.on&&vault(p))return;
 // Suppress automatic pickup only for the player in manual mode, retain bot loot.
 let stored=null;if(p.h&&!FRONTIER.autoLoot||typeof NET!=='undefined'&&NET.role==='host'&&p.id===1){stored=items;items=[]}try{oldMove(p,dt,i)}finally{if(stored)items=stored}
 p.legPhase+=dt*(i.run?14:9);const walk=(i.f||i.r)&&p.st==='ground'&&p.on?1:0;p.legs.forEach((leg,k)=>{leg.rotation.x=Math.sin(p.legPhase+k*PI)*.5*walk});p.ch.rotation.z=Math.sin(FRONTIER.time*1.6)*.055;if(p.h&&i.cr)p.gun.position.y=1.12;else p.gun.position.y=1.3;
};
addEventListener('keydown',e=>{if(state!=='play'||paused||invOpen||!$('bigw').classList.contains('h')||e.repeat||!pl[0]?.alive)return;const p=pl[0];if(e.code==='KeyV')vault(p);if(e.code==='KeyT')iceWall(p);if(e.code==='KeyL'){FRONTIER.autoLoot=!FRONTIER.autoLoot;msg('Coleta '+(FRONTIER.autoLoot?'automática':'manual · E para pegar'))}if(e.code==='KeyE'){const it=nearby(p);if(it){if(it.gear)collectCrate(p,it);else{pick(p,it);release(it.m);items.splice(items.indexOf(it),1)}}}});
const oldRender=rd.render.bind(rd);let prev=performance.now();
rd.render=function(scene,camera){document.body.classList.toggle('in-menu',state==='menu');const now=performance.now(),dt=Math.min(.05,(now-prev)/1000);prev=now;FRONTIER.time+=dt;wat.material.uniforms.time.value=FRONTIER.time;if(state==='play'&&!paused){FRONTIER.wallCD=Math.max(0,FRONTIER.wallCD-dt);for(let k=cover.length-1;k>=0;k--){const w=cover[k];w.t-=dt;if(w.hp<=0||w.t<=0){obs.splice(obs.indexOf(w.ob),1);solids.splice(solids.indexOf(w.m),1);release(w.m);cover.splice(k,1)}}hintClock+=dt;if(hintClock>.12){hintClock=0;const p=pl[0],it=nearby(p);$('extra').textContent='COLETE '+Math.ceil(p.armor||0)+' · FÔLEGO '+Math.ceil(p.stamina||0)+'% · GELO '+(p.ice||0)+' · ELIMINAÇÕES '+FRONTIER.kills;const hint=it?'F · '+(it.gear?'Abrir caixa de loot':WP[it.t]?.n||{armor:'Colete',ice:'Cobertura de gelo'}[it.t]||it.t):p.st==='ground'?'V / Espaço: transpor janela · T: cobertura · L: coleta '+(FRONTIER.autoLoot?'auto':'manual'):'';$('hint').textContent=hint;$('hint').classList.toggle('h',!hint)}}else{$('hint').classList.add('h');$('extra').textContent=''}oldRender(scene,camera);};
// Rebuild the lobby with the new character and release its previous meshes.
if(lp)release(lp.g);lp=null;showChar();setQuality(2);
const oldShow=showChar;showChar=function(){if(lp){release(lp.g);lp=null}oldShow()};
