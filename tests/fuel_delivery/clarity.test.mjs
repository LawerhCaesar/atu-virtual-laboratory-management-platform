import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {FuelSimulation} from '../../static/js/fuel-delivery/controller.mjs';
import {DEFAULTS} from '../../static/js/fuel-delivery/model.mjs';
const records=[];
function solve(change={}){const s=new FuelSimulation({...DEFAULTS,...change});s.start();while(s.running)s.tick();return s;}
const close=(a,b,t=1e-6)=>assert.ok(Math.abs(a-b)<=t,`${a} != ${b} ± ${t}`);
for(const [name,input,expected] of [
 ['cruise',{},{finalFuelMgPerEvent:20.408163,injectorPulseWidthMs:8.470956,injectorDutyCyclePct:17.647826,predictedLambda:1,fuelFlowGps:1.700680,cumulativeFuelG:51.020408}],
 ['scale-098',{fuelOptimisationScale:.98},{finalFuelMgPerEvent:20,injectorPulseWidthMs:8.321538,injectorDutyCyclePct:17.336537,predictedLambda:1.020408,fuelFlowGps:1.666667,cumulativeFuelG:50}],
 ['rich-095',{measuredLambda:.95,fuelOptimisationScale:.95},{stftPct:-6,ltftPct:-.54,predictedLambda:1.069982}],
 ['pressure-voltage',{fuelRailPressureKPa:200,batteryVoltageV:10},{injectorPulseWidthMs:10.470,injectorDutyCyclePct:21.813,finalFuelMgPerEvent:20.408163}],
 ['saturation',{engineSpeedRpm:4500,engineLoadPct:95,airFlowGps:95,brakeTorqueNm:200,injectorRatedFlowCcMin:150,fuelRailPressureKPa:200,batteryVoltageV:10},{injectorPulseWidthMs:31.068,rawDutyCyclePct:116.5,injectorDutyCyclePct:100}],
])test('brief fuel acceptance '+name,()=>{const s=solve(input),o=s.result.outputs;for(const [key,value]of Object.entries(expected))close(o[key],value,name==='pressure-voltage'?.001:name==='saturation'?.05:name==='rich-095'?.001:1e-6);if(name==='rich-095')assert(s.result.status.warnings.some(w=>w.includes('lambda')));if(name==='saturation')assert(s.result.status.warnings.some(w=>w.includes('Saturat')||w.includes('saturat')));assert.equal(s.result.integrationVector.length,8);records.push({name,inputs:s.inputs,expected,observed:o,vector:s.result.integrationVector});});
test('contexts distinguish edited preview, retained history and fresh comparison without altering reset/resume',()=>{
 const s=solve();const old=structuredClone(s.history),id=s.runId;
 s.edit({...s.inputs,fuelOptimisationScale:.98});assert.deepEqual(s.history,old);
 assert.equal(s.contexts().currentPreview.differsFromLastRecordedSample,true);
 assert.equal(s.contexts().lastRecordedRun.lastInputs.fuelOptimisationScale,1);
 assert.equal(s.evidence().inputs.fuelOptimisationScale,.98);
 s.compare();assert.equal(s.contexts().freshComparison.label,'Fresh comparison');assert.deepEqual(s.history,old);assert.equal(s.runId,id);
 s.start();assert.notEqual(s.runId,id);assert.equal(s.state.ltftPct,0);assert.equal(s.state.cumulativeFuelG,0);assert.equal(s.history.length,0);
 s.tick();s.running=false;const before=s.state.simulationTimeS;s.resume();s.tick();close(s.state.simulationTimeS,before+.1);
});
test.after(()=>{fs.mkdirSync('test-results/corrections',{recursive:true});fs.writeFileSync('test-results/corrections/fuel-acceptance.json',JSON.stringify(records,null,2));});
