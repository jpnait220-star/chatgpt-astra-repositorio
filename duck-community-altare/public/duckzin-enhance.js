
(()=>{'use strict';
const d=id=>document.getElementById(id);
const db=window.supabase.createClient(window.DUCKZIN_CONFIG.url,window.DUCKZIN_CONFIG.key);
const permitted=['zip','jar','exe','msi','apk','7z','rar','dmg','deb','pdf'];
let sending=false;
function notice(msg,kind=''){const el=d('siteStatus');if(el){el.textContent=msg;el.className='site-status '+kind;}}
function selectedChannel(){return document.querySelector('#discordChannels [data-channel].active')?.dataset.channel;}
function chat(){
const el=document.querySelector('.discord-composer');if(!el)return;
el.innerHTML='<form id="siteForm" class="site-form"><textarea id="siteMessage" maxlength="1500" rows="2" required placeholder="Digite sua mensagem para o Discord..." aria-label="Mensagem"></textarea><button type="submit" class="button gold" id="siteSend">Enviar →</button></form><div id="siteStatus" class="site-status">Entre na sua conta do site para participar. Seu nome será identificado na mensagem.</div><div class="site-status">O bot publica mensagens somente em canais públicos. Máximo 1.500 caracteres e intervalo de 12 segundos.</div>';
d('siteForm').addEventListener('submit',async ev=>{
ev.preventDefault();if(sending)return;
const text=d('siteMessage').value.trim(),channel=selectedChannel();
if(!channel)return notice('Escolha um canal público primeiro.','error');
if(text.length<1||text.length>1500)return notice('A mensagem deve ter de 1 a 1500 caracteres.','error');
const auth=await db.auth.getUser();
if(!auth.data.user){notice('Faça login para enviar mensagens.','error');d('accountButton').click();return;}
sending=true;d('siteSend').disabled=true;notice('Enviando para o bot...');
try{
const res=await db.from('discord_outbox').insert({channel_id:channel,sender_id:auth.data.user.id,body:text}).select('id').single();
if(res.error)throw res.error;
d('siteMessage').value='';notice('Mensagem recebida! Aguardando o bot...', 'ok');
checkStatus(res.data.id);
}catch(e){notice('Não foi possível enviar: '+e.message,'error');}
finally{sending=false;d('siteSend').disabled=false;}
});
d('siteMessage').addEventListener('keydown',ev=>{if(ev.key==='Enter'&&!ev.shiftKey&&!ev.isComposing){ev.preventDefault();d('siteForm').requestSubmit();}});
}
async function checkStatus(id){for(let i=0;i<10;i++){await new Promise(r=>setTimeout(r,3200));const r=await db.from('discord_outbox').select('status,error').eq('id',id).maybeSingle();if(r.error||!r.data)return;if(r.data.status==='sent')return notice('Publicado no Discord! 🦆','ok');if(r.data.status==='failed')return notice('Não foi possível publicar: '+(r.data.error||'confira as permissões do bot'),'error');}notice('Sua mensagem está na fila. O bot precisa estar online para enviá-la.');}
function fileStatus(el,msg){el.textContent=msg;el.className='site-file-msg';}
async function tusLibrary(){if(window.tus?.Upload)return;await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/tus-js-client@4.3.1/dist/tus.min.js';s.onload=()=>window.tus?.Upload?resolve():reject(Error('Biblioteca TUS indisponível'));s.onerror=()=>reject(Error('Falha ao baixar biblioteca de upload'));document.head.appendChild(s);});}
async function upload(file,onProgress){
if(!file.size||file.size>52428800)throw Error('Arquivos de até 50 MB.');
const ext=file.name.toLowerCase().split('.').pop();if(!permitted.includes(ext))throw Error('Formato permitido: '+permitted.join(', '));
const a=await db.auth.getUser();if(!a.data.user)throw Error('Entre na conta administradora.');
const role=await db.rpc('is_duckzin_admin');if(role.error||role.data!==true)throw Error('Somente o administrador pode publicar arquivos.');
const filename=file.name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-zA-Z0-9._-]/g,'_').slice(0,90);
const path=a.data.user.id+'/'+Date.now()+'-'+Math.random().toString(36).slice(2,9)+'-'+filename;
if(file.size<=6*1024*1024){
const r=await db.storage.from('project-files').upload(path,file,{cacheControl:'3600',upsert:false,contentType:file.type||'application/octet-stream'});
if(r.error)throw r.error;onProgress(100);
}else{
await tusLibrary();const session=(await db.auth.getSession()).data.session;if(!session)throw Error('Sessão expirada.');
await new Promise((resolve,reject)=>{
const uploader=new window.tus.Upload(file,{endpoint:window.DUCKZIN_CONFIG.url.replace('.supabase.co','.storage.supabase.co')+'/storage/v1/upload/resumable',retryDelays:[0,3000,5000,10000,20000],headers:{authorization:'Bearer '+session.access_token,apikey:window.DUCKZIN_CONFIG.key},uploadDataDuringCreation:true,removeFingerprintOnSuccess:true,metadata:{bucketName:'project-files',objectName:path,contentType:file.type||'application/octet-stream',cacheControl:'3600'},chunkSize:6*1024*1024,onProgress:(a,b)=>onProgress(Math.floor(100*a/b)),onError:reject,onSuccess:resolve});
uploader.findPreviousUploads().then(p=>{if(p.length)uploader.resumeFromPreviousUpload(p[0]);uploader.start();}).catch(reject);
});
}
return db.storage.from('project-files').getPublicUrl(path).data.publicUrl;
}
function adminEnhance(){
const form=d('projectForm');if(!form||form.dataset.siteEnhance)return;form.dataset.siteEnhance='1';
const link=form.querySelector('input[name="download_url"]');if(!link)return;
const box=document.createElement('div');box.className='site-file-box';
box.innerHTML='<b>📦 Upload direto do projeto</b><small>Arquivos .zip, .jar, .exe, .msi, .apk, .7z, .rar, .dmg, .deb ou .pdf, até 50 MB. Aguarde o upload terminar e depois clique em Salvar projeto.</small><input type="file" accept=".zip,.jar,.exe,.msi,.apk,.7z,.rar,.dmg,.deb,.pdf" aria-label="Arquivo do projeto"><progress max="100" value="0" hidden></progress><div class="site-file-msg">Ou utilize o link de download externo acima.</div>';
link.insertAdjacentElement('afterend',box);
const file=box.querySelector('input'),bar=box.querySelector('progress'),info=box.querySelector('.site-file-msg'),save=form.querySelector('button[type="submit"]');
let active=false;
form.addEventListener('submit',ev=>{if(active){ev.preventDefault();ev.stopImmediatePropagation();fileStatus(info,'Espere o upload terminar antes de salvar.');}},true);
file.addEventListener('change',async()=>{
if(!file.files?.length||active)return;
active=true;file.disabled=true;if(save)save.disabled=true;bar.hidden=false;bar.value=0;fileStatus(info,'Preparando upload...');
try{const result=await upload(file.files[0],pct=>{bar.value=pct;fileStatus(info,'Enviando arquivo: '+pct+'%');});link.value=result;fileStatus(info,'Arquivo enviado! Agora clique em Salvar projeto.');}
catch(e){fileStatus(info,'Falha: '+e.message);info.classList.add('error');}
finally{active=false;file.disabled=false;if(save)save.disabled=false;}
});
}
function start(){chat();const modal=d('modalContents');if(modal){new MutationObserver(adminEnhance).observe(modal,{childList:true,subtree:true});adminEnhance();}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
