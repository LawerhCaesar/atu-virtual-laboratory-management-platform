import fs from 'node:fs';
import {examples,exampleScenario,runScenario,exportResultsCsv,MODEL_HASH} from '../../static/js/bless/engine.mjs';
const dir=process.argv[2]||'test-results/bless/parity';fs.mkdirSync(dir,{recursive:true});
const scenarios=[];
for(const spec of examples){const s=exampleScenario(spec.id);const r=runScenario(s,()=>false,spec.id);for(const key of ['comparison','electric','diesel','road'])fs.writeFileSync(`${dir}/${spec.id}__${key}.csv`,exportResultsCsv(r,key));scenarios.push({id:spec.id,duration_s:s.duration_s,fixed_step_s:1,parameters:r.scenario.parameters});console.log(spec.id,r.samples.length);}
fs.writeFileSync(`${dir}/result_manifest.json`,JSON.stringify({source_model_sha256:MODEL_HASH,scenarios},null,2));
