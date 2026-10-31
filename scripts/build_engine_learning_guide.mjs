import fs from 'node:fs';import vm from 'node:vm';import {SPEC} from '../static/js/engine-live-data/spec.mjs';
const ui=fs.readFileSync(new URL('../static/js/engine-live-data/ui.mjs',import.meta.url),'utf8'), w=fs.readFileSync(new URL('../static/js/engine-live-data/workspace.mjs',import.meta.url),'utf8');
const literal=name=>vm.runInNewContext('('+ui.match(new RegExp('const '+name+' = (\\{[\\s\\S]*?\\n  \\});'))[1]+')');
const sections=vm.runInNewContext(w.match(/const sections=(\[\[.*?\]\]);/s)[1]);fs.writeFileSync(new URL('./engine-guide-content.json',import.meta.url),JSON.stringify({sections,labels:literal('labels'),meanings:literal('meanings'),signals:[...SPEC.inputs,...SPEC.outputs],source:SPEC.packageRevision}));
