import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeSettings, protection, canClose, reconcile } from '../core.js';
const now = 2_000_000;
const tab = { id:1, url:'https://example.org', active:false, audible:false, pinned:false };
const record = { lastActive:now - 15 * 60000, favorite:false };
const settings = { minutes:15, paused:false };
const gui = 'chrome-extension://test/dashboard.html';
test('enforces the minimum, maximum, and valid default timeout', () => {
  for (const input of [0,-1,.4]) assert.equal(normalizeSettings({minutes:input}).minutes,1);
  for (const input of [1,2,14,15]) assert.equal(normalizeSettings({minutes:input}).minutes,input);
  assert.equal(normalizeSettings({minutes:2000}).minutes,1440);
  assert.equal(normalizeSettings({minutes:'bad'}).minutes,15);
  assert.equal(normalizeSettings().minutes,15);
  assert.equal(normalizeSettings({minutes:30.7}).minutes,31);
});
test('one-minute timeout closes at 60 seconds and still protects the GUI and favorites', () => {
  const config = { minutes: 1, paused: false };
  const idle = { lastActive: now - 60000, favorite: false };
  assert.equal(canClose(tab,idle,config,now-1,gui),false);
  assert.equal(canClose(tab,idle,config,now,gui),true);
  assert.equal(canClose(tab,{...idle,favorite:true},config,now,gui),false);
  assert.equal(canClose({...tab,url:gui},idle,config,now+86400000,gui),false);
});
test('closes only after the complete inactivity interval', () => {
  assert.equal(canClose(tab,record,settings,now-1,gui),false);
  assert.equal(canClose(tab,record,settings,now,gui),true);
  assert.equal(canClose(tab,record,{...settings,minutes:30},now,gui),false);
  assert.equal(canClose(tab,null,settings,now,gui),false);
});
test('protects favorites, selected tabs, pinned tabs, audio, and browser pages', () => {
  for (const update of [{active:true},{pinned:true},{audible:true},{url:'opera://settings'},{url:gui},{url:'file:///tmp/report.html'},{url:undefined}]) {
    assert.equal(canClose({...tab,...update},record,settings,now,gui),false);
  }
  assert.equal(canClose(tab,{...record,favorite:true},settings,now,gui),false);
  assert.equal(canClose(tab,record,{...settings,paused:true},now,gui),false);
  assert.equal(protection(tab,{...record,favorite:true},gui),'Favorite');
});
test('reconciliation resets timers when active, pinned or audio protection ends', () => {
  for (const previous of [{active:true},{pinned:true},{audible:true}]) {
    const result = reconcile([tab],{1:{...record,...previous}},now);
    assert.equal(result[1].lastActive,now);
  }
  assert.equal(reconcile([tab],{1:record},now)[1].lastActive,record.lastActive);
});
test('new tabs get full timeout; removed tabs are forgotten; favorites survive navigation', () => {
  assert.equal(reconcile([tab],{},now)[1].lastActive,now);
  assert.deepEqual(reconcile([],{1:record},now),{});
  assert.equal(reconcile([{...tab,url:'https://new.example'}],{1:{...record,favorite:true}},now)[1].favorite,true);
});
