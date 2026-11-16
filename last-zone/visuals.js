// Procedural artwork inspired by the supplied low-resolution references.
// Textures are shared between characters and never fetch external resources.
const VART={textures:[],materials:[],details:new T.Group()};sc.add(VART.details);
function canvasMap(draw,w=256,h=512){const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);const t=new T.CanvasTexture(c);t.encoding=T.sRGBEncoding;t.anisotropy=Math.min(4,rd.capabilities.getMaxAnisotropy());VART.textures.push(t);return t;}
function jeansMap(accent){return canvasMap((c,w,h)=>{c.fillStyle='#141d25';c.fillRect(0,0,w,h);let seed=7821;const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};for(let i=0;i<12000;i++){const a=rand()*.08;c.fillStyle=`rgba(168,191,207,${a})`;c.fillRect(rand()*w,rand()*h,1,2)}c.strokeStyle='#52616a';c.lineWidth=2;for(const x of [12,w-12]){c.setLineDash([4,4]);c.beginPath();c.moveTo(x,0);c.lineTo(x,h);c.stroke()}c.setLineDash([]);c.strokeStyle='#2e3d48';c.lineWidth=5;c.beginPath();c.moveTo(50,30);c.quadraticCurveTo(130,110,206,40);c.stroke();c.strokeStyle='#54636b';c.lineWidth=1;for(let j=0;j<7;j++){c.beginPath();c.moveTo(60,150+j*5);c.lineTo(180,137+j*7);c.stroke()}c.fillStyle=accent;c.fillRect(225,40,4,400)},256,512)}
const angelMats={};for(const key of ['a1','a2','a3','a4','a5']){const color='#'+new T.Color(PANTS[key][1]).getHexString();angelMats[key]=new T.MeshStandardMaterial({map:jeansMap(color),roughness:.94,metalness:.02});VART.materials.push(angelMats[key])}
const wingMap=canvasMap((c,w,h)=>{c.clearRect(0,0,w,h);c.translate(w*.48,h*.1);c.fillStyle='#eaf4f7';c.strokeStyle='#a7c5cf';c.lineWidth=2;for(let i=0;i<11;i++){const y=i*29,reach=85-i*3;c.beginPath();c.moveTo(0,y);c.quadraticCurveTo(reach*.5,y-26,reach,y-8);c.quadraticCurveTo(reach*.85,y+35,6,y+47);c.quadraticCurveTo(20,y+18,0,y);c.fill();c.stroke()}c.strokeStyle='#ffffff';c.lineWidth=7;c.beginPath();c.moveTo(0,0);c.bezierCurveTo(-24,100,38,235,-20,350);c.stroke();c.fillStyle='#cce8ef';for(let j=0;j<12;j++){c.beginPath();c.arc(-45+(j%3)*12,230+j*12,2,0,PI*2);c.fill()}},256,512);
const wingMat=new T.MeshStandardMaterial({map:wingMap,transparent:true,alphaTest:.12,roughness:.7,depthWrite:false,side:T.DoubleSide});VART.materials.push(wingMat);
const skinFactory=mkChar;
mkChar=function(col,o){o=o||DEFO;const q=skinFactory(col,o);
 const attach=(geo,mat,pos)=>{const m=new T.Mesh(geo,mat);m.position.copy(pos);m.castShadow=true;q.g.add(m);q.body.push(m);return m};
 if(angelMats[o.pants]){q.legs.forEach((leg,k)=>{leg.material=angelMats[o.pants];const mark=new T.Mesh(new T.PlaneGeometry(.23,.57),wingMat);mark.position.set(0,.005,.126);mark.scale.x=k?1:-1;leg.add(mark);const cuff=new T.Mesh(new T.CylinderGeometry(.108,.105,.075,12),mt(0x0b1118));cuff.position.y=-.25;leg.add(cuff)});const hip=q.body.find(m=>Math.abs(m.position.y-.76)<.01);if(hip)hip.material=mt(0x172029);
 // Remove the previous plain neon strips; the requested reference uses dark fabric and pale wings.
 q.body.filter(m=>m.geometry.parameters.width===.03&&m.position.y===.31).forEach(m=>{q.g.remove(m);q.body.splice(q.body.indexOf(m),1);m.geometry.dispose()});
 }
 if(o.hair==='roxa'){const oldColor=HAIR.roxa[1];q.body.filter(m=>m.material===mt(oldColor)).forEach(m=>{q.g.remove(m);q.body.splice(q.body.indexOf(m),1);m.geometry.dispose()});
 const root=new T.MeshStandardMaterial({color:0x514366,roughness:.78}),silver=new T.MeshStandardMaterial({color:0xd6dce6,roughness:.65}),white=new T.MeshStandardMaterial({color:0xf2f1fa,roughness:.6});q.skinMaterials=[root,silver,white];
 attach(new T.SphereGeometry(.226,16,10,0,PI*2,0,PI*.45),root,new T.Vector3(0,1.87,0));
 // Swept asymmetric clusters: pale tips, violet roots, layered fringe.
 for(let i=0;i<26;i++){const a=i*2.39996,r=.09+((i*7)%11)*.009,x=Math.cos(a)*r,z=Math.sin(a)*r,y=2.02+Math.sin(i*1.7)*.035;const tip=new T.Vector3(x*1.6+.045,y+.10+(i%3)*.023,z*1.6+.01);const base=new T.Vector3(x,y-.035,z);const dir=tip.clone().sub(base);const tuft=attach(new T.ConeGeometry(.065,dir.length(),5),i%3?silver:white,base.clone().add(tip).multiplyScalar(.5));tuft.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),dir.normalize());}
 for(let j=0;j<7;j++){const x=(j-3)*.057;const tuft=attach(new T.ConeGeometry(.05,.21,5),j%2?white:silver,new T.Vector3(x,1.96-Math.abs(j-3)*.012,.164));tuft.rotation.z=PI+(j-3)*.13;tuft.rotation.x=-.38;}
 }
 return q;
};
// Protect shared skin textures/materials when a character is replaced.
const previousRelease=release;
release=function(root){const keep=[];root.traverse(m=>{if(m.material&&VART.materials.includes(m.material)){keep.push([m,m.material]);m.material=mt(0x172029)}});previousRelease(root);for(const [m,mat]of keep)m.material=mat;};
const lightDetail=new T.Group();VART.details.add(lightDetail);
function instances(geo,mat,transforms,parent=VART.details){const mesh=new T.InstancedMesh(geo,mat,transforms.length),dummy=new T.Object3D();transforms.forEach((f,i)=>{dummy.position.set(...f.p);dummy.scale.set(...(f.s||[1,1,1]));dummy.rotation.set(...(f.r||[0,0,0]));dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix)});mesh.receiveShadow=true;parent.add(mesh);return mesh;}
let vseed=351;function vr(){vseed=(vseed*1664525+1013904223)>>>0;return vseed/4294967296}
const groundMap=canvasMap((c,w,h)=>{c.fillStyle='#657049';c.fillRect(0,0,w,h);for(let i=0;i<6000;i++){c.fillStyle=i%2?'#788055':'#535f3d';c.fillRect(vr()*w,vr()*h,vr()*3+1,vr()*3+1)}},256,256);groundMap.wrapS=groundMap.wrapT=T.RepeatWrapping;groundMap.repeat.set(55,55);
const grassGround=new T.Mesh(new T.CircleGeometry(GAME_WORLD.radius-8,96),new T.MeshStandardMaterial({map:groundMap,roughness:1}));grassGround.rotation.x=-PI/2;grassGround.position.y=.012;grassGround.receiveShadow=true;sc.add(grassGround);
const shoreline=new T.Mesh(new T.RingGeometry(GAME_WORLD.radius-8,GAME_WORLD.radius,96),new T.MeshStandardMaterial({color:0xc7b48a,roughness:1}));shoreline.rotation.x=-PI/2;shoreline.position.y=.015;sc.add(shoreline);
const lines=[];for(let n=-23;n<=23;n++){if(Math.abs(n)<2)continue;lines.push({p:[0,.047,n*10],s:[.16,.01,4]},{p:[n*10,.047,0],s:[4,.01,.16]})}instances(new T.BoxGeometry(1,1,1),mt(0xd6d0aa),lines);
const grasses=[],rocks=[];for(let i=0;i<900;i++){const a=vr()*PI*2,r=30+vr()*(GAME_WORLD.radius-45),x=Math.cos(a)*r,z=Math.sin(a)*r;if(Math.abs(x)<7||Math.abs(z)<7||spots.some(s=>Math.hypot(x-s[0],z-s[1])<10))continue;grasses.push({p:[x,.12,z],s:[.35+vr()*.4,.25+vr()*.4,1],r:[0,vr()*PI,0]});if(i%14===0)rocks.push({p:[x,.14,z],s:[.4+vr()*.7,.3+vr()*.3,.4+vr()*.6],r:[vr(),vr()*PI,0]})}
instances(new T.ConeGeometry(.25,1,3),mt(0x546937),grasses,lightDetail);instances(new T.DodecahedronGeometry(1,0),mt(0x7e8173),rocks,lightDetail);
// Thin window frames and shutters, no extra collision barriers.
const frames=[],shutters=[];spots.filter(s=>!s[2]).forEach(([x,z])=>{const w=Math.abs(x)<30&&Math.abs(z)<30?12:9,d=Math.abs(x)<30&&Math.abs(z)<30?10:8;for(const side of [-1,1])for(const dx of [-w/4,w/4]){frames.push({p:[x+dx,2.4,z+side*(d/2+.04)],s:[1.7,.09,.12]},{p:[x+dx,.9,z+side*(d/2+.04)],s:[1.7,.10,.14]});for(const sx of [-1,1]){frames.push({p:[x+dx+sx*.82,1.65,z+side*(d/2+.04)],s:[.075,1.5,.1]});shutters.push({p:[x+dx+sx*1.03,1.65,z+side*(d/2+.04)],s:[.28,1.45,.1]})}}});instances(new T.BoxGeometry(1,1,1),mt(0x353d3c),frames);instances(new T.BoxGeometry(1,1,1),mt(0x607c76),shutters);
const clouds=[];for(let i=0;i<30;i++){const a=vr()*PI*2;clouds.push({p:[Math.cos(a)*180,95+vr()*35,Math.sin(a)*180],s:[12+vr()*12,3+vr()*3,6+vr()*8]})}instances(new T.SphereGeometry(1,10,6),new T.MeshBasicMaterial({color:0xe3e8df,fog:false}),clouds);
// Dark showroom gives the skin a readable silhouette.
ls.background.setHex(0x0b1425);ls.children.filter(o=>o.isMesh).forEach(o=>{if(o.geometry.type==='BoxGeometry'){o.material.color.setHex(0x142839);o.material.transparent=false}});
const ring=new T.Mesh(new T.TorusGeometry(1.25,.018,6,64),new T.MeshBasicMaterial({color:0x65e6d8}));ring.rotation.x=PI/2;ring.position.y=.015;ls.add(ring);
const grid=new T.GridHelper(14,28,0x256075,0x183347);grid.position.y=.008;ls.add(grid);
const backlight=new T.DirectionalLight(0x9296ff,.7);backlight.position.set(-3,3,-3);ls.add(backlight);
const vQuality=setQuality;setQuality=function(n){vQuality(n);lightDetail.visible=n>0};$('quality').onclick=()=>setQuality((FRONTIER.quality+1)%3);
// Use the supplied combination initially; existing saved choices remain accessible in the vault.
OUT.hair='roxa';OUT.pants='a2';showChar();
HAIR.roxa[0]='Sombra Roxa · prata / raiz violeta';PANTS.a2[0]='Angelical · preta com asas brancas';
