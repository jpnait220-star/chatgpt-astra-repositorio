import { DEFAULT_SETTINGS, normalizeSettings, protection, canClose, reconcile } from './core.js';
const GUI = chrome.runtime.getURL('dashboard.html');
let queue = Promise.resolve();
const serial = task => {
  const result = queue.then(task);
  queue = result.catch(error => console.error('DuckCleans:', error));
  return result;
};
async function load() {
  const [local, session, tabs] = await Promise.all([
    chrome.storage.local.get({ settings: DEFAULT_SETTINGS, cleaned: 0, history: [] }),
    chrome.storage.session.get({ records: {} }), chrome.tabs.query({})
  ]);
  const settings = normalizeSettings(local.settings);
  const records = reconcile(tabs, session.records, Date.now());
  await chrome.storage.session.set({ records });
  return { ...local, settings, records, tabs };
}
async function ensureAlarm() {
  if (!await chrome.alarms.get('duckcleans-sweep')) await chrome.alarms.create('duckcleans-sweep', { periodInMinutes: 1 });
}
async function sweep() {
  await ensureAlarm();
  const state = await load();
  for (const tab of state.tabs) {
    if (!canClose(tab, state.records[tab.id], state.settings, Date.now(), GUI)) continue;
    let fresh;
    try { fresh = await chrome.tabs.get(tab.id); } catch { continue; }
    if (!canClose(fresh, state.records[tab.id], state.settings, Date.now(), GUI)) continue;
    try { await chrome.tabs.remove(tab.id); } catch { continue; }
    state.cleaned++;
    state.history.unshift({ title: fresh.title || 'Aba sem título', at: Date.now() });
    delete state.records[tab.id];
    // Persist each successful close, so worker suspension cannot lose an entire sweep.
    await chrome.storage.local.set({ cleaned: state.cleaned, history: state.history.slice(0, 30) });
    await chrome.storage.session.set({ records: state.records });
  }
}
async function snapshot() {
  const state = await load();
  return {
    settings: state.settings, cleaned: state.cleaned, history: state.history,
    tabs: state.tabs.filter(tab => !tab.url?.startsWith(GUI)).map(tab => ({
      id: tab.id, windowId: tab.windowId, title: tab.title || 'Aba sem título', url: tab.url || '',
      favorite: state.records[tab.id].favorite, lastActive: state.records[tab.id].lastActive,
      protection: protection(tab, state.records[tab.id], GUI)
    }))
  };
}
async function handle(message) {
  if (message.type === 'getState') return snapshot();
  if (message.type === 'settings') {
    const state = await load();
    const settings = normalizeSettings({ ...state.settings, ...message.settings });
    // Give idle tabs a full new interval after resuming or changing the timeout.
    if ((state.settings.paused && !settings.paused) || state.settings.minutes !== settings.minutes) {
      for (const record of Object.values(state.records)) record.lastActive = Date.now();
      await chrome.storage.session.set({ records: state.records });
    }
    await chrome.storage.local.set({ settings });
    return snapshot();
  }
  if (message.type === 'favorite') {
    const state = await load();
    if (!state.records[message.id]) throw new Error('Esta aba já foi fechada.');
    state.records[message.id].favorite = !state.records[message.id].favorite;
    state.records[message.id].lastActive = Date.now();
    await chrome.storage.session.set({ records: state.records });
    return snapshot();
  }
  if (message.type === 'focus') {
    const tab = await chrome.tabs.get(message.id);
    await chrome.windows.update(tab.windowId, { focused: true });
    await chrome.tabs.update(message.id, { active: true });
    return snapshot();
  }
  if (message.type === 'clearHistory') {
    await chrome.storage.local.set({ history: [] });
    return snapshot();
  }
  throw new Error('Solicitação desconhecida.');
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (sender.id !== chrome.runtime.id || !sender.url?.startsWith(GUI)) return false;
  serial(() => handle(message)).then(data => respond({ ok: true, data }), error => respond({ ok: false, error: error.message }));
  return true;
});
chrome.action.onClicked.addListener(() => serial(async () => {
  const tabs = await chrome.tabs.query({});
  const existing = tabs.find(tab => tab.url?.startsWith(GUI));
  if (existing) {
    await chrome.windows.update(existing.windowId, { focused: true });
    await chrome.tabs.update(existing.id, { active: true });
  } else await chrome.tabs.create({ url: GUI });
}));
chrome.alarms.onAlarm.addListener(alarm => { if (alarm.name === 'duckcleans-sweep') serial(sweep); });
chrome.tabs.onActivated.addListener(() => serial(load));
chrome.tabs.onCreated.addListener(() => serial(load));
chrome.tabs.onRemoved.addListener(() => serial(load));
chrome.tabs.onUpdated.addListener((id, changes) => {
  if ('audible' in changes || 'pinned' in changes || 'url' in changes) serial(load);
});
chrome.runtime.onStartup.addListener(() => serial(sweep));
chrome.runtime.onInstalled.addListener(() => serial(sweep));
serial(ensureAlarm);
