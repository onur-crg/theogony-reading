/* Analytics is a consumer of the shared preferences component. */
(() => {
  'use strict';
  if (location.protocol !== 'https:' || location.hostname !== 'theogony-reading.vercel.app') return;
  let loaded = false;
  function allowed() { return window.TheogonyPreferences?.getState().analytics === true; }
  function update() {
    if (!allowed()) { if (loaded) location.reload(); return; }
    if (loaded) return;
    loaded = true;
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
    window.va('beforeSend', event => {
      if (!allowed()) return null;
      const url = new URL(event.url, location.origin);
      url.search = ''; url.hash = '';
      if (url.pathname === '/index.html') url.pathname = '/';
      return { ...event, url: url.href };
    });
    const script = document.createElement('script');
    script.src = '/_vercel/insights/script.js'; script.defer = true;
    document.head.appendChild(script);
  }
  document.addEventListener('theogony:preferences-changed', update);
  update();
})();
