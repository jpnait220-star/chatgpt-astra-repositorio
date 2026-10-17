export const DEFAULT_SETTINGS = Object.freeze({ minutes: 15, paused: false });
export function normalizeSettings(value = {}) {
  const minutes = Number(value.minutes);
  return { minutes: Number.isFinite(minutes) ? Math.max(1, Math.min(1440, Math.round(minutes))) : 15, paused: value.paused === true };
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
export function reconcile(tabs, records, now) {
  const next = {};
  for (const tab of tabs) {
    const old = records[tab.id];
    next[tab.id] = {
      favorite: old?.favorite === true,
      lastActive: !old || tab.active || tab.audible || tab.pinned || old.active || old.audible || old.pinned ? now : old.lastActive,
      active: !!tab.active, audible: !!tab.audible, pinned: !!tab.pinned
    };
  }
  return next;
}
