// Never expose the legacy source layout as a fallback for a failed module load.
try {
  await import(window.YanksonAssetURL('./teaching.mjs', import.meta.url));
} catch (error) {
  const status=document.getElementById('ys-layout-loading');
  status.setAttribute('role','alert');
  status.textContent='The starting workspace could not load. Reload this page. If this persists, report the browser error to support.';
  console.error('Starting workspace initialization failed',error);
}
