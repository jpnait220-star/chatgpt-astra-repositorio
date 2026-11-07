export const DEFAULT_SETTINGS = Object.freeze({ minutes: 15, paused: false });
export function normalizeSettings(value = {}) {
  const minutes = Number(value?.minutes);
  return { minutes: Number.isFinite(minutes) ? Math.max(1, Math.min(1440, Math.round(minutes))) : 15, paused: value?.paused === true };
}
export function favoriteKey(value) {
  try {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol)) return '';
    url.hash = '';
    return url.href;
  } catch { return ''; }
}
export function normalizeFavorites(value) {
  if (!Array.isArray(value)) return [];
  const seen = new Set();
  const items = [];
  for (const item of value) {
    const url = favoriteKey(item?.url);
    if (!url || seen.has(url)) continue;
    seen.add(url);
    items.push({
      url,
      title: String(item?.title || new URL(url).hostname).slice(0, 250),
      savedAt: Number.isFinite(item?.savedAt) ? item.savedAt : Date.now()
    });
    if (items.length === 500) break;
  }
  return items;
}
export function normalizeHistory(value) {
  if (!Array.isArray(value)) return [];
  return value.filter(item => item && typeof item.title === 'string' && Number.isFinite(item.at))
    .slice(0, 30).map(item => ({ title: item.title.slice(0, 300), at: item.at }));
}
export function protection(tab, record, guiUrl) {
  if (tab.url?.startsWith(guiUrl)) return 'DuckCleans';
  if (record?.favorite) return 'Favorite';
  if (tab.active) return 'Active now';
  if (tab.pinned) return 'Pinned';
  if (tab.audible) return 'Playing audio';
  if (!/^https?:\/\//i.test(tab.url || '')) return 'Browser page';
  return null;
}
export function canClose(tab, record, settings, now, guiUrl) {
  return !settings.paused && !!record && !protection(tab, record, guiUrl) && now - record.lastActive >= settings.minutes * 60000;
}
export function reconcile(tabs, records, now, favorites = []) {
  const saved = new Set(favorites.map(item => typeof item === 'string' ? item : item.url));
  const next = {};
  for (const tab of tabs) {
    const old = records?.[tab.id];
    const url = favoriteKey(tab.url);
    const savedHere = !!url && saved.has(url);
    next[tab.id] = {
      favorite: old?.favorite === true || savedHere,
      favoriteUrl: old?.favorite ? (old.favoriteUrl || url) : savedHere ? url : null,
      lastActive: !old || tab.active || tab.audible || tab.pinned || old.active || old.audible || old.pinned ? now : old.lastActive,
      active: !!tab.active, audible: !!tab.audible, pinned: !!tab.pinned
    };
  }
  return next;
}
