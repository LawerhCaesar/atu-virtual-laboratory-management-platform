// Reproducible, local-only third-party stylesheet generation.
import { copyFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
await mkdir(`${root}static/vendor/bootstrap`, { recursive: true });
for (const name of ['bootstrap.min.css', 'bootstrap.min.css.map']) {
  await copyFile(`${root}node_modules/bootstrap/dist/css/${name}`, `${root}static/vendor/bootstrap/${name}`);
}
await copyFile(`${root}node_modules/bootstrap/LICENSE`, `${root}static/vendor/bootstrap/LICENSE`);
console.log('Bootstrap stylesheet and licence copied to protected build inputs.');
