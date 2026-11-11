/* DuckzinCommunity V3: resilient Discord viewer and publication dashboard. No secret keys are included. */
(()=>{'use strict';
if(!window.supabase || !window.DUCKZIN_CONFIG){console.error('Duckzin V3: Supabase indisponível');return;}
const sb=window.supabase.createClient(window.DUCKZIN_CONFIG.url,window.DUCKZIN_CONFIG.key);
const $=id=>document.getElementById(id);
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const validUrl=v=>{try{let u=new URL(v);return u.protocol==='https:'?u.href:''}catch{return ''}};
const invite='https://discord.gg/QCCXQqGzV';
let guild=null,channels=[],selectedId='',history=[],beforeTime='',older=false;
let generation=0,loadingList=false,busyHistory=false,posting=false,admin=false,activeList='create',projectCache=[];
function setInfo(message,klass=''){$('v3Info').textContent=message;$('v3Info').className='v3-info '+klass}
function errorView(target,text){$(target).innerHTML='<div class="v3-empty"><strong>Não foi possível carregar</strong>'+escapeHTML(text)+'<br><button class="button gold" type="button" id="v3Retry">Tentar novamente</button></div>';const b=$('v3Retry');if(b)b.onclick=()=>loadChannels(true)}
function initChat(){const root=$('duckzinV3Root');if(!root)return;
root.innerHTML=`<aside class="v3-side"><div class="v3-guild"><span id="v3Guild">Discord do Duckzin</span><small id="v3GuildState">Conectando ao servidor...</small></div><div class="v3-chlabel">CANAIS PÚBLICOS</div><div id="v3ChannelList" class="v3-channel-list"><span class="v3-loading">Buscando canais...</span></div><div class="v3-side-footer">🛡 Canais privados não são publicados</div></aside><div class="v3-chat"><div class="v3-bar"><b id="v3Current"># comunidade</b><a id="v3DiscordLink" target="_blank" rel="noopener noreferrer" href="${invite}">Abrir no Discord ↗</a></div><div id="v3Messages" class="v3-messages" role="log" aria-live="polite"><div class="v3-loading">Carregando mensagens...</div></div><div class="v3-input"><form id="v3MessageForm" class="v3-compose"><textarea id="v3Message" maxlength="1500" required rows="2" placeholder="Escreva para o Discord..." aria-label="Sua mensagem"></textarea><button id="v3Send" type="submit" class="button gold">Enviar →</button></form><div id="v3Info" class="v3-info">Entre na sua conta para participar. Suas mensagens aparecem como “via site”.</div></div></div>`;
$('v3MessageForm').addEventListener('submit',sendMessage);
$('v3Message').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();$('v3MessageForm').requestSubmit();}});
loadChannels(true);
setInterval(()=>{if(document.visibilityState==='visible'){loadChannels(false);refreshMessages()}},7000);
}
async function requestTimeout(task,delay=12000){let timer;try{return await Promise.race([task,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Tempo limite atingido')),delay)})])}finally{clearTimeout(timer)}}
async function loadChannels(force){if(loadingList)return;loadingList=true;
try{
const [g,c]=await requestTimeout(Promise.all([sb.from('discord_guilds').select('id,name,icon_url,updated_at').order('updated_at',{ascending:false}).limit(1),sb.from('discord_channels').select('id,guild_id,name,position,kind').order('position',{ascending:true})]));
if(g.error)throw g.error;if(c.error)throw c.error;
guild=g.data?.[0]||null;channels=(c.data||[]).filter(x=>!guild||x.guild_id===guild.id);
$('v3Guild').textContent=guild?.name||'Discord do Duckzin';$('v3GuildState').textContent=channels.length?channels.length+' canais públicos conectados':'Aguardando canais do bot';
if(!channels.length){$('v3ChannelList').innerHTML='<div class="v3-loading">Nenhum canal público sincronizado.</div>';$('v3Messages').innerHTML='<div class="v3-empty"><strong>Discord aguardando canais</strong>Mantenha o bot online e confira suas permissões de leitura.</div>';return;}
const oldId=selectedId;
if(!channels.some(x=>x.id===selectedId))selectedId=channels[0].id;
renderChannels();
if(oldId!==selectedId||force){await chooseChannel(selectedId,true)}
}catch(e){$('v3GuildState').textContent='Erro de conexão';if(!channels.length){$('v3ChannelList').innerHTML='<div class="v3-loading">Falha ao consultar canais.</div>';errorView('v3Messages',e.message||'Falha de conexão')}}finally{loadingList=false;}
}
function renderChannels(){const root=$('v3ChannelList');root.innerHTML='';for(const channel of channels){const btn=document.createElement('button');btn.type='button';btn.className='v3-channel'+(channel.id===selectedId?' active':'');btn.innerHTML='<span class="hash">#</span>'+escapeHTML(channel.name);btn.addEventListener('click',()=>chooseChannel(channel.id,true));root.appendChild(btn);}}
async function chooseChannel(id,reset){const ch=channels.find(x=>x.id===id);if(!ch)return;selectedId=ch.id;generation++;busyHistory=false;history=[];beforeTime='';older=false;
$('v3Current').textContent='# '+ch.name;const url=`https://discord.com/channels/${encodeURIComponent(ch.guild_id)}/${encodeURIComponent(ch.id)}`;$('v3DiscordLink').href=url;
renderChannels();$('v3Messages').innerHTML='<div class="v3-loading">Carregando mensagens de #'+escapeHTML(ch.name)+'...</div>';
await loadMessages(true);
}
async function loadMessages(reset){if(!selectedId||busyHistory)return;const ref=selectedId,seq=generation;busyHistory=true;
try{let q=sb.from('discord_messages').select('id,guild_id,channel_id,author_name,author_avatar_url,content,reply_to,sent_at').eq('channel_id',ref).order('sent_at',{ascending:false}).limit(40);
if(!reset&&beforeTime)q=q.lt('sent_at',beforeTime);
const {data,error}=await requestTimeout(q,12000);if(error)throw error;if(ref!==selectedId||seq!==generation)return;
const chunk=(data||[]).reverse();const count=chunk.length;
if(reset){history=chunk}else{const ids=new Set(history.map(x=>x.id));history=[...chunk.filter(x=>!ids.has(x.id)),...history]}
older=count===40;beforeTime=history[0]?.sent_at||'';
renderMessages(reset);
}catch(e){if(ref===selectedId&&seq===generation)errorView('v3Messages',e.message||'Falha ao carregar mensagens')}
finally{busyHistory=false;}
}
function renderMessages(reset){const root=$('v3Messages'),nearBottom=root.scrollHeight-root.scrollTop-root.clientHeight<100;const previousHeight=root.scrollHeight,previousTop=root.scrollTop;root.innerHTML='';
if(!history.length){root.innerHTML='<div class="v3-empty"><strong>Nenhuma mensagem por enquanto</strong>Envie a primeira mensagem por aqui ou pelo Discord.</div>';return;}
if(older){const more=document.createElement('button');more.type='button';more.className='v3-load-more';more.textContent='↑ Mostrar mensagens antigas';more.onclick=()=>loadMessages(false);root.appendChild(more);}
for(const m of history){const box=document.createElement('article');box.className='v3-msg';const avatar=validUrl(m.author_avatar_url);const image=avatar?'<img class="v3-avatar" src="'+escapeHTML(avatar)+'" loading="lazy" alt="Avatar de '+escapeHTML(m.author_name)+'">':'<span class="v3-avatar v3-avatar-placeholder">'+escapeHTML((m.author_name||'?').slice(0,2).toUpperCase())+'</span>';const date=new Date(m.sent_at);const time=Number.isNaN(date.valueOf())?'':date.toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
const jump='https://discord.com/channels/'+encodeURIComponent(m.guild_id)+'/'+encodeURIComponent(m.channel_id)+'/'+encodeURIComponent(m.id);
box.innerHTML=image+'<div class="v3-msgtext"><div class="v3-msghead"><b>'+escapeHTML(m.author_name||'Membro')+'</b><time>'+escapeHTML(time)+'</time></div>'+ (m.reply_to?'<div class="v3-info">↳ Em resposta a uma mensagem</div>':'')+'<p>'+escapeHTML(m.content||'[Mensagem sem texto]')+'</p><a class="v3-jump" href="'+jump+'" rel="noopener noreferrer" target="_blank">Ver no Discord ↗</a></div>';
root.appendChild(box);}
if(reset||nearBottom)root.scrollTop=root.scrollHeight;else root.scrollTop=previousTop+Math.max(0,root.scrollHeight-previousHeight);
}
let refreshing=false;
async function refreshMessages(){if(!selectedId||refreshing||busyHistory)return;refreshing=true;const ref=selectedId,seq=generation;
try{const r=await requestTimeout(sb.from('discord_messages').select('id,guild_id,channel_id,author_name,author_avatar_url,content,reply_to,sent_at').eq('channel_id',ref).order('sent_at',{ascending:false}).limit(40));if(r.error)throw r.error;if(selectedId!==ref||seq!==generation)return;
const incoming=(r.data||[]).reverse();if(incoming.length){const prev=JSON.stringify(history.slice(-40));const next=JSON.stringify(incoming);
if(prev!==next){const seen=new Set(history.map(x=>x.id));history=[...history.filter(x=>!incoming.some(v=>v.id===x.id)),...incoming];history=history.slice(-200);renderMessages(false)}}
}catch(e){console.warn('Duckzin V3: tentativa de atualização',e.message)}finally{refreshing=false;}}
async function sendMessage(e){e.preventDefault();if(posting)return;const channel=channels.find(x=>x.id===selectedId);const body=$('v3Message').value.trim();if(!channel)return setInfo('Selecione um canal público.','error');if(!body||body.length>1500)return setInfo('A mensagem precisa ter de 1 a 1.500 caracteres.','error');
try{const auth=await requestTimeout(sb.auth.getUser());if(!auth.data.user){setInfo('Entre na sua conta do site para enviar.','error');$('accountButton')?.click();return;}posting=true;$('v3Send').disabled=true;setInfo('Enviando para o bot...');const r=await requestTimeout(sb.from('discord_outbox').insert({channel_id:channel.id,sender_id:auth.data.user.id,body}).select('id').single());if(r.error)throw r.error;$('v3Message').value='';setInfo('Mensagem na fila do bot. Aguarde alguns segundos...','ok');void waitSent(r.data.id)}catch(err){setInfo('Não foi possível enviar: '+(err.message||'erro desconhecido'),'error')}finally{posting=false;$('v3Send').disabled=false;}}
async function waitSent(id){for(let i=0;i<14;i++){await new Promise(r=>setTimeout(r,2600));try{const r=await requestTimeout(sb.from('discord_outbox').select('status,error').eq('id',id).maybeSingle(),7000);if(r.error||!r.data)return;if(r.data.status==='sent'){setInfo('Mensagem enviada ao Discord! 🦆','ok');return;}if(r.data.status==='failed'){setInfo('O bot não enviou: '+(r.data.error||'Verifique as permissões.'),'error');return;}}catch{}}setInfo('Ainda está na fila. O bot precisa estar online para enviar.');}
function initAdmin(){const a=$('pubNav'),sec=$('publicar');if(!a||!sec)return;a.addEventListener('click',e=>{e.preventDefault();sec.scrollIntoView({behavior:'smooth',block:'start'})});$('pubShowCreate').onclick=()=>switchTab('create');$('pubShowList').onclick=()=>switchTab('list');$('pubReset').onclick=()=>resetForm();$('pubForm').addEventListener('submit',saveProject);
const adminShortcut=$('adminButton');if(adminShortcut)adminShortcut.addEventListener('click',e=>{if(!admin)return;e.preventDefault();e.stopImmediatePropagation();sec.scrollIntoView({behavior:'smooth',block:'start'});},true);
$('pubItems').addEventListener('click',e=>{let btn=e.target.closest('button[data-act]');if(!btn)return;const p=projectCache.find(x=>x.id===btn.dataset.id);if(!p)return;if(btn.dataset.act==='edit'){fillForm(p);switchTab('create');sec.scrollIntoView({behavior:'smooth'})}else if(btn.dataset.act==='delete')void removeProject(p)});
void checkAdmin();sb.auth.onAuthStateChange(()=>{setTimeout(checkAdmin,100)});setInterval(checkAdmin,35000);}
function adminShortcutButton(){return !!$('adminButton');}
let authLock=false;
async function checkAdmin(){if(authLock)return;authLock=true;try{const {data:{user}}=await sb.auth.getUser();const privileged=user?await sb.rpc('is_duckzin_admin'):null;admin=!!(user&&privileged&&!privileged.error&&privileged.data===true);$('publicar').hidden=!admin;$('pubNav').hidden=!admin;if(adminShortcutButton())$('adminButton').textContent=admin?'Publicar':'Painel';if(admin&&!projectCache.length)void loadProjects();}catch(e){admin=false;$('publicar').hidden=true;$('pubNav').hidden=true;}finally{authLock=false;}}
function switchTab(to){activeList=to;$('pubCreate').hidden=to!=='create';$('pubList').hidden=to!=='list';if(to==='list')void loadProjects();}
function resetForm(){$('pubForm').reset();$('pubId').value='';$('pubTitle').textContent='Publicar novo projeto';$('pubSubmit').textContent='Publicar projeto';$('pubStatusText').textContent='';$('pubDownload').value='';$('pubProgress').hidden=true;}
function fillForm(p){resetForm();$('pubId').value=p.id;$('pubName').value=p.title||'';$('pubCategory').value=p.category||'Apps';$('pubVersion').value=p.version||'';$('pubStatus').value=p.status||'Disponível';$('pubDescription').value=p.description||'';$('pubDownload').value=p.download_url||'';$('pubTitle').textContent='Editar '+p.title;$('pubSubmit').textContent='Salvar alterações';}
async function loadProjects(){const r=await sb.from('projects').select('id,title,category,version,status,description,icon_url,banner_url,download_url').order('created_at',{ascending:false});if(r.error){$('pubItems').textContent='Erro: '+r.error.message;return;}projectCache=r.data||[];$('pubItems').innerHTML=projectCache.length?projectCache.map(p=>'<div class="pub-project-row"><div><b>'+escapeHTML(p.title)+'</b><small>'+escapeHTML(p.category)+' · '+escapeHTML(p.version||'Sem versão')+'</small></div><div class="pub-actions"><button type="button" class="button" data-act="edit" data-id="'+escapeHTML(p.id)+'">Editar</button><button type="button" class="button" data-act="delete" data-id="'+escapeHTML(p.id)+'">Excluir</button></div></div>').join(''):'<p>Nenhum projeto publicado.</p>';}
function fileStatus(s,state=''){$('pubStatusText').textContent=s;$('pubStatusText').className='pub-status '+state;}
async function loadTus(){if(window.tus?.Upload)return;await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/tus-js-client@4.3.1/dist/tus.min.js';s.onload=()=>window.tus?.Upload?resolve():reject(Error('Falha ao carregar o componente de upload'));s.onerror=()=>reject(Error('Não foi possível carregar upload de arquivos grandes'));document.head.appendChild(s);});}
async function uploadFile(bucket,file,limit,exts,progress){if(file.size>limit||file.size===0)throw Error('Arquivo vazio ou maior que '+Math.round(limit/1048576)+' MB');if(!exts.includes(file.name.toLowerCase().split('.').pop()))throw Error('Extensão não permitida');const {data:{user},error}=await sb.auth.getUser();if(error||!user)throw Error('Faça login novamente');const role=await sb.rpc('is_duckzin_admin');if(role.error||role.data!==true)throw Error('Sem autorização para publicar');const fname=file.name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^\w.-]/g,'_').slice(0,80);
const path=user.id+'/'+Date.now()+'-'+Math.random().toString(36).slice(2,10)+'-'+fname;
if(file.size<=6*1024*1024){const r=await sb.storage.from(bucket).upload(path,file,{contentType:file.type||'application/octet-stream',cacheControl:'3600',upsert:false});if(r.error)throw r.error;progress?.(100);}else{await loadTus();const session=(await sb.auth.getSession()).data.session;if(!session)throw Error('Sua sessão expirou');const host=new URL(window.DUCKZIN_CONFIG.url).hostname.replace('.supabase.co','.storage.supabase.co');await new Promise((resolve,reject)=>{const u=new window.tus.Upload(file,{endpoint:'https://'+host+'/storage/v1/upload/resumable',retryDelays:[0,3000,5000,10000,20000],headers:{authorization:'Bearer '+session.access_token,apikey:window.DUCKZIN_CONFIG.key},uploadDataDuringCreation:true,removeFingerprintOnSuccess:true,metadata:{bucketName:bucket,objectName:path,contentType:file.type||'application/octet-stream',cacheControl:'3600'},chunkSize:6*1024*1024,onProgress:(a,b)=>progress?.(Math.round(a/b*100)),onError:reject,onSuccess:resolve});u.findPreviousUploads().then(p=>{if(p.length)u.resumeFromPreviousUpload(p[0]);u.start()}).catch(reject);});}
return sb.storage.from(bucket).getPublicUrl(path).data.publicUrl;
}
let saving=false;
async function saveProject(e){e.preventDefault();if(saving)return;saving=true;$('pubSubmit').disabled=true;try{const auth=await sb.auth.getUser();const r=await sb.rpc('is_duckzin_admin');if(!auth.data.user||r.error||r.data!==true)throw Error('Você precisa entrar com a conta de administrador');const id=$('pubId').value;const old=projectCache.find(p=>p.id===id)||{};const payload={title:$('pubName').value.trim(),category:$('pubCategory').value,version:$('pubVersion').value.trim(),status:$('pubStatus').value.trim(),description:$('pubDescription').value.trim(),download_url:$('pubDownload').value.trim()||null,icon_url:old.icon_url||null,banner_url:old.banner_url||null};
if(!payload.title||!payload.description)throw Error('Preencha nome e descrição');const allowedImage=['png','jpg','jpeg','webp'],allowedBinary=['zip','jar','exe','msi','apk','7z','rar','dmg','deb','pdf'];const ic=$('pubIcon').files?.[0],bn=$('pubBanner').files?.[0],exe=$('pubFile').files?.[0];const progress=$('pubProgress');
if(ic){fileStatus('Enviando ícone...');payload.icon_url=await uploadFile('project-images',ic,2097152,allowedImage)}if(bn){fileStatus('Enviando banner...');payload.banner_url=await uploadFile('project-images',bn,2097152,allowedImage)}if(exe){progress.hidden=false;progress.value=0;fileStatus('Enviando arquivo de download...');payload.download_url=await uploadFile('project-files',exe,52428800,allowedBinary,v=>{progress.value=v;fileStatus('Upload do arquivo: '+v+'%')})}
fileStatus('Salvando projeto...');const query=id?sb.from('projects').update(payload).eq('id',id):sb.from('projects').insert(payload);const output=await query;if(output.error)throw output.error;fileStatus('Projeto publicado com sucesso!','ok');await loadProjects();setTimeout(()=>location.reload(),1800);
}catch(err){fileStatus('Erro ao publicar: '+(err.message||err),'error')}finally{saving=false;$('pubSubmit').disabled=false;}}
async function removeProject(p){if(!admin||!window.confirm('Excluir o projeto '+p.title+'?'))return;const r=await sb.from('projects').delete().eq('id',p.id);if(r.error)return window.alert('Erro: '+r.error.message);void loadProjects();window.alert('Projeto excluído. Atualize a página para atualizar o catálogo.');}
function boot(){initChat();initAdmin();setInterval(refreshMessages,4300);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();