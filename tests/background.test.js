import test from 'node:test';
import assert from 'node:assert/strict';

const clone = value => structuredClone(value);
const event = () => ({ listeners:[], addListener(fn) { this.listeners.push(fn); }, emit(...args) { for (const fn of this.listeners) fn(...args); } });
function storage() {
  const data = {};
  return { data, async get(defaults) { return clone(typeof defaults === 'string' ? { [defaults]:data[defaults] } : { ...defaults,...data }); }, async set(values) { Object.assign(data,clone(values)); } };
}
function harness() {
  const tabs = new Map(); let nextId=1;
  const events={onActivated:event(),onCreated:event(),onRemoved:event(),onUpdated:event()};
  const api = {
    storage:{local:storage(),session:storage()},
    runtime:{id:'test',getURL:path=>`chrome-extension://test/${path}`,onMessage:event(),onStartup:event(),onInstalled:event()},
    action:{onClicked:event()}, windows:{async update() {}},
    alarms:{items:{},onAlarm:event(),async get(name) { return this.items[name]; },async create(name,value) { this.items[name]=value; }},
    tabs:{...events,
      async query() { return clone([...tabs.values()]); },
      async get(id) { if (!tabs.has(id)) throw Error('Missing tab'); return clone(tabs.get(id)); },
      async remove(id) { if (!tabs.delete(id)) throw Error('Missing tab'); events.onRemoved.emit(id); },
      async update(id,changes) {
        if (!tabs.has(id)) throw Error('Missing tab');
        if (changes.active) for (const tab of tabs.values()) if (tab.windowId===tabs.get(id).windowId) tab.active=false;
        Object.assign(tabs.get(id),changes);
        if (changes.active) events.onActivated.emit({tabId:id});
        events.onUpdated.emit(id,changes,clone(tabs.get(id)));
        return clone(tabs.get(id));
      },
      async create(props) { const tab={id:nextId++,windowId:1,title:'Test tab',url:'https://example.org',active:false,pinned:false,audible:false,...props}; tabs.set(tab.id,tab); events.onCreated.emit(clone(tab)); return clone(tab); }
    }
  };
  async function rpc(message) {
    return new Promise((resolve,reject) => {
      const listener=api.runtime.onMessage.listeners.at(-1);
      const handled=listener(message,{id:'test',url:'chrome-extension://test/dashboard.html'},response=>response.ok?resolve(response.data):reject(Error(response.error)));
      if (!handled) reject(Error('Message was rejected'));
    });
  }
  return { api,tabs,rpc };
}

test('background worker integration with simulated Chrome APIs', async t => {
  const h=harness(); globalThis.chrome=h.api;
  let now=10_000_000; t.mock.method(Date,'now',()=>now);
  await import('../background.js?integration');
  const ids={};
  for (const name of ['expired','favorite','active','pinned','audio','recent','internal']) {
    const tab=await h.api.tabs.create({title:name,url:name==='internal'?'opera://settings':`https://example.org/${name}`,active:name==='active',pinned:name==='pinned',audible:name==='audio'});
    ids[name]=tab.id;
  }
  await h.rpc({type:'getState'});
  await h.rpc({type:'favorite',id:ids.favorite});
  await h.api.tabs.update(ids.favorite,{url:'https://different.example/'});
  let state=await h.rpc({type:'getState'});
  assert.ok(state.tabs.find(tab=>tab.id===ids.favorite).favorite);
  assert.ok(h.api.alarms.items['duckcleans-sweep']);
  now+=16*60_000;
  h.api.storage.session.data.records[ids.recent].lastActive=now-60_000;
  await h.rpc({type:'settings',settings:{paused:true}});
  h.api.alarms.onAlarm.emit({name:'duckcleans-sweep'});
  await h.rpc({type:'getState'});
  assert.ok(h.tabs.has(ids.expired));
  await h.rpc({type:'settings',settings:{paused:false}});
  assert.equal(h.api.storage.session.data.records[ids.expired].lastActive,now);
  h.api.storage.session.data.records[ids.expired].lastActive=now-16*60_000;
  h.api.alarms.onAlarm.emit({name:'duckcleans-sweep'});
  state=await h.rpc({type:'getState'});
  assert.equal(h.tabs.has(ids.expired),false);
  for (const name of ['favorite','active','pinned','audio','recent','internal']) assert.ok(h.tabs.has(ids[name]),`${name} was closed`);
  assert.equal(state.cleaned,1);
  assert.equal(state.history[0].title,'expired');
  // A page that becomes active immediately before removal must survive.
  const race=await h.api.tabs.create({title:'race'}); await h.rpc({type:'getState'});
  h.api.storage.session.data.records[race.id].lastActive=now-16*60_000;
  const originalGet=h.api.tabs.get;
  h.api.tabs.get=async id=>{if(id===race.id) h.tabs.get(id).active=true; return originalGet(id);};
  h.api.alarms.onAlarm.emit({name:'duckcleans-sweep'}); await h.rpc({type:'getState'});
  assert.ok(h.tabs.has(race.id)); h.api.tabs.get=originalGet;
  state=await h.rpc({type:'settings',settings:{minutes:0}}); assert.equal(state.settings.minutes,1);
  state=await h.rpc({type:'settings',settings:{minutes:2}}); assert.equal(state.settings.minutes,2);
  state=await h.rpc({type:'settings',settings:{minutes:60}}); assert.equal(state.settings.minutes,60);
  await h.rpc({type:'favorite',id:ids.favorite});
  assert.equal(h.api.storage.session.data.records[ids.favorite].lastActive,now);
  // Re-import to simulate a new worker instance, retaining Chrome-managed storage.
  for (const group of [h.api.runtime,h.api.action,h.api.tabs,h.api.alarms]) {
    for (const value of Object.values(group)) if (value?.listeners) value.listeners=[];
  }
  await import('../background.js?restart');
  state=await h.rpc({type:'getState'}); assert.equal(state.settings.minutes,60); assert.equal(state.cleaned,1);
  await h.rpc({type:'clearHistory'}); state=await h.rpc({type:'getState'}); assert.equal(state.history.length,0); assert.equal(state.cleaned,1);
  // Toolbar action opens one GUI and reuses it on subsequent clicks.
  h.api.action.onClicked.listeners.at(-1)(); await h.rpc({type:'getState'});
  h.api.action.onClicked.listeners.at(-1)(); await h.rpc({type:'getState'});
  assert.equal([...h.tabs.values()].filter(tab=>tab.url.includes('/dashboard.html')).length,1);
  await new Promise(resolve=>setImmediate(resolve));
  delete globalThis.chrome;
});
