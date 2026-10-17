/* Consent behaviour checks with browser storage and event boundaries simulated. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const memoryKey = 'theogonyRememberPreferencesV1';
const analyticsKey = 'theogonyAnalyticsConsentV1';
function page(initial = {}, privacySignal = false, storageBlocked = false) {
  const store = new Map(Object.entries(initial)), elements = new Map(), scripts = [];
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      id, hidden: false, checked: false, open: false, isConnected: true, listeners: {},
      addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); },
      emit(type) { for (const fn of this.listeners[type] || []) fn({ target: this }); },
      showModal() { this.open = true; }, close() { this.open = false; this.emit('close'); },
      focus() {}, querySelector() { return element('close'); }
    });
    return elements.get(id);
  }
  const events = {}, document = {
    activeElement: element('opener'), getElementById: element,
    addEventListener(type, fn) { (events[type] ||= []).push(fn); },
    dispatchEvent(event) { for (const fn of events[event.type] || []) fn(event); },
    createElement() { return {}; }, head: { appendChild(script) { scripts.push(script); } }
  };
  let reloads = 0;
  const context = { document, navigator: { globalPrivacyControl: privacySignal },
    location: { protocol: 'https:', hostname: 'theogony-reading.vercel.app', origin: 'https://theogony-reading.vercel.app', reload() { reloads++; } },
    localStorage: { getItem: key => store.get(key) ?? null,
      setItem(key, value) { if (storageBlocked) throw Error('blocked'); store.set(key, value); },
      removeItem(key) { if (storageBlocked) throw Error('blocked'); store.delete(key); } },
    CustomEvent: class { constructor(type, args) { this.type = type; this.detail = args.detail; } },
    addEventListener() {}, URL
  };
  context.window = context;
  vm.createContext(context);
  for (const file of ['site-preferences-v1.js', 'site-analytics-v1.js']) vm.runInContext(fs.readFileSync(`assets/${file}`, 'utf8'), context);
  return { element, store, scripts, context, reloads: () => reloads };
}
const fresh = page();
assert.equal(fresh.element('site-preferences').open, true);
assert.equal(fresh.element('preference-memory').checked, false);
assert.equal(fresh.element('preference-analytics').checked, false);
assert.equal(fresh.scripts.length, 0);
fresh.element('preferences-manage-button').emit('click');
assert.equal(fresh.element('preferences-manage').hidden, false);
fresh.element('preference-memory').checked = true;
fresh.element('preferences-save').emit('click');
assert.equal(fresh.store.get(memoryKey), 'enabled');
assert.equal(fresh.store.get(analyticsKey), 'disabled');
assert.equal(fresh.scripts.length, 0);
assert.equal(page(Object.fromEntries(fresh.store)).element('site-preferences').open, false);
const accept = page();
accept.element('preferences-accept').emit('click');
assert.equal(accept.store.get(memoryKey), 'enabled');
assert.equal(accept.store.get(analyticsKey), 'enabled');
assert.equal(accept.scripts.length, 1);
const beforeSend = accept.context.vaq[0][1];
assert.equal(beforeSend({url:'https://theogony-reading.vercel.app/index.html?query=private#v1'}).url, 'https://theogony-reading.vercel.app/');
accept.store.set('theogonyReadingSize', '2');
accept.store.set('theogonyReadingPositionV1', '{"id":"v10"}');
accept.store.set('theogonyDesktopContentsV1', 'hidden');
accept.context.TheogonyPreferences.open();
accept.element('preferences-reject').emit('click');
assert.equal(accept.reloads(), 1);
assert.equal(accept.store.has('theogonyReadingSize'), false);
assert.equal(accept.store.has('theogonyReadingPositionV1'), false);
assert.equal(accept.store.has('theogonyDesktopContentsV1'), false);
assert.equal(beforeSend({url:'https://theogony-reading.vercel.app/'}), null);
const signal = page({}, true);
signal.element('preferences-accept').emit('click');
assert.equal(signal.store.get(memoryKey), 'enabled');
assert.equal(signal.store.get(analyticsKey), 'disabled');
assert.equal(signal.scripts.length, 0);
assert.equal(signal.element('preference-analytics').disabled, true);
const blocked = page({}, false, true);
blocked.element('preferences-accept').emit('click');
assert.equal(blocked.scripts.length, 0);
assert.equal(blocked.element('preferences-error').hidden, false);
console.log('Passed: opt-in defaults, granular choices, return visits, accept/reject, reading-data removal, analytics withdrawal, URL minimisation, privacy signal and blocked storage.');
