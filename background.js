import { DEFAULT_SETTINGS, normalizeSettings, protection, canClose, reconcile, favoriteKey, normalizeFavorites, normalizeHistory } from './core.js';
const GUI = chrome.runtime.getURL('dashboard.html');
let queue = Promise.resolve();
const serial = task => {
  const result = queue.then(task);
  queue = result.catch(error => console.error('DuckCleans:', error));
  return result;
};
async function load() {
  const [local, session, tabs] = await Promise.all([
    chrome.storage.local.get({ settings: DEFAULT_SETTINGS, cleaned: 0, history: [], savedFavorites: [] }),
    chrome.storage.session.get({ records: {} }), chrome.tabs.query({})
  ]);
  const settings = normalizeSettings(local.settings);
  const history = normalizeHistory(local.history);
  const savedFavorites = normalizeFavorites(local.savedFavorites);
  const existing = new Set(savedFavorites.map(item => item.url));
  let migrated = false;
  // Recover stars from the old session-based version on the first update.
  for (const tab of tabs) {
    const old = session.records?.[tab.id];
    const url = favoriteKey(old?.favoriteUrl || tab.url);
    if (!old?.favorite || !url || existing.has(url)) continue;
    savedFavorites.push({ url, title: (tab.title || new URL(url).hostname).slice(0, 250), savedAt: Date.now() });
    existing.add(url);
    migrated = true;
  }
  if (migrated) await chrome.storage.local.set({ savedFavorites });
  const records = reconcile(tabs, session.records || {}, Date.now(), savedFavorites);
  await chrome.storage.session.set({ records });
  return { ...local, settings, history, savedFavorites, records, tabs };
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
    settings: state.settings, cleaned: state.cleaned, history: state.history, savedFavorites: state.savedFavorites,
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
    const tab = state.tabs.find(item => item.id === message.id);
    const record = state.records[message.id];
    if (!tab || !record) throw new Error('Esta aba já foi fechada.');
    const url = favoriteKey(tab.url);
    if (!url) throw new Error('Só é possível favoritar páginas de sites.');
    const now = Date.now();
    if (record.favorite) {
      const removed = record.favoriteUrl || url;
      state.savedFavorites = state.savedFavorites.filter(item => item.url !== removed);
      for (const item of Object.values(state.records)) {
        if (item.favoriteUrl === removed) { item.favorite = false; item.favoriteUrl = null; item.lastActive = now; }
      }
    } else {
      state.savedFavorites.unshift({ url, title: (tab.title || new URL(url).hostname).slice(0, 250), savedAt: now });
      state.savedFavorites = normalizeFavorites(state.savedFavorites);
      record.favorite = true; record.favoriteUrl = url; record.lastActive = now;
    }
    await chrome.storage.local.set({ savedFavorites: state.savedFavorites });
    await chrome.storage.session.set({ records: state.records });
    return snapshot();
  }
  if (message.type === 'removeFavorite') {
    const state = await load();
    const url = favoriteKey(message.url);
    if (!state.savedFavorites.some(item => item.url === url)) throw new Error('Favorito não encontrado.');
    state.savedFavorites = state.savedFavorites.filter(item => item.url !== url);
    const now = Date.now();
    for (const record of Object.values(state.records)) {
      if (record.favoriteUrl === url) { record.favorite = false; record.favoriteUrl = null; record.lastActive = now; }
    }
    await chrome.storage.local.set({ savedFavorites: state.savedFavorites });
    await chrome.storage.session.set({ records: state.records });
    return snapshot();
  }
  if (message.type === 'openFavorite') {
    const state = await load();
    const saved = state.savedFavorites.find(item => item.url === favoriteKey(message.url));
    if (!saved) throw new Error('Este favorito não está mais salvo.');
    await chrome.tabs.create({ url: saved.url, active: true });
    return snapshot();
  }
  if (message.type === 'exportData') {
    const state = await load();
    return { app: 'DuckCleans', format: 1, exportedAt: new Date().toISOString(),
      savedFavorites: state.savedFavorites, history: state.history, settings: state.settings, cleaned: state.cleaned };
  }
  if (message.type === 'importData') {
    const backup = message.data;
    if (!backup || backup.app !== 'DuckCleans' || backup.format !== 1 || !Array.isArray(backup.savedFavorites) || !Array.isArray(backup.history)) {
      throw new Error('Arquivo de backup inválido.');
    }
    const savedFavorites = normalizeFavorites(backup.savedFavorites);
    const history = normalizeHistory(backup.history);
    const cleaned = Number.isSafeInteger(backup.cleaned) && backup.cleaned >= 0 ? backup.cleaned : 0;
    const settings = normalizeSettings(backup.settings);
    await chrome.storage.local.set({ savedFavorites, history, cleaned, settings });
    // After import, do not keep stale tab flags that could override removed stars.
    const tabs = await chrome.tabs.query({});
    const records = reconcile(tabs, {}, Date.now(), savedFavorites);
    await chrome.storage.session.set({ records });
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
