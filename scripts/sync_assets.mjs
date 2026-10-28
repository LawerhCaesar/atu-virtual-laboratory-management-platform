// Reproducible, local-only third-party stylesheet generation.
import { copyFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { build } from 'esbuild';
const root = fileURLToPath(new URL('../', import.meta.url));
await mkdir(`${root}static/vendor/bootstrap`, { recursive: true });
for (const name of ['bootstrap.min.css', 'bootstrap.min.css.map']) {
  await copyFile(`${root}node_modules/bootstrap/dist/css/${name}`, `${root}static/vendor/bootstrap/${name}`);
}
await copyFile(`${root}node_modules/bootstrap/LICENSE`, `${root}static/vendor/bootstrap/LICENSE`);
console.log('Bootstrap stylesheet and licence copied to protected build inputs.');
await build({
  entryPoints: [`${root}frontend/engine-cutaway.mjs`],
  outfile: `${root}static/js/engine-live-data/cutaway.bundle.mjs`,
  bundle: true, minify: true, format: 'esm', target: 'es2022', legalComments: 'eof',
});
await mkdir(`${root}static/vendor/three`, { recursive: true });
await copyFile(`${root}node_modules/three/LICENSE`, `${root}static/vendor/three/LICENSE`);
console.log('Local 3D engine bundle and Three.js licence generated.');
await build({
  entryPoints: [`${root}frontend/fuel-delivery-3d.mjs`],
  outfile: `${root}static/js/fuel-delivery/fuel-3d.bundle.mjs`,
  bundle: true, minify: true, format: 'esm', target: 'es2022', legalComments: 'eof',
});
console.log('Local fuel-delivery 3D bundle generated.');

await build({entryPoints:[`${root}static/js/bless/engine.ts`], outfile:`${root}static/js/bless/engine.mjs`,format:"esm",target:"es2022"});
