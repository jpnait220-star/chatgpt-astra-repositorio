const $ = selector => document.querySelector(selector);
let state, view = 'overview', toastTimer, pending = false;
const protectionLabels = { 'DuckCleans': 'DuckCleans', 'Favorite': 'Favorita', 'Active now': 'Ativa agora', 'Pinned': 'Fixada', 'Playing audio': 'Reproduzindo áudio', 'Browser page': 'Página do navegador' };
const titles = {
  overview: ['Menos abas. Mente leve.', 'Guarde o que importa. Deixe o resto com a gente.'],
  favorites: ['Algumas abas merecem ficar.', 'Suas abas com estrela ficam protegidas durante esta sessão do navegador.'],
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
    const remaining = seconds >= 60 ? `${Math.ceil(seconds / 60)} min restantes` : seconds > 0 ? '< 1 min restante' : 'Na próxima verificação';
    const label = protectionLabels[tab.protection] || (state.settings.paused ? 'Limpeza pausada' : remaining);
    const status = node('span',`tab-status${tab.protection ? '' : ' idle'}`, `${tab.protection === 'Favorite' ? '☆  ' : ''}${label}`);
    const star = node('button',`star${tab.favorite ? ' favorited' : ''}`,tab.favorite ? '★' : '☆');
    star.setAttribute('aria-label',`${tab.favorite ? 'Remover dos favoritos:' : 'Favoritar:'} ${tab.title}`);
    star.setAttribute('aria-pressed',String(tab.favorite)); star.title = tab.favorite ? 'Remover proteção' : 'Proteger esta aba até ela ser fechada';
    star.addEventListener('click',() => act({ type:'favorite',id:tab.id },tab.favorite ? 'Proteção removida. A contagem recomeçou.' : 'Aba protegida. Ela fica aberta até você fechá-la.'));
    row.append(info,status,star); list.append(row);
  }
  if (!tabs.length) empty(list,view === 'favorites' ? '☆' : '◫',search ? 'Nenhuma aba encontrada.' : view === 'favorites' ? 'Dê uma estrela aos seus favoritos.' : 'Tudo pronto para começar.',search ? 'Tente outro título ou site.' : view === 'favorites' ? 'Marque uma aba com estrela na Visão geral para protegê-la da limpeza automática.' : 'Abra um site e ele aparecerá aqui.');
}
function render() {
  if (!state) return;
  const count = state.tabs.filter(tab => tab.favorite).length;
  $('#openCount').textContent = state.tabs.length; $('#favoriteCount').textContent = count;
  $('#navFavoriteCount').textContent = count; $('#cleanedCount').textContent = state.cleaned;
  $('#heroMinutes').textContent = `${state.settings.minutes} minutos`;
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
  document.querySelectorAll('[data-minutes]').forEach(button => button.classList.toggle('chosen',Number(button.dataset.minutes) === state.settings.minutes));
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
function setView(next) {
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
}
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click',() => setView(button.dataset.view)));
$('#search').addEventListener('input',renderTabs);
$('#pauseButton').addEventListener('click',() => state && act({ type:'settings',settings:{ paused:!state.settings.paused } },state.settings.paused ? 'Limpeza retomada. Todas as contagens recomeçaram.' : 'Limpeza pausada. Suas abas continuarão abertas.'));
$('#timeoutRange').addEventListener('input',event => { $('#timeoutDisplay').textContent = event.target.value; $('#customMinutes').value = event.target.value; });
$('#timeoutRange').addEventListener('change',event => saveTimeout(Number(event.target.value)));
function saveTimeout(minutes) {
  if (!Number.isInteger(minutes) || minutes < 15 || minutes > 1440) return toast('Escolha um número inteiro entre 15 e 1.440 minutos.');
  act({ type:'settings',settings:{ minutes } },`Tempo salvo: ${minutes} minutos.`).then(() => { if (state) syncSettings(); });
}
document.querySelectorAll('[data-minutes]').forEach(button => button.addEventListener('click',() => saveTimeout(Number(button.dataset.minutes))));
$('#timeoutForm').addEventListener('submit',event => { event.preventDefault(); saveTimeout(Number($('#customMinutes').value)); });
$('#clearHistory').addEventListener('click',() => act({ type:'clearHistory' },'Histórico apagado.'));
async function refresh() {
  if (pending || document.hidden) return;
  try { state = await request({ type:'getState' }); render(); }
  catch (error) { $('#headerStatus').textContent = 'Sem conexão'; toast(error.message); }
}
setView('overview'); refresh(); setInterval(refresh,10000);
document.addEventListener('visibilitychange',() => { if (!document.hidden) refresh(); });
