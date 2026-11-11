/* DuckzinCommunity — partículas 3D preenchendo TODA a aba Início.
 * Centro ancorado no início; partículas também nos cantos; atração das bolinhas para a posição do mouse com inércia.
 * Sem caudas, tentáculos, conexão de linhas ou efeitos em outras abas.
 */
(()=>{
  'use strict';
  if(window.__duckCenterOrbV6)return;
  window.__duckCenterOrbV6=true;

  const STYLE_ID='duckCenterOrbStyle';
  const css=`
    #duckConstellation,#duckHeroSparks,#duckJellyOrb{
      display:none!important;visibility:hidden!important;opacity:0!important;
    }
    #inicio{position:relative!important;isolation:isolate}
    #inicio > #duckParticleGlobes{
      position:absolute!important;inset:0!important;
      display:block!important;width:100%!important;height:100%!important;
      pointer-events:none!important;z-index:0!important;
      opacity:.91;mix-blend-mode:screen;
    }
    #inicio > .hero-inner{position:relative;z-index:1}
    @media(max-width:700px){#inicio > #duckParticleGlobes{opacity:.8}}
    @media(prefers-reduced-motion:reduce){#inicio > #duckParticleGlobes{opacity:.68}}
  `;
  const oldStyle=document.getElementById(STYLE_ID);
  if(oldStyle)oldStyle.textContent=css;
  else {const style=document.createElement('style');style.id=STYLE_ID;style.textContent=css;document.head.append(style)}

  function start(){
    const hero=document.getElementById('inicio');
    if(!hero)return;
    document.getElementById('duckJellyOrb')?.remove();
    document.getElementById('duckConstellation')?.remove();
    document.getElementById('duckHeroSparks')?.remove();
    document.getElementById('duckParticleGlobes')?.remove();
    const canvas=document.createElement('canvas');
    canvas.id='duckParticleGlobes';
    canvas.setAttribute('aria-hidden','true');
    hero.prepend(canvas);
    const ctx=canvas.getContext('2d',{alpha:true,desynchronized:true});
    if(!ctx)return;

    const compact=matchMedia('(max-width:700px)').matches;
    const reduced=matchMedia('(prefers-reduced-motion:reduce)').matches;
    let width=1,height=1,dpr=1,extentX=1,extentY=1,raf=0,last=0,rotation=0,inView=true;
    let motionX=0,motionY=0,targetX=0,targetY=0,turnX=0,turnY=0,aimTurnX=0,aimTurnY=0;
    let pointerX=0,pointerY=0,smoothPointerX=0,smoothPointerY=0;
    let lastPointerX=0,lastPointerY=0,pointerInside=false,impulseX=0,impulseY=0;
    const goldenAngle=Math.PI*(3-Math.sqrt(5));
    const fraction=n=>{const v=Math.sin(n*127.1+78.233)*43758.5453123;return v-Math.floor(v)};
    const count=reduced?(compact?150:270):(compact?370:760);
    const sphere=[];
    for(let i=0;i<count;i++){
      const y=1-2*(i+.5)/count;
      const ring=Math.sqrt(Math.max(0,1-y*y));
      const angle=i*goldenAngle;
      const depth=.73+.27*fraction(i*37+8);
      sphere.push({x:Math.cos(angle)*ring*depth,y:y*depth,z:Math.sin(angle)*ring*depth,
        size:.7+fraction(i*7+9)*1.25,shade:Math.floor(fraction(i*13+51)*3),phase:fraction(i*11+27)*Math.PI*2,
        lag:2.0+fraction(i*37+3)*2.8,ox:0,oy:0});
    }
    // Camada de partículas ambientais até as bordas e cantos da aba inicial.
    const fieldCount=reduced?(compact?55:100):(compact?145:320);
    const field=[];
    for(let i=0;i<fieldCount;i++)field.push({
      u:fraction(i*19+15),v:fraction(i*29+31),
      depth:fraction(i*17+41),size:.65+fraction(i*23+8)*1.25,
      shade:Math.floor(fraction(i*47+3)*3),phase:fraction(i*31+7)*Math.PI*2,
      lag:2.2+fraction(i*43+16)*3,ox:0,oy:0
    });
    const sprites=[[255,250,227],[255,215,139],[255,240,188]].map(([r,g,b])=>{
      const sprite=document.createElement('canvas');sprite.width=sprite.height=48;
      const c=sprite.getContext('2d');
      const glow=c.createRadialGradient(24,24,0,24,24,23);
      glow.addColorStop(0,`rgba(${r},${g},${b},1)`);
      glow.addColorStop(.1,`rgba(${r},${g},${b},.85)`);
      glow.addColorStop(.25,`rgba(${r},${g},${b},.23)`);
      glow.addColorStop(.52,`rgba(${r},${g},${b},.035)`);
      glow.addColorStop(1,`rgba(${r},${g},${b},0)`);
      c.fillStyle=glow;c.fillRect(0,0,48,48);return sprite;
    });

    function resize(){
      const rect=hero.getBoundingClientRect();
      width=Math.max(1,rect.width);height=Math.max(1,rect.height);
      dpr=Math.min(devicePixelRatio||1,compact?1.2:1.5);
      canvas.width=Math.max(1,Math.round(width*dpr));
      canvas.height=Math.max(1,Math.round(height*dpr));
      ctx.setTransform(dpr,0,0,dpr,0,0);
      // A esfera vira um campo amplo: ela ultrapassa o viewport e é cortada nas bordas.
      extentX=width*(compact?.78:.82);
      extentY=height*(compact?.88:.93);
      pointerX=smoothPointerX=lastPointerX=width*.5;
      pointerY=smoothPointerY=lastPointerY=height*.5;
    }
    const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
    function onPointer(e){
      const r=hero.getBoundingClientRect();
      if(!inView||hero.hidden||getComputedStyle(hero).display==='none'||r.width<=0||r.height<=0)return;
      const x=clamp(e.clientX-r.left,0,width);
      const y=clamp(e.clientY-r.top,0,height);
      if(!pointerInside){lastPointerX=x;lastPointerY=y;smoothPointerX=x;smoothPointerY=y;}
      if(!reduced){
        // Captura a direção em que o mouse viaja para as partículas seguirem seu movimento.
        impulseX=clamp(impulseX*.52+(x-lastPointerX)*1.25,-68,68);
        impulseY=clamp(impulseY*.52+(y-lastPointerY)*1.25,-68,68);
        aimTurnX=clamp((x-width*.5)/(width*.5),-1,1);
        aimTurnY=clamp((y-height*.5)/(height*.5),-1,1);
        const maxShift=Math.min(52,width*.063);
        targetX=aimTurnX*maxShift;
        targetY=aimTurnY*maxShift*.7;
      }
      pointerInside=true;pointerX=x;pointerY=y;
      lastPointerX=x;lastPointerY=y;
      if(inView&&!raf&&!document.hidden)schedule();
    }
    // Cada ponto é atraído pelo cursor com velocidade própria; quando o ponteiro sai,
    // retorna aos poucos ao lugar, sem trilhas, linhas ou caudas.
    function followParticle(p,x,y,dt,depth){
      let desiredX=0,desiredY=0;
      if(pointerInside&&!reduced){
        const dx=smoothPointerX-x,dy=smoothPointerY-y;
        const distance=Math.hypot(dx,dy);
        const radius=Math.max(260,Math.min(600,Math.min(width,height)*.79));
        const proximity=Math.max(0,1-distance/radius);
        const force=proximity*proximity;
        const strength=(.42+.17*depth)*force;
        desiredX=clamp(dx*strength+impulseX*force*.56,-155,155);
        desiredY=clamp(dy*strength+impulseY*force*.56,-135,135);
      }
      const easing=1-Math.exp(-dt*p.lag);
      p.ox+=(desiredX-p.ox)*easing;
      p.oy+=(desiredY-p.oy)*easing;
      return [x+p.ox,y+p.oy];
    }
    function draw(now){
      raf=0;
      if(document.hidden||!inView)return;
      const dt=Math.min((last?now-last:16)/1000,.06);last=now;
      if(!reduced)rotation+=dt*.045;
      const smooth=1-Math.exp(-dt*2.4);
      motionX+=(targetX-motionX)*smooth;
      motionY+=(targetY-motionY)*smooth;
      turnX+=(aimTurnX-turnX)*smooth;
      turnY+=(aimTurnY-turnY)*smooth;
      if(pointerInside){
        const pointerEasing=1-Math.exp(-dt*8);
        smoothPointerX+=(pointerX-smoothPointerX)*pointerEasing;
        smoothPointerY+=(pointerY-smoothPointerY)*pointerEasing;
      }
      impulseX*=Math.exp(-dt*4.1);
      impulseY*=Math.exp(-dt*4.1);
      ctx.clearRect(0,0,width,height);
      const centerX=width*.5+motionX,centerY=height*.5+motionY;
      const angle=rotation+turnX*.18,c=Math.cos(angle),s=Math.sin(angle);
      const vertical=turnY*.16+.08,cy=Math.cos(vertical),sy=Math.sin(vertical);
      for(const p of sphere){
        const dx=p.x*c-p.z*s,dz=p.x*s+p.z*c;
        const dy=p.y*cy-dz*sy,depth=p.y*sy+dz*cy;
        const perspective=.89+.12*(depth+1)*.5;
        const baseX=centerX+dx*extentX*perspective,baseY=centerY+dy*extentY*perspective;
        const [px,py]=followParticle(p,baseX,baseY,dt,(depth+1)*.5);
        if(px<0||px>width||py<0||py>height)continue;
        const opacity=.21+.71*(depth+1)*.5;
        const pulse=reduced?1:.95+.05*Math.sin(rotation*6+p.phase);
        ctx.globalAlpha=opacity*pulse;
        const size=(3.3+p.size*5)*(compact?.82:1);
        ctx.drawImage(sprites[p.shade],px-size/2,py-size/2,size,size);
      }
      // Espalha pontos até os cantos; cada ponto fica no fundo, não sobre os textos.
      for(const p of field){
        const drift=reduced?0:Math.sin(rotation*4+p.phase)*3;
        const baseX=p.u*width+(p.depth-.5)*motionX*.5+drift;
        const baseY=p.v*height+(p.depth-.5)*motionY*.5+drift*.65;
        const [x,y]=followParticle(p,baseX,baseY,dt,p.depth);
        const alpha=.23+.49*p.depth;
        ctx.globalAlpha=alpha;
        const size=(2.8+p.size*4.1)*(compact?.78:1);
        ctx.drawImage(sprites[p.shade],x-size/2,y-size/2,size,size);
      }
      ctx.globalAlpha=1;
      if(!reduced)schedule();
    }
    function schedule(){if(!raf)raf=requestAnimationFrame(draw)}
    function pause(){if(raf)cancelAnimationFrame(raf);raf=0;last=0}
    if('IntersectionObserver'in window){
      new IntersectionObserver(entries=>{
        inView=!!entries[0]?.isIntersecting;
        if(inView){last=0;schedule()}else{targetX=0;targetY=0;aimTurnX=0;aimTurnY=0;pointerInside=false;impulseX=0;impulseY=0;motionX=0;motionY=0;turnX=0;turnY=0;pause();}
      },{threshold:.005}).observe(hero);
    }
    // A interação pertence exclusivamente à aba Início: fora do #inicio
    // o cursor não altera o campo de partículas.
    function resetPointer(){
      pointerInside=false;impulseX=0;impulseY=0;
      targetX=0;targetY=0;aimTurnX=0;aimTurnY=0;
      if(inView&&!document.hidden)schedule();
    }
    hero.addEventListener('pointermove',onPointer,{passive:true});
    hero.addEventListener('pointerleave',resetPointer,{passive:true});
    hero.addEventListener('pointercancel',resetPointer,{passive:true});
    window.addEventListener('resize',()=>{resize();schedule()},{passive:true});
    document.addEventListener('visibilitychange',()=>document.hidden?pause():inView&&schedule());
    if('ResizeObserver'in window)new ResizeObserver(()=>{resize();schedule()}).observe(hero);
    resize();schedule();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
  else start();
})();