/* Optional visit statistics. Separate from reading-memory preferences. */
(() => {
  'use strict';
  if (location.protocol !== 'https:' || location.hostname !== 'theogony-reading.vercel.app') return;
  const key = 'theogonyAnalyticsConsentV1';
  const privacySignal = navigator.globalPrivacyControl === true || navigator.doNotTrack === '1';
  let choice = readChoice(), loaded = false, notice;
  function readChoice() { try { return localStorage.getItem(key); } catch (_) { return null; } }
  function allowed() { return choice === 'enabled' && !privacySignal; }
  function start() {
    if (!allowed() || loaded) return;
    loaded = true;
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
    window.va('beforeSend', event => {
      if (!allowed() || readChoice() !== 'enabled') return null;
      const url = new URL(event.url, location.origin);
      url.search = ''; url.hash = '';
      if (url.pathname === '/index.html') url.pathname = '/';
      return { ...event, url: url.href };
    });
    const script = document.createElement('script');
    script.src = '/_vercel/insights/script.js'; script.defer = true;
    document.head.appendChild(script);
  }
  function choose(value) {
    choice = value;
    try { localStorage.setItem(key, value); } catch (_) {
      // No persistent consent means no statistics, even if the visitor chose Allow.
      choice = null;
    }
    const wasLoaded = loaded;
    update();
    if (!allowed() && wasLoaded) location.reload();
    else start();
  }
  function update() {
    if (notice) {
      const readingNotice = document.getElementById('reading-notice');
      notice.hidden = privacySignal || choice !== null || Boolean(readingNotice && !readingNotice.hidden);
    }
    const toggle = document.getElementById('analytics-consent');
    if (toggle) { toggle.checked = allowed(); toggle.disabled = privacySignal; }
    const status = document.getElementById('analytics-status');
    if (status) status.textContent = privacySignal
      ? 'Ausgeschaltet: Dein Browser sendet ein Datenschutzsignal (Do Not Track / Global Privacy Control).'
      : allowed() ? 'Besuchsstatistik ist auf diesem Gerät erlaubt.' : 'Besuchsstatistik ist auf diesem Gerät ausgeschaltet.';
  }
  function setup() {
    const style = document.createElement('style');
    style.textContent = '.visit-notice{position:fixed;z-index:19;bottom:1rem;left:50%;transform:translateX(-50%);width:min(38rem,calc(100% - 2rem));box-sizing:border-box;padding:1rem 1.2rem;background:#dedede;color:#1b2c48;border:1px solid #9db2cc;box-shadow:0 .4rem 1.6rem #1b2c481c;font:14px/1.5 "Helvetica Neue",Arial,sans-serif}.visit-notice[hidden]{display:none}.visit-notice p{margin:0 0 .8rem}.visit-notice a{color:#075fce}.visit-actions{display:flex;gap:.6rem}.visit-actions button{flex:1;min-height:42px;padding:.5rem .8rem;border:1px solid #075fce;background:transparent;color:#075fce;font:600 14px/1.3 "Helvetica Neue",Arial,sans-serif;cursor:pointer}.visit-actions button:hover{background:#075fce0c}.visit-actions button:focus-visible{outline:3px solid #075fce;outline-offset:3px}';
    document.head.appendChild(style);
    notice = document.createElement('section'); notice.className = 'visit-notice';
    notice.setAttribute('aria-label', 'Optional visit statistics'); notice.hidden = true;
    notice.innerHTML = '<p>May we count your visit? Optional, cookie-free statistics help us understand which pages are read. No reading position or search text is sent. <a href="privacy.html#visit-statistics">Privacy</a></p><div class="visit-actions"><button type="button" data-visit-choice="enabled">Allow statistics</button><button type="button" data-visit-choice="disabled">No thanks</button></div>';
    document.body.appendChild(notice);
    notice.querySelectorAll('[data-visit-choice]').forEach(button => button.addEventListener('click', () => choose(button.dataset.visitChoice)));
    document.getElementById('analytics-consent')?.addEventListener('change', event => choose(event.target.checked ? 'enabled' : 'disabled'));
    const readingNotice = document.getElementById('reading-notice');
    if (readingNotice) new MutationObserver(update).observe(readingNotice, { attributes: true, attributeFilter: ['hidden'] });
    update(); start();
  }
  addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    choice = readChoice(); update();
    if (loaded && !allowed()) location.reload(); else start();
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup, { once: true });
  else setup();
})();
