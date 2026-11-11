/* DuckzinCommunity • Descrições em texto normal e ordenação manual dos cards.
   Não interpreta Markdown/Discord. Mantém o painel de organização existente. */
(()=>{
 'use strict';
 if(window.__duckMarkdownCardOrderLoaded)return;
 window.__duckMarkdownCardOrderLoaded=true;
 const $=id=>document.getElementById(id);
 const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=String(text);return e};
 const css=`
 /* Descrição normal, curta e legível no card; mantém o restante do visual. */
 #projectGrid .project-card{align-self:start;min-height:0!important}
 #projectGrid .duck-plain-description{
   color:#bec2cc;font-size:13px;line-height:1.45;overflow-wrap:anywhere;
   white-space:pre-line;display:-webkit-box;-webkit-box-orient:vertical;
   -webkit-line-clamp:3;line-clamp:3;overflow:hidden;
 }
 .duck-sort-admin{margin:10px 0 17px;border:1px solid #66542d;border-radius:13px;padding:13px;background:#181a20;color:#f0ede5}
 .duck-sort-admin[hidden],.duck-sort-list[hidden]{display:none!important}
 .duck-sort-title{display:flex;gap:12px;justify-content:space-between;align-items:center;flex-wrap:wrap}
 .duck-sort-title strong{color:#ffe099}.duck-sort-title p{color:#adb0bb;font-size:12px;margin:5px 0 0}
 .duck-sort-toggle,.duck-sort-save,.duck-sort-control{border:1px solid #776439;color:#fff2cc;background:#30291b;border-radius:9px;padding:9px 11px;cursor:pointer;font-weight:750}
 .duck-sort-toggle:hover,.duck-sort-save:hover,.duck-sort-control:hover{border-color:#f4cf73;background:#42331c}
 .duck-sort-list{padding:0;list-style:none;margin:12px 0;display:grid;gap:8px}
 .duck-sort-item{display:flex;align-items:center;gap:9px;background:#101218;border:1px solid #43444a;border-radius:11px;padding:9px 10px}
 .duck-sort-item[draggable='true']{cursor:grab}.duck-sort-item.duck-dragging{opacity:.4}
 .duck-sort-grip{color:#bca772}.duck-sort-label{flex:1;min-width:0;overflow-wrap:anywhere;font-weight:800;font-size:13px}
 .duck-sort-label small{display:block;color:#a6a7b0;font-weight:500;margin-top:3px}
 .duck-sort-control{font-size:14px;min-width:35px;padding:7px 9px}
 .duck-sort-save{background:#eec456;color:#1d1607;min-width:170px}.duck-sort-save:disabled{opacity:.5;cursor:wait}
 .duck-sort-feedback{color:#e9d29a;font-size:12px;margin:8px 0 0}

 `;
 const style=el('style');style.id='duckProjectOrderStyle';style.textContent=css;document.head.append(style);
 let db=null,projects=[],cardsTimer=0,checking=false,isAdmin=false,sortActive=false,sortItems=[];
 function projectId(card){return card.querySelector('[data-project]')?.getAttribute('data-project')||card.getAttribute('data-project')||card.dataset.projectId}
 function norm(s){return String(s||'').replace(/\s+/g,' ').trim()}
 // Limpa símbolos de formatação no VISUAL sem alterar a descrição salva no banco.
 function plainDescription(source){
   return String(source??'').replace(/\r\n?/g,'\n')
     .replace(/^\s*```[^\n]*$/gm,'')
     .replace(/^\s{0,3}#{1,6}\s+/gm,'')
     .replace(/^\s*>\s?/gm,'')
     .replace(/^\s*[-+*]\s+/gm,'• ')
     .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'$1')
     .replace(/\*\*\*([^\n]+?)\*\*\*/g,'$1')
     .replace(/\*\*([^\n]+?)\*\*/g,'$1')
     .replace(/__([^\n]+?)__/g,'$1')
     .replace(/~~([^\n]+?)~~/g,'$1')
     .replace(/\|\|([^\n]+?)\|\|/g,'$1')
     .replace(/`([^\n]+?)`/g,'$1')
     .replace(/\*([^\n*]+?)\*/g,'$1')
     .replace(/(^|\s)_([^\n_]+?)_(?=\s|$)/gm,'$1$2')
     .replace(/\n{3,}/g,'\n\n').trim();
 }
 function descriptionTarget(card,description){
   const body=card.querySelector('.project-body')||card;
   const candidate=[...body.querySelectorAll('.project-desc,.project-description,.description,[class*="description"],p,small,div,span')];
   const normalized=norm(description);let partial=null;
   for(const node of candidate){
     if(node.closest('.dvm-trigger,.duck-version-picker,.duck-sort-admin'))continue;
     if(node.matches('button,a,input,textarea')||node.querySelector('button,a,input,textarea'))continue;
     const val=norm(node.textContent);
     if(val===normalized && (!node.children.length||node.children.length===1))return node;
     if(!partial&&val.length>=24&&normalized.startsWith(val.replace(/\.{3}$|…$/,''))&&val.length<normalized.length+5)partial=node;
   }
   return partial;
 }
 function applyCatalog(){
   const grid=$('projectGrid');if(!grid||!projects.length)return;
   const byId=new Map(projects.map(p=>[p.id,p]));
   const cards=[...grid.querySelectorAll(':scope > .project-card')];
   for(const card of cards){
     const id=projectId(card),p=byId.get(id);if(!p||!p.description)continue;
     const previous=card.querySelector('[data-duck-plain-id="'+id+'"]');
     if(previous && previous.dataset.plainSource===p.description)continue;
     const target=previous||descriptionTarget(card,p.description);if(!target)continue;
     target.textContent=plainDescription(p.description);
     target.classList.add('duck-plain-description');
     target.dataset.duckPlainId=id;
     target.dataset.plainSource=p.description;
   }
   const rank=new Map(projects.map((p,i)=>[p.id,i]));
   const sorted=[...cards].sort((a,b)=>(rank.get(projectId(a))??99999)-(rank.get(projectId(b))??99999));
   if(sorted.some((c,i)=>c!==cards[i]))for(const card of sorted)grid.append(card);
 }
 function scheduleCatalog(){if(cardsTimer)return;cardsTimer=requestAnimationFrame(()=>{cardsTimer=0;applyCatalog()})}
 async function loadProjects(){
   if(!db)return;
   const response=await db.from('projects').select('id,title,category,description,sort_order,created_at')
     .order('sort_order',{ascending:true}).order('created_at',{ascending:false}).limit(250);
   if(response.error){console.warn('[Duckzin] Erro ao buscar ordem dos projetos',response.error.message);return}
   projects=response.data||[];scheduleCatalog();if(sortActive)renderSort();
 }
 function setFeedback(message){const out=$('duckSortFeedback');if(out)out.textContent=message}
 function updateSortLocal(){sortItems.forEach((id,i)=>{const p=projects.find(row=>row.id===id);if(p)p.sort_order=(i+1)*100});projects.sort((a,b)=>a.sort_order-b.sort_order);scheduleCatalog()}
 function shift(id,delta){const i=sortItems.indexOf(id),j=i+delta;if(i<0||j<0||j>=sortItems.length)return;
   [sortItems[i],sortItems[j]]=[sortItems[j],sortItems[i]];renderSort();setFeedback('Ordem alterada. Clique em Salvar para guardar.')}
 function renderSort(){const root=$('duckSortList');if(!root||root.hidden)return;
   root.replaceChildren();if(sortItems.length!==projects.length||sortItems.some(id=>!projects.some(p=>p.id===id)))sortItems=projects.map(p=>p.id);
   sortItems.forEach((id,i)=>{
     const p=projects.find(x=>x.id===id);if(!p)return;
     const row=el('li','duck-sort-item');row.draggable=true;row.dataset.id=id;
     const grip=el('span','duck-sort-grip','⠿');grip.title='Arrastar para reorganizar';
     const label=el('div','duck-sort-label',(i+1)+'. '+p.title);label.append(el('small','',p.category));
     const up=el('button','duck-sort-control','↑');up.type='button';up.title='Subir '+p.title;up.disabled=i===0;up.onclick=()=>shift(id,-1);
     const down=el('button','duck-sort-control','↓');down.type='button';down.title='Descer '+p.title;down.disabled=i===sortItems.length-1;down.onclick=()=>shift(id,1);
     row.append(grip,label,up,down);
     row.addEventListener('dragstart',e=>{e.dataTransfer?.setData('text/plain',id);e.dataTransfer.effectAllowed='move';row.classList.add('duck-dragging')});
     row.addEventListener('dragend',()=>row.classList.remove('duck-dragging'));
     row.addEventListener('dragover',e=>{e.preventDefault();e.dataTransfer.dropEffect='move'});
     row.addEventListener('drop',e=>{e.preventDefault();const from=e.dataTransfer.getData('text/plain'),a=sortItems.indexOf(from),b=sortItems.indexOf(id);if(a<0||b<0||a===b)return;sortItems.splice(b,0,sortItems.splice(a,1)[0]);renderSort();setFeedback('Ordem alterada. Clique em Salvar para guardar.')});
     root.append(row);
   });
 }
 function mountAdmin(){const pubItems=$('pubItems');if(!pubItems||$('duckSortAdmin'))return;
   const box=el('section','duck-sort-admin');box.id='duckSortAdmin';box.hidden=true;
   const header=el('div','duck-sort-title');const title=el('div');title.append(el('strong','', '↕ Ordem dos cards'),el('p','', 'Arraste ou use ↑ ↓ para escolher a posição de cada projeto.'));
   const toggle=el('button','duck-sort-toggle','Organizar cards');toggle.type='button';toggle.addEventListener('click',()=>{
     sortActive=!sortActive;list.hidden=!sortActive;save.hidden=!sortActive;toggle.textContent=sortActive?'Fechar organização':'Organizar cards';
     if(sortActive){sortItems=projects.map(p=>p.id);renderSort()}
   });header.append(title,toggle);box.append(header);
   const list=el('ol','duck-sort-list');list.id='duckSortList';list.hidden=true;box.append(list);
   const save=el('button','duck-sort-save','💾 Salvar ordem');save.type='button';save.hidden=true;
   save.addEventListener('click',async()=>{
     if(!isAdmin)return setFeedback('Entre com uma conta de administrador.');
     save.disabled=true;setFeedback('Salvando ordem dos projetos...');
     const result=await db.rpc('reorder_duckzin_projects',{p_project_ids:sortItems});
     if(result.error){setFeedback('❌ Não foi possível salvar: '+result.error.message);save.disabled=false;return}
     updateSortLocal();setFeedback('✅ Ordem salva! Os cards estão organizados para todos os visitantes.');
     save.disabled=false;await loadProjects();
   });box.append(save);
   const feedback=el('p','duck-sort-feedback','');feedback.id='duckSortFeedback';box.append(feedback);
   pubItems.insertAdjacentElement('beforebegin',box);
 }
 async function adminCheck(){if(checking||!db)return;checking=true;
   try{
     if(!($('publicar')&&!$('publicar').hidden)){isAdmin=false;return}
     const r=await db.rpc('is_duckzin_admin');isAdmin=!r.error&&r.data===true;
     const panel=$('duckSortAdmin');if(panel)panel.hidden=!isAdmin;
   }catch{isAdmin=false}finally{checking=false}
 }
 function boot(){const cfg=window.DUCKZIN_CONFIG;if(!window.supabase||!cfg?.url||!cfg?.key){setTimeout(boot,300);return}
   db=window.supabase.createClient(cfg.url,cfg.key);
   mountAdmin();void loadProjects();void adminCheck();
   const grid=$('projectGrid');if(grid)new MutationObserver(scheduleCatalog).observe(grid,{childList:true});
   $('pubShowList')?.addEventListener('click',()=>{mountAdmin();void adminCheck();void loadProjects()});
   $('pubNav')?.addEventListener('click',()=>setTimeout(adminCheck,150));
   db.auth.onAuthStateChange(()=>{setTimeout(adminCheck,250)});
   document.addEventListener('visibilitychange',()=>{if(!document.hidden)void loadProjects()});
   setInterval(()=>{if(!document.hidden){void adminCheck(); if(!$('duckSortAdmin'))mountAdmin()}},18000);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();