// DuckCleans 1.3 — magnetic effects with slow return on release and leave.
// This module intentionally changes presentation only.
const reduced=matchMedia('(prefers-reduced-motion:reduce)');
const fine=matchMedia('(pointer:fine) and (hover:hover)');
const SELECTOR='button:not(:disabled),.stat';
let active=null,frame=0,point=null;
function targetFor(event){return event.target instanceof Element ? event.target.closest(SELECTOR) : null;}
function neutral(el){
 if(!el)return;
 el.classList.remove('magnetic-hover','magnetic-pressed');
 el.style.setProperty('--magnet-x','0px');
 el.style.setProperty('--magnet-y','0px');
 el.style.setProperty('--magnet-scale','1');
 el.style.setProperty('--tilt-x','0deg');
 el.style.setProperty('--tilt-y','0deg');
}
function reset(){
 if(frame)cancelAnimationFrame(frame); frame=0;point=null;
 if(active)neutral(active);
 active=null;
}
function paint(){
 frame=0;
 if(!active||!active.isConnected||!point)return;
 const r=active.getBoundingClientRect();
 if(!r.width||!r.height)return;
 const x=Math.max(-1,Math.min(1,(point.x-r.left-r.width/2)/(r.width/2)));
 const y=Math.max(-1,Math.min(1,(point.y-r.top-r.height/2)/(r.height/2)));
 const isCard=active.classList.contains('stat');
 active.style.setProperty('--magnet-x',(x*(isCard?1.5:4)).toFixed(2)+'px');
 active.style.setProperty('--magnet-y',(y*(isCard?1.5:2.6)).toFixed(2)+'px');
 if(isCard) {
  active.style.setProperty('--tilt-x',(-y*1.8).toFixed(2)+'deg');
  active.style.setProperty('--tilt-y',(x*1.8).toFixed(2)+'deg');
 }
}
function requestPaint(p){
 point={x:p.clientX,y:p.clientY};
 if(!frame)frame=requestAnimationFrame(paint);
}
export function fadeIn(element){
 if(reduced.matches||!element)return;
 element.animate([{opacity:0,transform:'translateY(7px)'},{opacity:1,transform:'translateY(0)'}],{duration:280,easing:'cubic-bezier(.16,1,.3,1)'});
}
export function initMotion(){
 document.addEventListener('pointermove',e=>{
  if(reduced.matches||!fine.matches||e.pointerType!=='mouse')return;
  const el=targetFor(e);
  if(el!==active){reset();if(el){active=el;el.classList.add('motion-surface','magnetic-hover');}}
  if(active&&!active.classList.contains('magnetic-pressed'))requestPaint(e);
 },{passive:true});
 document.addEventListener('pointerdown',e=>{
  if(e.button!==0||!fine.matches||reduced.matches)return;
  const el=targetFor(e);
  if(!el||el.classList.contains('stat'))return;
  if(active!==el){reset();active=el;el.classList.add('motion-surface');}
  active.classList.remove('magnetic-hover');
  active.classList.add('magnetic-pressed');
  active.style.setProperty('--magnet-scale','.969');
 },{passive:true});
 document.addEventListener('pointerup',e=>{
  if(e.button!==0)return;
  // Neutral values are applied AFTER removing fast-moving classes.
  if(active&&active.classList.contains('magnetic-pressed'))reset();
 },{passive:true});
 document.addEventListener('pointerout',e=>{
  if(active&&!active.contains(e.relatedTarget))reset();
 },{passive:true});
 document.addEventListener('pointercancel',reset,{passive:true});
 document.addEventListener('scroll',reset,true);
 window.addEventListener('blur',reset);
 window.addEventListener('resize',reset);
 reduced.addEventListener?.('change',reset);
}
