window.DUCKZIN_CONFIG={url:"https://meivyvpqsmhsndgafdwy.supabase.co",key:"sb_publishable_bd3X0v_9hJb8HoPTPqtH-Q_Y2Ta5ZCJ"};
;(()=>{
 const resources=['/duckzin-download-versions.js','/duckzin-jelly-particles.js','/duckzin-markdown-card-order.js'];
 for(const path of resources){const element=document.createElement('script');element.src=path;element.async=false;document.head.appendChild(element)}
 const css=`
 .project-card>.duck-white-blade-zone{position:absolute!important;left:0;right:0;bottom:0;top:var(--duck-blade-top,48%);overflow:hidden;pointer-events:none;z-index:8;border-radius:0 0 16px 16px}
 .project-card>.duck-white-blade-zone::before{content:"";position:absolute;top:-30%;bottom:-30%;left:-58%;width:58%;opacity:0;transform:translateX(0) skewX(-19deg);pointer-events:none;will-change:transform,opacity;background:linear-gradient(90deg,transparent,rgba(255,255,255,.02) 12%,rgba(255,255,255,.09) 28%,rgba(255,255,255,.36) 42%,rgba(255,255,255,.8) 50%,rgba(255,255,255,.36) 58%,rgba(255,255,255,.09) 72%,transparent)}
 .project-card:is(:hover,:focus-within)>.duck-white-blade-zone::before{animation:duck-white-blade-travel 6.5s ease-in-out infinite}
 @keyframes duck-white-blade-travel{0%,7%{opacity:0;transform:translateX(0) skewX(-19deg)}13%{opacity:.95}69%{opacity:.95;transform:translateX(300%) skewX(-19deg)}78%,100%{opacity:0;transform:translateX(300%) skewX(-19deg)}}
 @media(hover:none),(prefers-reduced-motion:reduce){.project-card>.duck-white-blade-zone{display:none!important}}
 `;
 const style=document.createElement('style');style.id='duck-white-blade-style';style.textContent=css;document.head.appendChild(style);
 const update=()=>{const grid=document.getElementById('projectGrid');if(!grid)return;
  for(const card of grid.querySelectorAll('.project-card')){let zone=card.querySelector(':scope>.duck-white-blade-zone');
    if(!zone){zone=document.createElement('span');zone.className='duck-white-blade-zone';zone.setAttribute('aria-hidden','true');card.appendChild(zone)}
    const cover=card.querySelector('.project-cover,.project-banner,.project-image,.card-cover');
    const r=card.getBoundingClientRect(),c=cover?.getBoundingClientRect();
    if(r.height>0){let top=c?c.bottom-r.top:r.height*.48;if(!Number.isFinite(top)||top<25||top>r.height-25)top=r.height*.48;
      card.style.setProperty('--duck-blade-top',Math.ceil(top+1)+'px')}
  }
 };
 const mount=()=>{const grid=document.getElementById('projectGrid');if(!grid)return;update();
  let queued=false;new MutationObserver(()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;update()})}).observe(grid,{childList:true});
  window.addEventListener('resize',update,{passive:true});
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
