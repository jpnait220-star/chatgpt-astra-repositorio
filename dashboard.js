import { initMotion, fadeIn } from './motion.js';
const $ = selector => document.querySelector(selector);
let state, view = 'overview', toastTimer, pending = false;
const protectionLabels = { 'DuckCleans': 'DuckCleans', 'Favorite': 'Favorita', 'Active now': 'Ativa agora', 'Pinned': 'Fixada', 'Playing audio': 'Reproduzindo áudio', 'Browser page': 'Página do navegador' };
const titles = {
  overview: ['Menos abas. Mente leve.', 'Guarde o que importa. Deixe o resto com a gente.'],
  favorites: ['Algumas abas merecem ficar.', 'Seus sites favoritos continuam salvos após reiniciar o navegador.'],
  activity: ['Já está tudo mais leve.', 'Veja as abas que a DuckCleans fechou para você.'],
  settings: ['Seu navegador. Seu ritmo.', 'Escolha o tempo. A gente cuida da limpeza.']
};
function toast(message) {
  $('#toast').textContent = message; $('#toast').hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => $('#toast').hidden = true, 4200);
}
async function request(message) {
  if (!globalThis.chrome?.runtime?.sendMessage) throw new Error('Instale a DuckCleans como extensão no Opera para acessar suas abas.');
  const response = await chrome.runtime.sendMessage(message);
  if (!response?.ok) throw new Error(response?.error || 'Não foi possível conectar. Abra a DuckCleans novamente.');
  return response.data;
}
async function act(message, feedback) {
  if (pending) return;
  pending = true;
  try { state = await request(message); render(); if (feedback) toast(feedback); }
  catch (error) { toast(error.message); }
  finally { pending = false; }
}
function domain(url) {
  try { return new URL(url).hostname || 'Página do navegador'; } catch { return 'Página do navegador'; }
}
function node(tag, className, text) {
  const el = document.createElement(tag); if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
function empty(container, icon, title, description) {
  const el = node('div', 'empty');
  el.append(node('span','empty-icon',icon),node('strong','',title),node('span','',description)); container.append(el);
}
function renderTabs() {
  if (!state) return;
  const search = $('#search').value.toLowerCase().trim();
  const tabs = state.tabs.filter(tab => (view !== 'favorites' || tab.favorite) && `${tab.title} ${tab.url}`.toLowerCase().includes(search));
  const list = $('#tabList'); list.replaceChildren(); $('#tabCount').textContent = tabs.length;
  for (const tab of tabs) {
    const row = node('div','tab-row'), info = node('div','tab-info');
    const icon = node('span','site-icon',domain(tab.url).replace(/^www\./,'')[0]?.toUpperCase() || '↗');
    const link = node('button','tab-link'); link.title = `Abrir ${tab.title}`;
    link.append(node('span','tab-title',tab.title),node('span','tab-domain',domain(tab.url)));
    link.addEventListener('click',() => act({ type:'focus',id:tab.id }));
    info.append(icon,link);
    const seconds = Math.max(0, Math.ceil((tab.lastActive + state.settings.minutes * 60000 - Date.now()) / 1000));
    const remaining = seconds >= 60 ? `${Math.ceil(seconds / 60)} min restantes` : seconds > 0 ? `${seconds} s restantes` : 'Na próxima verificação';
    const label = protectionLabels[tab.protection] || (state.settings.paused ? 'Limpeza pausada' : remaining);
    const status = node('span',`tab-status${tab.protection ? '' : ' idle'}`, `${tab.protection === 'Favorite' ? '☆  ' : ''}${label}`);
    const star = node('button',`star${tab.favorite ? ' favorited' : ''}`,tab.favorite ? '★' : '☆');
    star.setAttribute('aria-label',`${tab.favorite ? 'Remover dos favoritos:' : 'Favoritar:'} ${tab.title}`);
    star.setAttribute('aria-pressed',String(tab.favorite)); star.title = tab.favorite ? 'Remover dos favoritos salvos' : 'Salvar este site nos favoritos';
    star.addEventListener('click',() => act({ type:'favorite',id:tab.id },tab.favorite ? 'Favorito removido.' : 'Site salvo! Ele continuará nos favoritos após reiniciar.'));
    row.append(info,status,star); list.append(row);
  }
  if (view === 'favorites') {
    const opened = new Set(state.tabs.filter(tab => tab.favorite).map(tab => {
      try { const url = new URL(tab.url); url.hash = ''; return url.href; } catch { return ''; }
    }));
    for (const fav of (state.savedFavorites || [])) {
      if (opened.has(fav.url) || !(`${fav.title} ${fav.url}`).toLowerCase().includes(search)) continue;
      const row = node('div', 'tab-row'), info = node('div','tab-info');
      const icon = node('span','site-icon','☆');
      const link = node('button','tab-link'); link.title = 'Abrir favorito salvo';
      link.append(node('span','tab-title',fav.title),node('span','tab-domain',domain(fav.url)));
      link.addEventListener('click',() => act({type:'openFavorite',url:fav.url}));
      info.append(icon,link);
      const status = node('span','tab-status','Salvo para depois');
      const remove = node('button','star favorited','★');
      remove.title='Remover favorito salvo'; remove.setAttribute('aria-label','Remover favorito salvo: '+fav.title);
      remove.addEventListener('click',()=>act({type:'removeFavorite',url:fav.url},'Favorito removido.'));
      row.append(info,status,remove); list.append(row);
    }
  }
  if (!list.childElementCount) empty(list,view === 'favorites' ? '☆' : '◫',search ? 'Nenhuma aba encontrada.' : view === 'favorites' ? 'Dê uma estrela aos seus favoritos.' : 'Tudo pronto para começar.',search ? 'Tente outro título ou site.' : view === 'favorites' ? 'Marque uma aba com estrela na Visão geral para protegê-la da limpeza automática.' : 'Abra um site e ele aparecerá aqui.');
  $('#tabCount').textContent = list.querySelectorAll('.tab-row').length;
}
function render() {
  if (!state) return;
  const count = state.savedFavorites?.length || 0;
  $('#openCount').textContent = state.tabs.length; $('#favoriteCount').textContent = count;
  $('#navFavoriteCount').textContent = count; $('#cleanedCount').textContent = state.cleaned;
  $('#heroMinutes').textContent = formatMinutes(state.settings.minutes);
  $('#headerStatus').textContent = state.settings.paused ? 'Limpeza pausada' : 'Limpeza ativada';
  $('#headerDot').style.opacity = state.settings.paused ? '.3' : '1';
  $('#heroStatus').replaceChildren(node('span','status-dot'), document.createTextNode(state.settings.paused ? 'LIMPEZA AUTOMÁTICA PAUSADA' : 'LIMPEZA AUTOMÁTICA ATIVA'));
  $('#pauseButton').replaceChildren(document.createTextNode(state.settings.paused ? '▶ ' : 'II '),node('span','',state.settings.paused ? 'Retomar limpeza' : 'Pausar limpeza'));
  // Avoid overwriting a timeout the user is currently editing during background refresh.
  if (!$('#settingsSection').contains(document.activeElement)) syncSettings();
  renderTabs(); renderActivity();
}
function syncSettings() {
  $('#timeoutDisplay').textContent = state.settings.minutes;
  $('#customMinutes').value = state.settings.minutes;
  $('#timeoutRange').value = Math.min(240,state.settings.minutes);
  updateRange();
  document.querySelectorAll('[data-minutes]').forEach(button => button.classList.toggle('chosen',Number(button.dataset.minutes) === state.settings.minutes));
}
function formatMinutes(minutes) { return `${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}`; }
function updateRange() {
  const slider = $('#timeoutRange');
  const progress = (Number(slider.value) - Number(slider.min)) / (Number(slider.max) - Number(slider.min)) * 100;
  slider.style.setProperty('--range-progress', `${progress}%`);
  slider.setAttribute('aria-valuetext', formatMinutes(Number(slider.value)));
}
function renderActivity() {
  const list = $('#activityList'); list.replaceChildren();
  for (const item of state.history) {
    const row = node('div','activity-row'), info = node('div');
    info.append(node('strong','',item.title),node('p','','Fechada automaticamente · tempo de inatividade'));
    const time = node('time','',new Date(item.at).toLocaleString('pt-BR',{ month:'short',day:'numeric',hour:'2-digit',minute:'2-digit' }));
    time.dateTime = new Date(item.at).toISOString(); row.append(info,time); list.append(row);
  }
  if (!state.history.length) empty(list,'✧','Tudo tranquilo por aqui.','As abas fechadas automaticamente aparecerão aqui.');
  $('#clearHistory').disabled = state.history.length === 0;
}
$('#exportBackup').addEventListener('click', async () => {
  try {
    const backup = await request({type:'exportData'});
    const blob = new Blob([JSON.stringify(backup,null,2)],{type:'application/json'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.href=url; link.download='DuckCleans-backup.json'; link.click();
    setTimeout(()=>URL.revokeObjectURL(url),5000);
    toast('Backup baixado com sucesso.');
  } catch (error) { toast(error.message); }
});
$('#importBackup').addEventListener('change', async event => {
  const file = event.target.files?.[0]; event.target.value='';
  if (!file) return;
  if (file.size > 2_000_000) return toast('Backup muito grande.');
  try {
    const data=JSON.parse(await file.text());
    if (!confirm('Restaurar este backup? Favoritos e histórico atuais serão substituídos.')) return;
    await act({type:'importData',data},'Backup restaurado!');
  } catch(error) { toast('Não foi possível importar: '+error.message); }
});
function setView(next, animate = true) {
  view = next;
  document.querySelectorAll('[data-view]').forEach(button => { const selected = button.dataset.view === view; button.classList.toggle('selected',selected); if (selected) button.setAttribute('aria-current','page'); else button.removeAttribute('aria-current'); });
  $('#pageTitle').textContent = ({ overview: 'Visão geral', favorites: 'Favoritos', activity: 'Histórico', settings: 'Configurações' })[view];
  $('#heading').textContent = titles[view][0]; $('#subtitle').textContent = titles[view][1];
  $('#overviewSection').hidden = view !== 'overview';
  $('#tabsSection').hidden = !['overview','favorites'].includes(view);
  $('#settingsSection').hidden = view !== 'settings'; $('#activitySection').hidden = view !== 'activity';
  $('#tabsTitle').firstChild.textContent = view === 'favorites' ? 'Suas abas protegidas ' : 'Suas abas abertas ';
  $('#tabsDescription').textContent = view === 'favorites' ? 'Protegidas da limpeza, mesmo ao navegar para outra página.' : 'Uma estrela é tudo que uma aba precisa para ficar.';
  $('#search').value = ''; if (state) syncSettings(); renderTabs();
  if (animate) fadeIn($('.content'));
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click',() => setView(button.dataset.view)));
$('#search').addEventListener('input',renderTabs);
$('#pauseButton').addEventListener('click',() => state && act({ type:'settings',settings:{ paused:!state.settings.paused } },state.settings.paused ? 'Limpeza retomada. Todas as contagens recomeçaram.' : 'Limpeza pausada. Suas abas continuarão abertas.'));
$('#timeoutRange').addEventListener('input',event => { $('#timeoutDisplay').textContent = event.target.value; $('#customMinutes').value = event.target.value; updateRange(); });
$('#timeoutRange').addEventListener('change',event => saveTimeout(Number(event.target.value)));
function saveTimeout(minutes) {
  if (!Number.isInteger(minutes) || minutes < 1 || minutes > 1440) return toast('Escolha um número inteiro entre 1 e 1.440 minutos.');
  act({ type:'settings',settings:{ minutes } },`Tempo salvo: ${formatMinutes(minutes)}.`).then(() => { if (state) syncSettings(); });
}
document.querySelectorAll('[data-minutes]').forEach(button => button.addEventListener('click',() => saveTimeout(Number(button.dataset.minutes))));
$('#timeoutForm').addEventListener('submit',event => { event.preventDefault(); saveTimeout(Number($('#customMinutes').value)); });
$('#clearHistory').addEventListener('click',() => act({ type:'clearHistory' },'Histórico apagado.'));
async function refresh() {
  if (pending || document.hidden) return;
  try { state = await request({ type:'getState' }); render(); }
  catch (error) { $('#headerStatus').textContent = 'Sem conexão'; toast(error.message); }
}
initMotion(); updateRange(); setView('overview', false); refresh(); setInterval(refresh,10000);
document.addEventListener('visibilitychange',() => { if (!document.hidden) refresh(); });
