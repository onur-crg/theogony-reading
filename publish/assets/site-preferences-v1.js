/* Shared preferences UI and storage. No optional feature starts before its choice. */
(() => {
  'use strict';
  const memoryKey = 'theogonyRememberPreferencesV1';
  const analyticsKey = 'theogonyAnalyticsConsentV1';
  const readingData = ['theogonyReadingPositionV1', 'theogonyReadingSize', 'theogonyDesktopContentsV1', 'theogonyExplanationPreferencesV1'];
  const privacySignal = navigator.globalPrivacyControl === true || navigator.doNotTrack === '1';
  const dialog = document.getElementById('site-preferences');
  if (!dialog) return;
  const memory = document.getElementById('preference-memory');
  const analytics = document.getElementById('preference-analytics');
  let opener, state;
  function read(key) {
    try { const value = localStorage.getItem(key); return ['enabled', 'disabled'].includes(value) ? value : null; }
    catch (_) { return null; }
  }
  function getState() {
    return { memory: read(memoryKey) === 'enabled', analytics: read(analyticsKey) === 'enabled' && !privacySignal, privacySignal };
  }
  function sync() {
    state = getState(); memory.checked = state.memory; analytics.checked = state.analytics;
    analytics.disabled = privacySignal;
    document.getElementById('preferences-signal').hidden = !privacySignal;
    const toggle = document.getElementById('analytics-consent');
    if (toggle) { toggle.checked = state.analytics; toggle.disabled = privacySignal; }
    const status = document.getElementById('analytics-status');
    if (status) status.textContent = privacySignal
      ? 'Ausgeschaltet: Dein Browser sendet ein Datenschutzsignal.'
      : state.analytics ? 'Besuchsstatistik ist auf diesem Gerät erlaubt.' : 'Besuchsstatistik ist auf diesem Gerät ausgeschaltet.';
    document.dispatchEvent(new CustomEvent('theogony:preferences-changed', { detail: state }));
  }
  function manage() {
    document.getElementById('preferences-manage').hidden = false;
    document.getElementById('preferences-accept').hidden = true;
    document.getElementById('preferences-save').hidden = false;
    document.getElementById('preferences-manage-button').textContent = 'Back';
  }
  function open(detailed = true, trigger = document.activeElement) {
    opener = trigger; sync();
    document.getElementById('preferences-manage').hidden = !detailed;
    document.getElementById('preferences-accept').hidden = detailed;
    document.getElementById('preferences-save').hidden = !detailed;
    document.getElementById('preferences-manage-button').textContent = detailed ? 'Back' : 'Manage preferences';
    if (!dialog.open) dialog.showModal();
  }
  function save(remember, count, close = true) {
    try {
      localStorage.setItem(memoryKey, remember ? 'enabled' : 'disabled');
      localStorage.setItem(analyticsKey, count && !privacySignal ? 'enabled' : 'disabled');
      if (!remember) readingData.forEach(key => localStorage.removeItem(key));
    } catch (_) {
      // Never start analytics if the consent decision could not be stored.
      try { localStorage.setItem(analyticsKey, 'disabled'); } catch (_) {}
      document.getElementById('preferences-error').hidden = false;
      document.getElementById('preferences-error').textContent = 'Your browser could not save these preferences. Optional statistics remain off.';
      return;
    }
    if (close && dialog.open) dialog.close();
    sync();
  }
  window.TheogonyPreferences = { open, getState, setAnalytics: value => save(getState().memory, value, false), disableReading: () => save(false, getState().analytics, false) };
  document.getElementById('preferences-accept').addEventListener('click', () => save(true, !privacySignal));
  document.getElementById('preferences-reject').addEventListener('click', () => save(false, false));
  document.getElementById('preferences-save').addEventListener('click', () => save(memory.checked, analytics.checked));
  document.getElementById('preferences-manage-button').addEventListener('click', () => {
    if (document.getElementById('preferences-manage').hidden) manage();
    else open(false, opener);
  });
  dialog.querySelector('[data-preferences-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { if (opener?.isConnected) opener.focus({ preventScroll: true }); });
  document.addEventListener('click', event => {
    const trigger = event.target.closest('[data-preferences-open]');
    if (trigger) { event.preventDefault(); open(true, trigger); }
  });
  document.getElementById('analytics-consent')?.addEventListener('change', event => save(getState().memory, event.target.checked, false));
  addEventListener('storage', event => { if ([null, memoryKey, analyticsKey].includes(event.key)) sync(); });
  sync();
  if (read(memoryKey) === null || (!privacySignal && read(analyticsKey) === null)) open(false);
})();
