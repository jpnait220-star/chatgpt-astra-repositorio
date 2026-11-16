// Articulated procedural rig. The physics root remains independent from the visual pose.
const rigFactory=mkChar;
mkChar=function(col,o){const q=rigFactory(col,o);o=o||DEFO;const g=q.g,avatar=new T.Group();avatar.name='ArticulatedAvatar';g.add(avatar);
 const moved=g.children.filter(c=>c!==avatar&&c!==q.ch&&c!==q.au&&c!==q.jp);moved.forEach(m=>avatar.add(m));
 const torso=q.body.find(m=>Math.abs(m.position.y-1.2)<.01&&m.geometry.type==='CylinderGeometry');if(torso){torso.geometry.dispose();const points=[[.17,-.31],[.22,-.18],[.25,.08],[.29,.22],[.22,.31]].map(p=>new T.Vector2(...p));torso.geometry=new T.LatheGeometry(points,16);torso.scale.z=.68;}
 const oldLegs=q.legs.slice(),boots=q.body.filter(m=>m.geometry.type==='BoxGeometry'&&Math.abs(m.position.y-.05)<.01);
 const arms=avatar.children.filter(m=>m.isMesh&&m.rotation.order==='YXZ');const legs=[],hands=[];
 function bone(parent,geo,mat,x,y,z,hit=false){const m=new T.Mesh(geo,mat);m.position.set(x,y,z);m.castShadow=true;parent.add(m);q.body.push(m);if(hit){m.userData.part='body';q.parts.push(m)}return m}
 function joint(parent,x,y,z){const j=new T.Group();j.position.set(x,y,z);parent.add(j);return j}
 function discard(m){m.parent?.remove(m);q.parts=q.parts.filter(p=>p!==m);q.body=q.body.filter(p=>p!==m);m.geometry?.dispose()}
 oldLegs.forEach((old,k)=>{const hip=joint(avatar,k?.135:-.135,.76,0),knee=joint(hip,0,-.34,0);const mat=old.material;bone(hip,new T.CylinderGeometry(.12,.105,.34,12),mat,0,-.17,0,true);bone(knee,new T.CylinderGeometry(.104,.078,.32,12),mat,0,-.16,0,true);const foot=bone(knee,new T.BoxGeometry(.18,.12,.30),mt(BOOT[o.boots]?.[1]||0x181f25),0,-.32,.055);bone(knee,new T.BoxGeometry(.185,.035,.31),mt(0x1a2025),0,-.37,.055);
 // Split the wing decal at the knee so cloth follows both moving segments.
 if(angelMats[o.pants]){for(const [part,y,start,end]of [[hip,-.17,.5,1],[knee,-.16,0,.5]]){const geo=new T.PlaneGeometry(.20,.32),uv=geo.attributes.uv;for(let i=0;i<uv.count;i++)uv.setY(i,start+uv.getY(i)*(end-start));const mark=new T.Mesh(geo,wingMat);mark.position.set(0,y,.109);mark.scale.x=k?1:-1;part.add(mark)}}
 discard(old);legs.push({hip,knee,foot});});boots.forEach(discard);
 arms.forEach(discard);const cloth=mt(CHEST[o.chest]?.[1]||0xd5dcdf),skin=mt(0xc7977d);
 for(const side of [-1,1]){const shoulder=joint(avatar,side*.30,1.44,0),elbow=joint(shoulder,0,-.29,0),hand=joint(elbow,0,-.26,0);bone(shoulder,new T.CylinderGeometry(.093,.076,.29,12),cloth,0,-.145,0,true);bone(elbow,new T.CylinderGeometry(.075,.061,.26,12),skin,0,-.13,0,true);bone(hand,new T.SphereGeometry(.075,10,8),mt(0x253139),0,-.025,0);hands.push({shoulder,elbow,hand,side});}
 const head=joint(avatar,0,1.56,0);q.body.filter(m=>m.parent===avatar&&m.position.y>1.57).forEach(m=>{head.add(m);m.position.y-=1.56});
 const hipMesh=q.body.find(m=>m.geometry.type==='CylinderGeometry'&&Math.abs(m.position.y-.76)<.01);if(hipMesh)hipMesh.scale.set(.88,.72,.65);
 q.rig={avatar,legs,hands,head,phase:0,blend:0,crouch:0,lastX:0,lastZ:0,ready:false};return q;
};
function pose(q,dt,lobby=false){const r=q.rig;if(!r)return;let speed=0;if(!lobby&&r.ready)speed=Math.hypot(q.x-r.lastX,q.z-r.lastZ)/Math.max(.001,dt);r.lastX=q.x;r.lastZ=q.z;r.ready=true;const ground=lobby||q.st==='ground'&&q.on,air=!ground&&!lobby,run=speed>6;const target=lobby?0:Math.min(1,speed/3);r.blend+=(target-r.blend)*Math.min(1,dt*12);r.phase+=dt*(run?12:8)*Math.max(.15,r.blend);const cr=!lobby&&(q.crouched??(q.h&&(K.ControlLeft||K.ControlRight)))&&q.st==='ground'?1:0;r.crouch+=(cr-r.crouch)*Math.min(1,dt*12);const c=r.crouch,t=r.phase,b=r.blend,kick=q.kick||0;
 q.g.scale.y=1;r.avatar.position.y=-c*.35+(ground?Math.sin(t*2)*.024*b:0);r.avatar.rotation.x=(run?.10:.025)*b;r.avatar.rotation.z=Math.sin(t)*.025*b;
 r.legs.forEach((leg,i)=>{const cycle=t+i*PI,s=Math.sin(cycle);leg.hip.rotation.x=ground?(s*(run?.70:.45)*b-c*.65):-.25+(i?.12:-.12);leg.knee.rotation.x=ground?Math.max(0,-s)*.85*b+c*1.15:1.0;leg.foot.rotation.x=-leg.knee.rotation.x*.28});
 const reload=q.rl>0?Math.sin((1-q.rl/WP[q.w[q.cur]].rl)*PI):0;
 r.hands.forEach((arm,i)=>{const idle=Math.sin(FRONTIER.time*2)*.018;arm.shoulder.rotation.set(-.75-idle-(air?.45:0)-kick*.15,arm.side*.05,arm.side*-.13);arm.elbow.rotation.x=-.85;arm.shoulder.rotation.z+=Math.sin(t+i*PI)*.05*b;if(i===0){arm.shoulder.rotation.x+=reload*.65;arm.elbow.rotation.x-=reload*.5}if(air){arm.shoulder.rotation.z=arm.side*-.7;arm.elbow.rotation.x=-.4}});
 r.head.rotation.y=lobby?Math.sin(FRONTIER.time*.5)*.07:0;r.head.rotation.x=(!lobby?-(q.pit||0)*.25:0)+Math.sin(FRONTIER.time*1.8)*.01;
 q.gun.position.y=1.20-c*.03;q.gun.position.x=.20;q.gun.position.z=.40;q.gun.rotation.x=-kick*.18+(air?-.7:0)+reload*.35;q.gun.rotation.z=reload*.32;
 if(!lobby&&q.h&&c>0)cam.position.y-=c*.3;
}
const renderRig=rd.render.bind(rd);let rigPrev=performance.now();
rd.render=function(scene,camera){const now=performance.now(),dt=Math.min(.05,Math.max(.001,(now-rigPrev)/1000));rigPrev=now;if(scene===ls&&lp)pose(lp,dt,true);if(scene===sc&&state==='play'&&!paused)pl.filter(p=>p.alive).forEach(p=>pose(p,dt));renderRig(scene,camera)};
// Improve contrast and eliminate excessive flat lobby fill.
ls.children.forEach(o=>{if(o.isHemisphereLight)o.intensity=.55});
const portraitLight=new T.DirectionalLight(0xffdebc,1.1);portraitLight.position.set(2,4,4);ls.add(portraitLight);
sc.children.forEach(o=>{if(o.isHemisphereLight)o.intensity=.72});sun.intensity=1.15;rd.toneMappingExposure=.95;
// Replace simple conifer silhouettes with a broader canopy assembled in a single instanced pass.
const leaves=[];sc.children.filter(o=>o.isMesh&&o.geometry===tg).forEach((tree,i)=>{tree.visible=false;for(let k=0;k<4;k++)leaves.push({p:[tree.position.x+Math.sin(k*2.4)*.9,3.9+k*.55,tree.position.z+Math.cos(k*2.4)*.9],s:[1.8-k*.17,1.2,1.7-k*.15]})});const oldTreeCrowns=instances(new T.IcosahedronGeometry(1,1),new T.MeshStandardMaterial({color:0x526846,roughness:1}),leaves);
// Lobby floating cubes removed so attention stays on the outfit.
LC.forEach(o=>o.visible=false);showChar();
