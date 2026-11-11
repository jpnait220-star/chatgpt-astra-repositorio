/* DuckzinCommunity - catálogo de versões e downloads (sem chave secreta). */
(()=>{
 'use strict';

  // Mantém o identificador interno no Storage, mas entrega o nome original ao baixar.
  const duckDownloadStoragePath=/\/storage\/v1\/object\/(?:public|sign|authenticated)\/project-files\//;
  function duckCorrectDownloadName(anchor){
    if(!anchor || !anchor.href)return;
    try{
      const url=new URL(anchor.href,location.href);
      const host=url.hostname.toLowerCase();
      if(!(host.endsWith('.supabase.co')||host.endsWith('.storage.supabase.co')))return;
      if(!duckDownloadStoragePath.test(url.pathname))return;
      const internal=decodeURIComponent(url.pathname.split('/').pop()||'');
      const standard=internal.match(/^\d{10,17}[-_][a-z0-9]{7,10}[-_](.+)$/i);
      const original=standard?standard[1]:internal.replace(/^\d{10,17}[-_]?/,'');
      const chosen=String(anchor.dataset?.duckFilename||original||internal)
        .split(/[\/\\]/).pop().replace(/[<>:"|?*\x00-\x1f]/g,'_').trim().slice(0,150);
      if(chosen){url.searchParams.set('download',chosen);anchor.href=url.href;}
    }catch(e){console.warn('[DuckDownloads] Nome de download não ajustado',e?.message||e);}
  }
  function duckFixLinkFromEvent(e){
    if(e.type==='keydown'&&e.key!=='Enter')return;
    const el=e.target?.closest?.('a[href]');
    if(el)duckCorrectDownloadName(el);
  }
  for(const type of ['pointerdown','click','auxclick','keydown'])
    document.addEventListener(type,duckFixLinkFromEvent,true);

 const C=window.DUCKZIN_CONFIG;
 if(!C?.url||!C?.key||!window.supabase){console.warn('[DuckVersions] Configuração indisponível.');return;}
 const db=window.supabase.createClient(C.url,C.key);
 const $=id=>document.getElementById(id);
 const state={projects:new Map(),versions:new Map(),current:null,adminProject:null,busy:false,ready:false};
 const safeURL=x=>{try{const u=new URL(String(x||''));return u.protocol==='https:'?u.href:null}catch{return null}};
 const node=(tag,className,text)=>{const e=document.createElement(tag);if(className)e.className=className;if(text!==undefined)e.textContent=String(text);return e};
 const fmtDate=x=>{const d=new Date(x);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat('pt-BR',{day:'2-digit',month:'2-digit',year:'numeric'}).format(d):''};
 const css=`
 .duck-version-picker{display:none!important}
 .dvm-trigger{position:relative;z-index:3;display:flex;gap:8px;align-items:center;justify-content:center;width:100%;border:1px solid #e5bf52;background:linear-gradient(120deg,#e5b832,#ffd96f);color:#191508;font-weight:800;border-radius:11px;padding:12px 14px;cursor:pointer;font:800 13px 'DM Sans',sans-serif;margin-top:12px;box-shadow:0 4px 24px #f1bd2830}
 .dvm-trigger:hover{filter:brightness(1.07);transform:translateY(-1px)}
 .dvm-admin-open{border:1px solid #c99b32;background:#302617;color:#ffe19b;padding:9px 12px;border-radius:9px;font-weight:750;cursor:pointer;white-space:nowrap}
 .duck-source-open{font-weight:800!important}
 .dvm-overlay[hidden]{display:none!important}
 .dvm-overlay{position:fixed;inset:0;z-index:2147483000;display:grid;place-items:center;background:#03050be0;backdrop-filter:blur(9px);padding:16px;overflow:auto}
 .dvm-window{width:min(100%,630px);max-height:min(89vh,820px);overflow:auto;background:linear-gradient(165deg,#202127,#111318);border:1px solid #67562f;border-radius:19px;box-shadow:0 28px 100px #000a;padding:21px;color:#f9f7ef;font:14px 'DM Sans',sans-serif}
 .dvm-head{display:flex;justify-content:space-between;gap:15px;align-items:flex-start;margin-bottom:14px}
 .dvm-head h3{margin:5px 0 8px;font:800 23px 'Space Grotesk',sans-serif;color:#fff}
 .dvm-head p{margin:0;color:#b8b6b1;line-height:1.5}
 .dvm-kicker{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:#f2c456;font-weight:800}
 .dvm-close{background:#2e3036;color:white;border:1px solid #4b4e54;border-radius:10px;min-width:36px;height:36px;cursor:pointer;font-size:20px}
 .dvm-list{display:grid;gap:9px;margin-top:18px}
 .dvm-version{display:flex;align-items:center;gap:14px;justify-content:space-between;padding:14px;border:1px solid #414248;border-radius:13px;background:#181a20}
 .dvm-version:hover{border-color:#c5a24f;background:#222124}
 .dvm-detail{min-width:0;flex:1}.dvm-detail strong{display:block;font-size:15px;margin-bottom:5px}.dvm-detail small{display:block;color:#aeb0b9;word-break:break-word;line-height:1.4}
 .dvm-download{display:inline-flex;align-items:center;gap:7px;padding:10px 13px;background:#f5c94d;color:#1b1709;text-decoration:none;font-weight:800;border-radius:10px;white-space:nowrap}
 .dvm-download:hover{background:#ffdf80}.dvm-empty{padding:20px;color:#d0c6b1;text-align:center}
 .dvm-fields{display:grid;gap:12px;margin-top:12px}.dvm-fields label{display:grid;gap:6px;font-weight:700;font-size:12px;color:#ddd0aa}
 .dvm-fields input{width:100%;min-width:0;box-sizing:border-box;background:#121419;border:1px solid #5a5549;border-radius:10px;padding:12px;color:#fff;outline:none;font-size:14px}
 .dvm-fields input:focus{border-color:#ebc65a}.dvm-save{background:#f4c953;color:#1c190b;padding:12px;border:none;border-radius:10px;font-weight:800;cursor:pointer}
 .dvm-save:disabled{opacity:.5;cursor:wait}.dvm-info{font-size:12px;line-height:1.5;color:#b4b6c2;margin:0}
 .dvm-manager-row{display:flex;align-items:center;gap:9px;margin:8px 0;padding:10px;background:#17191e;border-radius:9px}
 .dvm-manager-row span{flex:1;min-width:0;overflow-wrap:anywhere}.dvm-remove{border:1px solid #a94e4e;background:#3a1818;color:#ffd0d0;padding:7px 10px;border-radius:8px;cursor:pointer}
 @media(max-width:470px){.dvm-window{padding:15px}.dvm-version{flex-direction:column;align-items:stretch}.dvm-download{justify-content:center}}
 `;
 function style(){if($('dvm-style'))return;const s=node('style');s.id='dvm-style';s.textContent=css;document.head.append(s)}
 function overlay(){if($('dvm-overlay'))return $('dvm-overlay');const ov=node('div','dvm-overlay');ov.id='dvm-overlay';ov.hidden=true;ov.setAttribute('role','presentation');
  const box=node('section','dvm-window');box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label','Selecionar versão');
  ov.append(box);document.body.append(ov);ov.addEventListener('click',e=>{if(e.target===ov)close()});return ov;}
 function close(){const ov=$('dvm-overlay');if(ov)ov.hidden=true;state.current=null;state.adminProject=null;document.body.style.overflow='';}
 function show(title,subtitle,isAdmin=false){const ov=overlay();const panel=ov.querySelector('.dvm-window');panel.replaceChildren();const h=node('div','dvm-head');const left=node('div');left.append(node('span','dvm-kicker',isAdmin?'👑 Gerenciar versões':'🦆 DUCKZINCOMMUNITY • DOWNLOADS'),node('h3','',title),node('p','',subtitle));const closeBtn=node('button','dvm-close','×');closeBtn.type='button';closeBtn.title='Fechar';closeBtn.addEventListener('click',close);h.append(left,closeBtn);panel.append(h);ov.hidden=false;document.body.style.overflow='hidden';closeBtn.focus();return panel;}
 async function reload(){
  const [p,v]=await Promise.all([
   db.from('projects').select('id,title,category,version,download_url').limit(250),
   db.from('project_versions').select('id,project_id,version_label,file_name,file_url,sort_order,created_at').order('sort_order',{ascending:true}).order('created_at',{ascending:false}).limit(1500)
  ]);
  if(p.error||v.error){console.warn('[DuckVersions] Falha ao consultar dados:',p.error?.message||v.error?.message);return false;}
  state.projects=new Map((p.data||[]).map(x=>[x.id,x]));const m=new Map();for(const x of v.data||[]){if(!m.has(x.project_id))m.set(x.project_id,[]);m.get(x.project_id).push(x)}state.versions=m;state.ready=true;paintCards();paintAdmin();return true;
 }
 function optionsFor(id){const p=state.projects.get(id);if(!p)return [];
  const versions=(state.versions.get(id)||[]).filter(x=>safeURL(x.file_url));
  if(versions.length)return versions;
  const legacy=safeURL(p.download_url);
  return legacy?[{id:'original',project_id:id,version_label:p.version||'Versão atual',file_name:p.title||'Download',file_url:legacy}]:[];
 }
 function openDownload(id){const project=state.projects.get(id);if(!project)return;state.current=id;const versions=optionsFor(id);
  const panel=show('⬇ '+(project.title||'Projeto'),'Escolha a versão que deseja baixar. Você pode voltar e selecionar outra a qualquer momento.');
  const listing=node('div','dvm-list');if(!versions.length)listing.append(node('div','dvm-empty','📭 Nenhuma versão com download disponível ainda.'));
  for(const ver of versions){const url=safeURL(ver.file_url);if(!url)continue;const card=node('div','dvm-version');const desc=node('div','dvm-detail');desc.append(node('strong','',`📦 ${ver.version_label}`),node('small','',`📄 ${ver.file_name||'Arquivo de download'}`));const a=node('a','dvm-download','⬇ Baixar');a.href=url;a.dataset.duckFilename=ver.file_name||'';a.target='_blank';a.rel='noopener noreferrer';a.dataset.dvmAllowed='1';a.setAttribute('aria-label','Baixar '+(ver.version_label||'versão'));card.append(desc,a);listing.append(card)}panel.append(listing);
 }
 function paintCards(){const root=$('projectGrid');if(!root||!state.ready)return;
  for(const card of root.querySelectorAll('.project-card')){const el=card.querySelector('[data-project]');const id=el?.getAttribute('data-project');if(!id||!state.projects.has(id))continue;
   const versions=optionsFor(id);let btn=card.querySelector('.dvm-trigger');if(!versions.length){btn?.remove();continue;}
   if(!btn){btn=node('button','dvm-trigger');btn.type='button';btn.dataset.dvProject=id;btn.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();openDownload(id)});(card.querySelector('.project-body')||card).append(btn)}
   const count=(state.versions.get(id)||[]).filter(x=>safeURL(x.file_url)).length;const txt=count>1?`📦 Selecionar versão (${count})`:'📦 Selecionar versão';if(btn.textContent!==txt)btn.textContent=txt;
  }
 }
 // O administrador já tem gerenciador nativo para arquivos/links e upload.
 // Tornamos o acesso mais claro e criamos alternativa caso a versão do site não o tenha.
 function paintAdmin(){const list=$('pubItems');if(!list)return;
  for(const row of list.querySelectorAll('.pub-project-row')){
   const edit=row.querySelector('[data-act="edit"][data-id]');const id=edit?.dataset.id;if(!id)continue;
   const original=row.querySelector('.duck-source-open');if(original){row.querySelector('.dvm-admin-open')?.remove();if(original.textContent!=='➕ Adicionar versão')original.textContent='➕ Adicionar versão';continue;}
   let b=row.querySelector('.dvm-admin-open');if(b)continue;b=node('button','dvm-admin-open','➕ Adicionar versão');b.type='button';b.addEventListener('click',()=>void openAdmin(id));(row.querySelector('.pub-actions')||row).prepend(b);
  }
 }
 async function mustAdmin(){const [user,role]=await Promise.all([db.auth.getUser(),db.rpc('is_duckzin_admin')]);if(!user.data?.user||role.error||role.data!==true)throw Error('Faça login como administrador para adicionar versões.');}
 async function openAdmin(id){try{await mustAdmin();await reload();state.adminProject=id;const p=state.projects.get(id);if(!p)throw Error('Projeto não encontrado.');
  const panel=show('➕ Adicionar versão • '+p.title,'Cadastre o nome da versão, o nome do arquivo e o link HTTPS do download.',true);
  const form=node('form','dvm-fields');const defs=[['version','Nome da versão','Ex.: 1.21.4 • Fabric'],['file','Nome do arquivo','Ex.: DuckClientZ-1.21.4.jar'],['url','Link do download (HTTPS)','https://...']];
  for(const [name,label,placeholder] of defs){const l=node('label','',label);const input=node('input');input.name=name;input.placeholder=placeholder;input.required=true;input.maxLength=name==='version'?60:name==='file'?160:2000;input.type=name==='url'?'url':'text';l.append(input);form.append(l)}
  const save=node('button','dvm-save','✅ Salvar versão');save.type='submit';form.append(save);const message=node('p','dvm-info','Você pode adicionar quantas versões desejar. Links externos devem começar com https://.');form.append(message);panel.append(form);
  const list=node('div','dvm-list');panel.append(node('h4','', 'Versões cadastradas'),list);
  const draw=()=>{list.replaceChildren();const arr=state.versions.get(id)||[];if(!arr.length)list.append(node('p','dvm-info','Nenhuma versão adicional cadastrada.'));for(const item of arr){const wrap=node('div','dvm-manager-row');wrap.append(node('span','',`📦 ${item.version_label}  •  ${item.file_name}`));const del=node('button','dvm-remove','Excluir');del.type='button';del.addEventListener('click',async()=>{if(!confirm('Excluir a versão '+item.version_label+'?'))return;try{await mustAdmin();const r=await db.from('project_versions').delete().eq('id',item.id).eq('project_id',id);if(r.error)throw r.error;await reload();draw();}catch(err){alert('Não foi possível excluir: '+err.message)}});wrap.append(del);list.append(wrap)}};
  draw();form.addEventListener('submit',async e=>{e.preventDefault();if(state.busy)return;state.busy=true;save.disabled=true;try{await mustAdmin();const version=form.elements.version.value.trim(),name=form.elements.file.value.trim(),url=safeURL(form.elements.url.value.trim());if(!version||!name||!url)throw Error('Preencha os três campos e informe um link HTTPS válido.');const r=await db.from('project_versions').insert({project_id:id,version_label:version,file_name:name,file_url:url,sort_order:0});if(r.error)throw r.error;form.reset();message.textContent='✅ Versão adicionada! Ela já aparecerá no seletor de download.';await reload();draw();}catch(err){message.textContent='❌ '+(err.message||err)}finally{state.busy=false;save.disabled=false}});
 }catch(err){alert('⚠️ '+(err.message||err))}}
 function init(){style();overlay();const grid=$('projectGrid'),admin=$('pubItems');if(grid){const mo=new MutationObserver(()=>paintCards());mo.observe(grid,{childList:true,subtree:true});}if(admin){const mo=new MutationObserver(()=>paintAdmin());mo.observe(admin,{childList:true,subtree:true});}
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('dvm-overlay')?.hidden)close()});
  // Também bloqueia o antigo botão de download direto, incluindo na janela de detalhes.
  document.addEventListener('click',e=>{const link=e.target.closest?.('a[href]');if(!link||link.dataset.dvmAllowed==='1'||link.closest('#publicar'))return;let href;try{href=new URL(link.href,document.baseURI).href}catch{return}if(!safeURL(href))return;for(const [id,p] of state.projects){if(safeURL(p.download_url)===href||(state.versions.get(id)||[]).some(x=>safeURL(x.file_url)===href)){e.preventDefault();e.stopImmediatePropagation();openDownload(id);return}}},true);
  setTimeout(()=>{paintAdmin();paintCards()},1000);void reload();setInterval(()=>void reload(),90000);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();