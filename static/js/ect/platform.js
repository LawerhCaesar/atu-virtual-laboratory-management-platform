/* Platform-only presentation adapter. The supplied numerical runtime stays byte-for-byte intact. */
(() => {
  const container = document.getElementById('ect-lab');
  if (!container) return;
  const lab = window.AmachieECT.mount(container);
  const ui = lab.host.shadowRoot;
  const style = document.createElement('style');
  style.textContent = `:host{font-family:inherit}.lab{border-radius:20px;background:#f3f7fa}h1{font-family:Georgia,serif;font-weight:500}button,input,select{min-height:44px}.tour-target-highlight{outline:3px solid #d6a73b!important;outline-offset:5px!important}.quick-settings{margin:18px 0}.quick-settings summary{color:#145d7a}.quick-settings p{font-size:13px}.quick-settings .settings{grid-template-columns:repeat(3,minmax(0,1fr))}@media(max-width:560px){.quick-settings .settings{grid-template-columns:1fr 1fr}}`;
  ui.append(style);
  // Keep all settings and their atomic submit behavior in the original reference form.
  const form = ui.querySelector('#settings');
  const details = form.closest('details');
  details.id = 'ect-settings';
  details.classList.add('quick-settings');
  ui.querySelector('.controls').after(details);
  ui.querySelector('.grid').id = 'ect-readings';
  ui.querySelector('.plots').id = 'ect-plots';
  ui.querySelector('.tag').textContent = 'ECT sensor · supplied reference logic';
  // Preserve state on back-forward cache restoration, pause it on any departure.
  window.addEventListener('pagehide', () => lab.pause());
})();
