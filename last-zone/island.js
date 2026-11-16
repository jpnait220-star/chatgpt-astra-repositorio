// Island revision: world art, consistent trees, movement and a locally synthesized score.
const ISLAND={version:'2.0',time:0,treeCount:0,motionSteps:0};
const art=new T.Group();art.name='IslandArt';sc.add(art);
const artGroups={branches:[],crowns:[],trunks:[]};
// Keep original trunk meshes/colliders, rebuild crowns so no disconnected cones remain.
oldTreeCrowns.visible=false;
const originalTrunks=sc.children.filter(o=>o.isMesh&&o.geometry===tk),treePositions=[];
originalTrunks.forEach((trunk,i)=>{const {x,z}=trunk.position;treePositions.push({x,z});trunk.scale.y=1.4;trunk.position.y=1.4;trunk.castShadow=trunk.receiveShadow=true;const ob=obs.find(o=>o.y0===undefined&&Math.abs((o.x0+o.x1)/2-x)<.01&&Math.abs((o.z0+o.z1)/2-z)<.01);if(ob){ob.y0=0;ob.y1=2.8}
 for(let k=0;k<3;k++){const a=i*.9+k*2.1,dir=new T.Vector3(Math.cos(a)*.8,.9,Math.sin(a)*.8),mid=new T.Vector3(x+dir.x*.5,2.1+dir.y*.5,z+dir.z*.5);const rotation=new T.Euler().setFromQuaternion(new T.Quaternion().setFromUnitVectors(new T.Vector3(0,1,0),dir.clone().normalize()));artGroups.branches.push({p:mid.toArray(),s:[1,dir.length(),1],r:[rotation.x,rotation.y,rotation.z]})}
 const scale=.85+(i%7)*.055;for(let k=0;k<5;k++){const a=k*2.4+i,spread=k===4?0:1.1;artGroups.crowns.push({p:[x+Math.cos(a)*spread,3.15+(k===4?1.25:(k%2)*.5),z+Math.sin(a)*spread],s:[scale*1.65,scale*1.35,scale*1.55],r:[0,a,0]})}});
ISLAND.treeCount=originalTrunks.length;
const bark=mt(0x4f3d2e),branches=instances(new T.CylinderGeometry(.07,.16,1,7),bark,artGroups.branches,art);branches.castShadow=true;
const leafMat=new T.MeshStandardMaterial({color:0x577341,roughness:1});const leafTime={value:0};leafMat.onBeforeCompile=s=>{s.uniforms.treeTime=leafTime;s.vertexShader='uniform float treeTime;\n'+s.vertexShader;s.vertexShader=s.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\ntransformed.x+=sin(treeTime*.9+position.y*2.)*.045*max(0.,position.y);')};
const canopy=instances(new T.SphereGeometry(1,12,9),leafMat,artGroups.crowns,art);canopy.castShadow=true;canopy.frustumCulled=false;
artGroups.crowns.forEach((p,i)=>canopy.setColorAt(i,new T.Color().setHSL(.23+(i%5)*.009,.22+(i%3)*.04,.7+(i%4)*.05)));
// Replace cone-shaped grass with transparent crossed blades. No colliders on decoration.
lightDetail.children.filter(m=>m.geometry?.type==='ConeGeometry').forEach(m=>m.visible=false);
const bladeTex=canvasMap((c,w,h)=>{c.clearRect(0,0,w,h);for(let i=0;i<13;i++){c.fillStyle=['#829553','#728441','#9da05d'][i%3];const x=8+i*19;c.beginPath();c.moveTo(x-6,h);c.quadraticCurveTo(x+4,h*.45,x+(i%3-1)*20,h*(.08+(i%5)*.08));c.quadraticCurveTo(x+12,h*.6,x+9,h);c.fill()}},256,256);
const blades=new T.MeshStandardMaterial({map:bladeTex,alphaTest:.45,side:T.DoubleSide,roughness:1});const grassTransforms=grasses.flatMap((g,i)=>[{p:[g.p[0],.22,g.p[2]],s:[.65,.45,1],r:g.r},{p:[g.p[0],.22,g.p[2]],s:[.65,.45,1],r:[0,g.r[1]+PI/2,0]}]);const bladeMesh=instances(new T.PlaneGeometry(1,1),blades,grassTransforms,lightDetail);bladeMesh.frustumCulled=false;
// A coherent sky gradient replaces the flat backdrop. Clouds are soft sky-space noise.
const skyUniform={value:0};const skyMaterial=new T.ShaderMaterial({side:T.BackSide,depthWrite:false,fog:false,uniforms:{time:skyUniform},vertexShader:'varying vec3 direction;void main(){direction=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:`varying vec3 direction;uniform float time;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}float noise(vec2 p){vec2 a=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(a),hash(a+vec2(1.,0.)),f.x),mix(hash(a+vec2(0.,1.)),hash(a+1.),f.x),f.y);}float cloud(vec2 p){return noise(p)*.5+noise(p*2.1)*.25+noise(p*4.3)*.125;}
void main(){vec3 d=normalize(direction);float h=clamp(d.y,0.,1.);vec3 color=mix(vec3(.46,.61,.67),vec3(.025,.10,.24),pow(h,.42));vec3 sunDir=normalize(vec3(-.6,.9,-.4));float sunGlow=pow(max(dot(d,sunDir),0.),40.);color+=vec3(.40,.28,.12)*sunGlow;float disk=smoothstep(.9990,.9996,dot(d,sunDir));color=mix(color,vec3(1.,.9,.66),disk);if(d.y>.02){vec2 uv=d.xz/(d.y+.22)*1.6+vec2(time*.002,0.);float c=smoothstep(.36,.62,cloud(uv));color=mix(color,vec3(.85,.85,.76),c*.42*smoothstep(.08,.4,d.y));}gl_FragColor=vec4(color,1.);
#include <tonemapping_fragment>
#include <encodings_fragment>
}`});const skyDome=new T.Mesh(new T.SphereGeometry(340,32,16),skyMaterial);skyDome.renderOrder=-10;skyDome.frustumCulled=false;sc.add(skyDome);skySun.visible=false;
sc.traverse(o=>{if(o.isInstancedMesh&&o.material?.isMeshBasicMaterial&&o.material.fog===false)o.visible=false});
sc.fog.color.setHex(0x9eafb0);sc.fog.near=100;sc.fog.far=270;
// Street dressing and roof details use exact original house footprints, leaving every entrance open.
const roofPanels=[],roofTrim=[],plinths=[],paths=[],cobble=[],roofCaps=[];
WORLD_HOUSES.forEach((h,i)=>{const y=h.H*h.floors;
 // Flat roofs remain walkable; corrugated rooftop strips, ledges and rainwater downpipes add scale.
 const roofColor=i%3===0?0x596466:i%3===1?0x885743:0x71644d;
 for(let j=0;j<Math.ceil(h.w*2);j++)roofPanels.push({p:[h.x-h.w/2+j*.5,y+.025,h.z],s:[.09,.045,h.d+.5]});
 roofTrim.push({p:[h.x-h.w/2-.16,y-.04,h.z],s:[.14,.22,h.d+.7]},{p:[h.x+h.w/2+.16,y-.04,h.z],s:[.14,.22,h.d+.7]});
 plinths.push({p:[h.x,h.H*.15/2,h.z-h.d/2-.015],s:[h.w,.15*h.H,.05]});
 // A short entry path connects each front door without filling window openings.
 paths.push({p:[h.x,.036,h.z+h.d/2+1.6],s:[3,.04,3.3]});
 if(h.floors===2){roofCaps.push({p:[h.x+h.w*.27,y+.22,h.z-h.d*.25],s:[.65,.44,.65]})}
 // Paint individual facades for recognizable districts, using a shared surface shader.
 const frameColor=h.x>55?0x40585b:h.z< -50?0x5d5b42:0x4d6564;
 const lamp=new T.Mesh(new T.BoxGeometry(.12,.2,.13),mt(frameColor));lamp.position.set(h.x+1.8,2.15,h.z+h.d/2+.12);art.add(lamp);
});
instances(new T.BoxGeometry(1,1,1),mt(0x705546),roofPanels,art);instances(new T.BoxGeometry(1,1,1),mt(0x41494b),roofTrim,art);instances(new T.BoxGeometry(1,1,1),mt(0x696d64),plinths,art);instances(new T.BoxGeometry(1,1,1),mt(0xb1aa91),paths,art);instances(new T.BoxGeometry(1,1,1),mt(0x727b7a),roofCaps,art);
// Broad curb strips and roadside gravel give streets distinct boundaries.
const curbs=[];for(let a=-140;a<141;a+=2){if(WORLD_HOUSES.some(h=>Math.abs(a-h.z)<h.d/2+2&&Math.abs(h.x)<h.w/2+8))continue;for(const side of [-1,1])curbs.push({p:[side*5.2,.08,a],s:[.22,.16,1.9]})}const curbMeshes=instances(new T.BoxGeometry(1,1,1),mt(0xa9a99a),curbs,art);
const districtSigns=[['PORTO NORTE',0,-48],['VILA SOLAR',-96,48],['POSTO LESTE',96,58],['GALPÕES',-97,-63]];
for(const [name,x,z]of districtSigns){const tex=canvasMap((c,w,h)=>{c.fillStyle='#1d3435';c.fillRect(0,0,w,h);c.strokeStyle='#b7c9a4';c.lineWidth=6;c.strokeRect(8,8,w-16,h-16);c.fillStyle='#e6e8cb';c.font='bold 25px sans-serif';c.textAlign='center';c.fillText(name,w/2,h/2+10)},256,96);const board=new T.Mesh(new T.BoxGeometry(3.2,1.2,.12),new T.MeshStandardMaterial({map:tex,roughness:.9}));board.position.set(x,2.6,z);art.add(board);const posts=instances(new T.CylinderGeometry(.06,.06,2,6),mt(0x434d45),[-1.25,1.25].map(dx=>({p:[x+dx,1,z],s:[1,1,1]})),art)}
// Root-level tree collision metadata now matches its visible trunk height.
sc.updateMatrixWorld(true);
const baseGround=gh;gh=function(p){let y=baseGround(p);for(const h of WORLD_HOUSES){const roof=h.H*h.floors;if(Math.abs(p.x-h.x)<h.w/2+.5&&Math.abs(p.z-h.z)<h.d/2+.5&&p.y>=roof-.08)y=Math.max(y,roof)}return y};
// Collision substeps prevent slide/sprint tunneling. Inputs accelerate in world-space.
const inertiaMove=mv;
function approach(a,b,step){return a<b?Math.min(a+step,b):Math.max(a-step,b)}
mv=function(p,dt,input){if(!p.alive)return;const i={f:0,r:0,run:0,cr:0,j:0,...input};if(p.vault){inertiaMove(p,dt,i);return}p.motion??={x:0,z:0,exhausted:false};const m=p.motion;const standingHeight=1.8;if(!i.cr&&p.st==='ground'&&blocked(p.x,p.z,p.y+.03,standingHeight))i.cr=1;
 m.exhausted=false;p.stamina=100;if(i.cr)i.run=0;p.crouched=!!i.cr;
 const ss=Math.sin(p.yaw),cs=Math.cos(p.yaw),l=Math.max(1,Math.hypot(i.f,i.r)),sp=i.cr?2.6:i.run?8.5:5.2,tx=(i.f*ss-i.r*cs)/l*sp,tz=(i.f*cs+i.r*ss)/l*sp,acc=p.on?30:12;
 const dx=tx-m.x,dz=tz-m.z,d=Math.hypot(dx,dz),step=acc*dt;if(d>step){m.x+=dx/d*step;m.z+=dz/d*step}else{m.x=tx;m.z=tz}
 const speed=Math.hypot(m.x,m.z),f=speed?(m.x*ss+m.z*cs)/speed:0,r=speed?(-m.x*cs+m.z*ss)/speed:0;
 const count=Math.max(1,Math.ceil(dt/.0125));ISLAND.motionSteps+=count;for(let k=0;k<count;k++){const beforeX=p.x,beforeZ=p.z;p.moveSpeed=speed;inertiaMove(p,dt/count,{...i,f,r,j:k===0?i.j:0});if(!p.vault){const height=i.cr?1.15:1.8;for(const o of obs){if(p.y>=(o.y1??9)||p.y+height<=(o.y0||0))continue;const a=o.x0-.4,b=o.x1+.4,c=o.z0-.4,e=o.z1+.4;if(p.x>a&&p.x<b&&p.z>c&&p.z<e){const pens=[p.x-a,b-p.x,p.z-c,e-p.z],idx=pens.indexOf(Math.min(...pens));if(idx===0)p.x=a;else if(idx===1)p.x=b;else if(idx===2)p.z=c;else p.z=e;}}}if(p.vault)break}
 delete p.moveSpeed;
};
// The map shows the same buildings and streets as the rendered world, without revealing bots.
const mapCache=document.createElement('canvas');mapCache.width=mapCache.height=640;const mapInk=mapCache.getContext('2d'),mapXY=v=>(v+160)*2;
mapInk.fillStyle='#244855';mapInk.fillRect(0,0,640,640);mapInk.fillStyle='#78805a';mapInk.beginPath();mapInk.arc(320,320,300,0,PI*2);mapInk.fill();mapInk.strokeStyle='#c4bc95';mapInk.lineWidth=3;mapInk.stroke();mapInk.fillStyle='#53595b';mapInk.fillRect(310,22,20,596);mapInk.fillRect(22,310,596,20);for(const h of WORLD_HOUSES){mapInk.fillStyle='#c4bb9e';mapInk.fillRect(mapXY(h.x-h.w/2),mapXY(h.z-h.d/2),h.w*2,h.d*2);mapInk.strokeStyle='#444f45';mapInk.lineWidth=1;mapInk.strokeRect(mapXY(h.x-h.w/2),mapXY(h.z-h.d/2),h.w*2,h.d*2)}mapInk.fillStyle='#384f38';for(const t of treePositions){mapInk.beginPath();mapInk.arc(mapXY(t.x),mapXY(t.z),3,0,PI*2);mapInk.fill()}
dm=function(c,S){const k=S/320,X=v=>(v+160)*k;c.drawImage(mapCache,0,0,S,S);c.strokeStyle='#c9fbf6';c.lineWidth=2;c.beginPath();c.arc(X(zf.x),X(zf.z),zf.r*k,0,PI*2);c.stroke();if(zs==='shr'){c.strokeStyle='#65b7eb';c.beginPath();c.arc(X(z1.x),X(z1.z),z1.r*k,0,PI*2);c.stroke()}if(S>200){c.font='bold 11px sans-serif';c.textAlign='center';c.fillStyle='#fff5da';AR.forEach(a=>c.fillText(a[0],X(a[1]),X(a[2])))}const p=pl[0];if(!p)return;c.save();c.translate(X(p.x),X(p.z));c.rotate(-p.yaw);c.fillStyle='#fff3b5';c.strokeStyle='#233a36';c.beginPath();c.moveTo(0,7);c.lineTo(-4,-5);c.lineTo(4,-5);c.closePath();c.fill();c.stroke();c.restore()};
// A calm original 16-bar ambient loop, synthesized locally. No downloaded recordings.
const MUSIC={enabled:true,volume:.22,started:false,next:0,step:0,active:0,timer:null,scheduled:0};try{const saved=JSON.parse(localStorage.getItem('lz-music')||'null');if(saved){MUSIC.enabled=!!saved.enabled;MUSIC.volume=Math.max(0,Math.min(1,Number(saved.volume)||0))}}catch{}
const panel=document.createElement('div');panel.id='music-panel';panel.innerHTML='<button id="music-toggle" type="button">♫ MÚSICA</button><input id="music-volume" aria-label="Volume da música" type="range" min="0" max="100" value="'+Math.round(MUSIC.volume*100)+'">';document.body.append(panel);
const musicCSS=document.createElement('style');musicCSS.textContent='#music-panel{position:fixed;right:20px;top:60px;z-index:8;display:flex;gap:7px;align-items:center;background:#10272edb;border:1px solid #476d6e;border-radius:7px;padding:4px 7px}#music-panel button{font-size:11px;padding:5px 7px;background:transparent;color:#d4e8da}#music-panel input{width:65px;accent-color:#b2c9a0}#mini{top:112px}#wl{top:275px}@media(max-height:600px){#mini{width:105px;height:105px;top:100px}#wl{top:215px;font-size:11px;width:150px}#news{font-size:11px;line-height:1.5;max-width:260px}}';document.head.append(musicCSS);
let musicBus=null;const noteHz=n=>440*Math.pow(2,(n-69)/12);
function musicNote(midi,at,duration,volume,type='sine'){if(!musicBus||!MUSIC.enabled)return;const osc=AC.createOscillator(),gain=AC.createGain();osc.type=type;osc.frequency.value=noteHz(midi);gain.gain.setValueAtTime(0,at);gain.gain.linearRampToValueAtTime(volume,at+.025);gain.gain.exponentialRampToValueAtTime(.0001,at+duration);osc.connect(gain);gain.connect(musicBus);osc.start(at);osc.stop(at+duration+.02);MUSIC.active++;MUSIC.scheduled++;osc.onended=()=>{osc.disconnect();gain.disconnect();MUSIC.active--}}
function musicTick(){if(!musicBus||AC.state!=='running'||document.hidden)return;const now=AC.currentTime;if(!MUSIC.enabled){MUSIC.next=now;return}if(MUSIC.next<now-.2)MUSIC.next=now+.05;const stepDuration=60/84/2;let guard=0;while(MUSIC.next<now+.18&&guard++<4){const n=MUSIC.step%128,bar=Math.floor(n/8),chords=[[45,52,57,60],[41,48,53,57],[48,55,60,64],[43,50,55,59]],chord=chords[Math.floor(bar/4)%4],t=MUSIC.next;
 if(n%8===0){for(const pitch of chord.slice(1))musicNote(pitch,t,2.8,.028,'triangle');musicNote(chord[0]-12,t,1.2,.075)}
 const melody=[0,7,12,7,3,7,10,7];if(n%2===0)musicNote(chord[0]+24+melody[Math.floor(n/2)%8],t,1.15,.045,'sine');
 if(n%4===0)musicNote(28,t,.12,.055,'sine');MUSIC.next+=stepDuration;MUSIC.step++}}
function musicLevel(save=false){if(musicBus&&AC)musicBus.gain.setTargetAtTime(MUSIC.enabled?MUSIC.volume*(state==='play'&&!paused?.32:.70):0,AC.currentTime,MUSIC.enabled?.12:.03);$('music-toggle').textContent=MUSIC.enabled?'♫ MÚSICA':'♫ SILENCIADA';if(save)try{localStorage.setItem('lz-music',JSON.stringify({enabled:MUSIC.enabled,volume:MUSIC.volume}))}catch{}}
function startMusic(){initAudio();AC.resume().catch(()=>{});if(!musicBus){musicBus=AC.createGain();musicBus.gain.value=0;musicBus.connect(AC.destination);MUSIC.next=AC.currentTime+.05;MUSIC.started=true;MUSIC.timer=setInterval(musicTick,100)}musicLevel()}
$('music-toggle').onclick=()=>{MUSIC.enabled=!MUSIC.enabled;startMusic();musicLevel(true)};$('music-volume').oninput=e=>{MUSIC.volume=Number(e.target.value)/100;startMusic();musicLevel(true)};musicLevel();document.addEventListener('pointerdown',()=>{startMusic()},{once:true});document.addEventListener('visibilitychange',()=>{if(musicBus){musicBus.gain.cancelScheduledValues(AC.currentTime);musicBus.gain.setTargetAtTime(document.hidden?0:MUSIC.enabled?MUSIC.volume*.4:0,AC.currentTime,.08)}});
// Keep weather optional: the previous permanent rain obscured surfaces and tree silhouettes.
let weatherRain=false;RN.visible=false;const islandQuality=setQuality;setQuality=function(n){islandQuality(n);RN.visible=weatherRain&&n===2;canopy.castShadow=n===2;branches.castShadow=n>0};$('quality').onclick=()=>setQuality((FRONTIER.quality+1)%3);
const islandRender=rd.render.bind(rd);let islandPrev=performance.now(),volumeClock=0;
rd.render=function(scene,camera){const now=performance.now(),dt=Math.min(.05,(now-islandPrev)/1000);islandPrev=now;ISLAND.time+=dt;leafTime.value=ISLAND.time;skyUniform.value=ISLAND.time;if(scene===sc)skyDome.position.set(camera.position.x,0,camera.position.z);volumeClock+=dt;if(volumeClock>.5){volumeClock=0;musicLevel()}islandRender(scene,camera)};
// Keep idle camera and movement state from leaking across restarts.
const islandNew=newGame;newGame=function(){islandNew();pl.forEach(p=>{p.motion={x:0,z:0,exhausted:false}});if(AC)AC.resume().catch(()=>{})};$('bplay').onclick=newGame;$('bagain').onclick=newGame;
const islandPose=pose;pose=function(q,dt,lobby=false){islandPose(q,dt,lobby);const r=q.rig;if(!r)return;if(!lobby&&q.vault){const s=Math.sin(Math.min(1,q.vault.t/.5)*PI);r.avatar.rotation.x=-s*.6;r.legs[0].hip.rotation.x=-s*1.0;r.legs[1].knee.rotation.x=s*1.3}if(!lobby&&q.sl>0){r.avatar.position.y-=.25;r.legs.forEach(l=>{l.hip.rotation.x=-.7;l.knee.rotation.x=1.2})}if(lobby)r.hands.forEach(a=>{a.shoulder.rotation.z+=Math.sin(ISLAND.time*1.1)*.015})};
// Correct warm, directional lighting while retaining detail in shadowed areas.
sc.children.forEach(o=>{if(o.isHemisphereLight){o.intensity=.68;o.color.setHex(0xb8d4dd);o.groundColor.setHex(0x62614a)}});sun.intensity=1.35;rd.toneMappingExposure=1.06;finishShader.uniforms.strength.value=.6;
decodePalette(sc);setQuality(FRONTIER.quality);
$('news').innerHTML='<strong>FRONTIER · ISLAND 2</strong><br>Árvores reconstruídas e copas ao vento<br>Céu atmosférico, ruas e fachadas<br>Mapa com edifícios e vegetação<br>Movimento com aceleração e frenagem<br>Colisão em subpassos e pouso no telhado<br>Trilha ambiente original com volume<br><small>Música inicia após o primeiro clique</small>';
