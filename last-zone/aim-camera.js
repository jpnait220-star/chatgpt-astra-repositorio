// A single orbit camera: follow movement smoothly, apply mouse rotation immediately.
const CAMERA_TUNING={distance:3.8,adsDistance:1.6,shoulder:.62,follow:28,heightFollow:16,release:12};
const steadyCamera={anchor:new T.Vector3(),round:-1,ready:false,last:performance.now(),arm:3.8,view:-1};
function cameraDirection(p,free=true){const f=BATTLE.free,yaw=p.yaw+(free?f.yaw:0),pitch=Math.max(-1.1,Math.min(1.1,p.pit+(free?f.pitch:0)));return new T.Vector3(Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),Math.cos(yaw)*Math.cos(pitch))}
function stableCameraUpdate(p,dt){
 if(!p?.alive)return;dt=Math.max(0,Math.min(.12,dt));const s=steadyCamera,head=new T.Vector3(p.x,p.y+(p.crouched?1.25:1.65),p.z),snap=!s.ready||s.round!==ROUND_ID||s.view!==view||s.anchor.distanceTo(head)>8;
 if(snap){s.anchor.copy(head);s.round=ROUND_ID;s.ready=true;s.view=view;s.arm=CAMERA_TUNING.distance}else{const a=1-Math.exp(-CAMERA_TUNING.follow*dt);s.anchor.x+=(head.x-s.anchor.x)*a;s.anchor.z+=(head.z-s.anchor.z)*a;s.anchor.y+=(head.y-s.anchor.y)*(1-Math.exp(-CAMERA_TUNING.heightFollow*dt))}
 const direction=cameraDirection(p);cam.up.set(0,1,0);if(view===1){cam.position.copy(s.anchor);cam.lookAt(cam.position.clone().add(direction));return}
 const yaw=p.yaw+BATTLE.free.yaw,right=new T.Vector3(-Math.cos(yaw),0,Math.sin(yaw)),distance=CAMERA_TUNING.distance+(CAMERA_TUNING.adsDistance-CAMERA_TUNING.distance)*aimK,offset=direction.clone().multiplyScalar(view===2?distance:-distance);
 if(view!==2)offset.addScaledVector(right,CAMERA_TUNING.shoulder*(1-.5*aimK));const desired=s.anchor.clone().add(offset),delta=desired.clone().sub(head),length=delta.length();let allowed=length;
 if(length>.001){const ray=new T.Raycaster(),unit=delta.clone().normalize(),up=new T.Vector3(0,.13,0),side=right.clone().multiplyScalar(.13);for(const shift of [new T.Vector3(),side,side.clone().negate(),up,up.clone().negate()]){ray.set(head.clone().add(shift),unit);ray.far=length+.15;const hit=ray.intersectObjects(raySolids(ray.ray,ray.far),false)[0];if(hit)allowed=Math.min(allowed,Math.max(.28,hit.distance-.20))}
  if(allowed<s.arm||snap)s.arm=allowed;else s.arm+=(allowed-s.arm)*(1-Math.exp(-CAMERA_TUNING.release*dt));cam.position.copy(head).addScaledVector(unit,Math.min(allowed,s.arm));
 }else cam.position.copy(desired);
 cam.position.y=Math.max(cam.position.y,terrainHeight(cam.position.x,cam.position.z)+.23);
 if(view===2)cam.lookAt(head);else cam.lookAt(cam.position.clone().add(direction));
}
const cameraRender=rd.render.bind(rd);rd.render=function(scene,camera){const now=performance.now(),dt=(now-steadyCamera.last)/1000;steadyCamera.last=now;if(scene===sc&&state==='play'&&!paused)stableCameraUpdate(pl[0],dt);else if(state!=='play')steadyCamera.ready=false;cameraRender(scene,camera)};
// Stronger, bounded torso assistance; walls, reloads and free look always break the lock.
const ASSIST={lock:null,cone:.11,maxRange:85,hipSpeed:.40,adsSpeed:.58};
softAim=function(p,dt){RETICLE.target=null;if(p?.h&&!paused&&!BATTLE.free.held&&view!==2)cam.lookAt(cam.position.clone().add(cameraDirection(p)));if(!RETICLE.enabled||!p?.alive||!fh||paused||invOpen||BATTLE.free.held||view===2||p.rl>0||p.veh||p.vault||Math.abs(BATTLE.free.yaw)>.03||Math.abs(BATTLE.free.pitch)>.03||!document.pointerLockElement){ASSIST.lock=null;return}let best=null,score=Infinity;const origin=cam.position;dt=Math.min(.08,Math.max(0,dt));
 for(const enemy of pl){if(enemy===p||!enemy.alive||enemy.st!=='ground')continue;const point=new T.Vector3(enemy.x,enemy.y+(enemy.crouched?.95:1.35),enemy.z),delta=point.sub(origin),dist=Math.hypot(delta.x,delta.z);if(dist<2||dist>ASSIST.maxRange)continue;const yaw=Math.atan2(delta.x,delta.z),pitch=Math.atan2(delta.y,dist),ey=ang(p.yaw,yaw),ep=pitch-p.pit,error=Math.hypot(ey,ep),sticky=enemy.id===ASSIST.lock,limit=ASSIST.cone*(sticky?1.2:1);if(error>limit)continue;
 const length=delta.length();aimRay.set(origin,delta.normalize());aimRay.far=Math.max(0,length-.35);const walls=raySolids(aimRay.ray,aimRay.far);if(aimRay.intersectObjects(walls,false).length||aimRay.intersectObject(grassGround,false).length)continue;const weight=error*(sticky?.72:1)+dist*.000025;if(weight<score){score=weight;best={enemy,ey,ep,error}}}
 if(!best){ASSIST.lock=null;return}const gain=1-Math.exp(-(aim?8:6)*dt),speed=(aim?ASSIST.adsSpeed:ASSIST.hipSpeed)*dt,scale=best.error>0?Math.min(gain,speed/best.error):0;p.yaw+=best.ey*scale;p.pit=Math.max(-1,Math.min(1.1,p.pit+best.ep*scale));RETICLE.target=ASSIST.lock=best.enemy.id;
 // Fire reads the camera ray in the same frame, so assistance never waits for the next render.
 if(!BATTLE.free.held)cam.lookAt(cam.position.clone().add(cameraDirection(p,false)));
};
assistButton.textContent='Assistência de mira: '+(RETICLE.enabled?'padrão':'desligada');assistButton.onclick=()=>{RETICLE.enabled=!RETICLE.enabled;ASSIST.lock=null;assistButton.textContent='Assistência de mira: '+(RETICLE.enabled?'padrão':'desligada')};

$('edition').textContent='LAST ZONE · ILHA VERDE · V6';$('news').innerHTML='<strong>ILHA VERDE · 200 HP</strong><br>Gramado corrigido e bosques mais densos<br>Sol natural e sombras mais estáveis<br>Câmera sem balanço e um pouco mais distante<br>Assistência de mira aprimorada com linha de visão<br>48 kits, bots com cura e teclas configuráveis<br><small>Ctrl: toque e solte · C: segure · O: controles</small>';
