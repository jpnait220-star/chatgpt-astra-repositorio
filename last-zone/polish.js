// Connected volume at every joint and two-bone IK for hand/weapon contact.
const connectedFactory=mkChar;
mkChar=function(col,o){const q=connectedFactory(col,o),r=q.rig;if(!r)return q;const shirt=mt(CHEST[(o||DEFO).chest]?.[1]||0xd5dcdf),skin=mt(0xc7977d);
 const jointBall=(parent,radius,material,y=0)=>{const m=new T.Mesh(new T.SphereGeometry(radius,12,9),material);m.position.y=y;m.castShadow=true;parent.add(m);q.body.push(m);return m};
 r.hands.forEach(a=>{jointBall(a.shoulder,.099,shirt);jointBall(a.elbow,.077,skin);jointBall(a.hand,.066,skin)});
 r.legs.forEach(l=>{const material=l.hip.children.find(c=>c.isMesh)?.material||mt(0x172029);jointBall(l.hip,.12,material);jointBall(l.knee,.104,material)});
 // Small facial forms create a readable face instead of floating black dots.
 for(const side of [-1,1]){const ear=new T.Mesh(new T.SphereGeometry(.048,10,8),mt(0xd3a48d));ear.scale.set(.4,1,.7);ear.position.set(side*.193,.25,0);r.head.add(ear);q.body.push(ear)}
 const nose=new T.Mesh(new T.SphereGeometry(.025,8,6),mt(0xc79b84));nose.scale.set(.7,1,1.4);nose.position.set(0,.245,.196);r.head.add(nose);q.body.push(nose);
 const mouth=new T.Mesh(new T.BoxGeometry(.064,.009,.008),mt(0x8c6155));mouth.position.set(0,.177,.19);r.head.add(mouth);q.body.push(mouth);
 decodePalette(q.g);return q;
};
const inverseDown=new T.Vector3(0,-1,0);
function handIK(arm,target){const start=arm.shoulder.position.clone(),delta=target.clone().sub(start),distance=Math.max(.06,Math.min(.543,delta.length())),dir=delta.normalize(),along=(.29*.29+distance*distance-.26*.26)/(2*distance),height=Math.sqrt(Math.max(0,.29*.29-along*along)),pole=new T.Vector3(arm.side*.8,-.5,-.5);pole.addScaledVector(dir,-pole.dot(dir)).normalize();const elbow=start.clone().addScaledVector(dir,along).addScaledVector(pole,height),wrist=start.clone().addScaledVector(dir,distance),upper=elbow.clone().sub(start).normalize(),lower=wrist.clone().sub(elbow).normalize();arm.shoulder.quaternion.setFromUnitVectors(inverseDown,upper);lower.applyQuaternion(arm.shoulder.quaternion.clone().invert());arm.elbow.quaternion.setFromUnitVectors(inverseDown,lower);arm.hand.rotation.set(0,0,0);arm.lastTarget=wrist;}
const connectedPose=pose;
pose=function(q,dt,lobby=false){connectedPose(q,dt,lobby);const r=q.rig;if(!r)return;const move=lobby?0:r.blend,c=r.crouch||0,run=!lobby&&Math.hypot(q.motion?.x||0,q.motion?.z||0)>6,air=!lobby&&q.st!=='ground',time=ISLAND.time,phase=r.phase,recoil=q.kick||0,reload=q.rl>0?Math.sin((1-q.rl/WP[q.w[q.cur]].rl)*PI):0;
 q.gun.position.set(.025+Math.sin(phase)*move*.012,1.22-c*.04-(run?.14:0)+Math.sin(time*2)*.004,.10-recoil*.035);
 q.gun.rotation.set((run?.28:0)-recoil*.15+reload*.35,Math.sin(phase)*move*.025,reload*.30);q.gun.updateMatrix();
 r.hands.forEach(arm=>{let target=new T.Vector3(arm.side===1?0:-.02,arm.side===1?-.10:-.03,arm.side===1?-.03:.19).applyMatrix4(q.gun.matrix);
 if(arm.side===-1&&reload>0)target.add(new T.Vector3(-reload*.12,-reload*.22,-reload*.04));
 if(air){target.set(arm.side*.48,q.st==='chute'?1.75:1.52,.10);q.gun.visible=false}else q.gun.visible=true;
 if(q.vault)target.set(arm.side*.28,1.2,.35);handIK(arm,target)});
 // Flexion and torso turn are blended rather than snapping to a new pose.
 const lateral=q.motion?(-q.motion.x*Math.cos(q.yaw)+q.motion.z*Math.sin(q.yaw)):0;r.avatar.rotation.z+=Math.max(-.055,Math.min(.055,lateral*.012));r.head.rotation.z=-r.avatar.rotation.z*.35;
 r.legs.forEach((l,i)=>{l.hip.rotation.z=(i===0?1:-1)*(.025+c*.12);l.knee.rotation.x=Math.max(.04,l.knee.rotation.x)});
};
// Distinct roof silhouettes and colored facades create recognizable neighborhoods.
const pitched=[];WORLD_HOUSES.forEach((h,i)=>{if(h.w===9||(i%3===0&&!(h.x===0&&h.z===0))){h.roofRise=h.w===9?1.15:1.4;const y=h.H*h.floors,w=h.w/2+.5,len=Math.hypot(w,h.roofRise),angle=Math.atan2(h.roofRise,w);for(const side of [-1,1]){const roof=new T.Mesh(new T.BoxGeometry(len,.12,h.d+1),new T.MeshStandardMaterial({color:i%2?0x6b5445:0x855e49,roughness:.95}));roof.position.set(h.x+side*w/2,y+h.roofRise/2+.08,h.z);roof.rotation.z=-side*angle;roof.castShadow=roof.receiveShadow=true;art.add(roof);solids.push(roof)}for(const side of [-1,1]){const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute([h.x-w,y,h.z+side*h.d/2,h.x+w,y,h.z+side*h.d/2,h.x,y+h.roofRise,h.z+side*h.d/2],3));geo.computeVertexNormals();const gable=new T.Mesh(geo,new T.MeshStandardMaterial({color:h.c,side:T.DoubleSide,roughness:1}));gable.castShadow=true;art.add(gable)}pitched.push(h)}});
const flatGround=gh;gh=function(p){let h=flatGround(p);for(const house of pitched){if(Math.abs(p.x-house.x)<house.w/2+.5&&Math.abs(p.z-house.z)<house.d/2+.5){const roof=house.H*house.floors+house.roofRise*(1-Math.abs(p.x-house.x)/(house.w/2+.5))+.12;if(p.y>=roof-.08)h=Math.max(h,roof)}}return h};
// The shared town geometry gets a stable per-house palette in world space.
const townMat=mt(0x9aa3ab),townCompile=townMat.onBeforeCompile;
townMat.onBeforeCompile=shader=>{townCompile(shader);shader.fragmentShader=shader.fragmentShader.replace('float row=floor(uvw.y*2.8);',`vec2 district=floor(vec2(detailWorld.x+12.,detailWorld.z+11.)/vec2(24.,22.));float houseSeed=grain(district+17.);vec3 paint=houseSeed<.33?vec3(.93,.67,.43):houseSeed<.66?vec3(.48,.70,.72):vec3(.86,.83,.64);diffuseColor.rgb*=paint;float row=floor(uvw.y*2.8);`)};townMat.needsUpdate=true;
// Low cover in the open military/warehouse yards, each with matching physics and ray geometry.
const mapProps=[];
function solidProp(x,z,w,d,h,c){const m=new T.Mesh(new T.BoxGeometry(w,h,d),mt(c));m.position.set(x,h/2,z);m.castShadow=m.receiveShadow=true;art.add(m);solids.push(m);obs.push({x0:x-w/2,x1:x+w/2,z0:z-d/2,z1:z+d/2,y0:0,y1:h});mapProps.push({x,z,w,d});return m}
for(const [x,z,c]of [[-90,-82,0x435f63],[-107,-58,0x7b5947],[104,-80,0x62674b]]){solidProp(x,z,6,2.8,2.6,c);const corr=[];for(let j=0;j<15;j++)for(const side of [-1,1])corr.push({p:[x-2.85+j*.4,1.3,z+side*1.415],s:[.06,2.4,.035]});instances(new T.BoxGeometry(1,1,1),mt(0x353e39),corr,art)}
for(const [x,z]of [[11,36],[-12,-37],[38,11],[-38,-12]]){solidProp(x,z,1.3,1.3,.85,0x66553c);solidProp(x+1.5,z,1.3,1.3,.85,0x72664d)}
mapInk.fillStyle='#576a67';for(const p of mapProps)mapInk.fillRect(mapXY(p.x-p.w/2),mapXY(p.z-p.d/2),p.w*2,p.d*2);
// Window boxes on front-facing village facades; entrances remain unobstructed.
const boxes=[],blooms=[];WORLD_HOUSES.filter(h=>h.w===9).forEach((h,i)=>{const y=1.0;for(const dx of [-h.w/4,h.w/4]){boxes.push({p:[h.x+dx,y-.12,h.z+h.d/2+.25],s:[1.5,.20,.36]});for(let k=0;k<4;k++)blooms.push({p:[h.x+dx-.55+k*.35,y+.08,h.z+h.d/2+.25],s:[.16,.18,.16]})}});instances(new T.BoxGeometry(1,1,1),mt(0x544335),boxes,art);instances(new T.SphereGeometry(1,8,5),mt(0x6b8c4c),blooms,art);
// Opaque, bounded branches cast shadows only in the quality modes that request them.
sc.updateMatrixWorld(true);decodePalette(sc);showChar();
