import test from "node:test";
import assert from "node:assert/strict";
import {DEFAULTS,PRESETS,simulate,validateConfig} from "../../static/js/wheel-slip/model.mjs";

test("fixed-step first update follows the documented resistance equation",()=>{
  const c={...DEFAULTS,durationS:2,brakeAfter:0,throttleAfter:0};
  const result=simulate(c), v=80/3.6, resistance=.015*1500*9.81+.5*1.225*.65*v*v;
  assert.equal(result.samples.length,2001);
  assert.ok(Math.abs(result.samples[1].vehicleSpeedKph-(v-.001*resistance/1500)*3.6)<1e-10);
  assert.equal(result.samples[1].tyreForceN,0);
  assert.equal(result.samples[0].vehicleSpeedKph,80);
});

test("ABS and TCS presets are deterministic and controller switches matter",()=>{
  const runs=Object.fromEntries(Object.entries(PRESETS).map(([name,c])=>[name,simulate(c)]));
  const braking=runs["ABS emergency braking"], noAbs=runs["Braking without ABS"], launch=runs["TCS low-friction launch"], noTcs=runs["Launch without TCS"];
  assert.deepEqual(simulate(PRESETS["ABS emergency braking"]),braking);
  assert.deepEqual(new Set(braking.samples.map(s=>s.controllerMode)),new Set([0,1,2,3]));
  assert.deepEqual(new Set(launch.samples.map(s=>s.controllerMode)),new Set([0,-1,-2,-3]));
  assert.equal(noAbs.metrics.absActiveTimeS,0);assert.equal(noTcs.metrics.tcsActiveTimeS,0);
  assert.ok(braking.metrics.absActiveTimeS>0);assert.ok(launch.metrics.tcsActiveTimeS>0);
  assert.notEqual(braking.metrics.stoppingDistanceM,noAbs.metrics.stoppingDistanceM);
  assert.ok(noTcs.metrics.peakDriveSlip>launch.metrics.peakDriveSlip);
  assert.notEqual(simulate({...DEFAULTS, roadMu:.8}).metrics.stoppingDistanceM,braking.metrics.stoppingDistanceM);
});

test("brake priority, validation and finite boundary results",()=>{
  const priority=simulate({...DEFAULTS,durationS:2,brakeStepTimeS:0,throttleStepTimeS:0,throttleAfter:1});
  assert.ok(priority.samples.every(s=>s.driveTorqueNm===0));
  assert.ok(priority.warnings.some(w=>w.includes("priority")));
  assert.equal(simulate({...DEFAULTS,durationS:2,brakeAfter:0}).metrics.stoppingTimeS,null);
  assert.ok(validateConfig({...DEFAULTS,roadMu:0}).roadMu);
  assert.ok(validateConfig({...DEFAULTS,durationS:2,brakeStepTimeS:3}).brakeStepTimeS);
  assert.ok(validateConfig({...DEFAULTS,timeStepS:.01}).timeStepS);
  assert.ok(validateConfig({...DEFAULTS,durationS:2.0001}).durationS);
  for(const config of [
    {...DEFAULTS,durationS:2,initialSpeedKph:0,roadMu:.05,vehicleMassKg:500,wheelRadiusM:.15,wheelInertiaKgm2:.05,maxBrakeTorqueNm:5000},
    {...DEFAULTS,durationS:2,initialSpeedKph:160,roadMu:1.2,vehicleMassKg:3500,wheelRadiusM:.5,wheelInertiaKgm2:5,maxDriveTorqueNm:5000},
  ])for(const row of simulate(config).samples)for(const value of Object.values(row))if(typeof value==="number")assert.ok(Number.isFinite(value));
});

import {visualState} from '../../static/js/wheel-slip/visual-state.mjs';
test('visual feedback uses the preceding 1 ms state and recorded wheel motion',()=>{
 const r=simulate(DEFAULTS),index=r.samples.findIndex(s=>s.controllerMode===3),v=visualState(r,index);
 assert.ok(index>0);assert.equal(v.feedback,r.samples[index-1]);assert.equal(v.row,r.samples[index]);assert.ok(Math.abs(v.outputTimeS-v.feedbackTimeS-.001)<1e-12);assert.ok(v.feedback.brakeSlip>.20);assert.equal(v.pumpIllustration,true);assert.equal(v.wheelAngleRad,r.samples[index].wheelAngleRad);assert.equal(v.sensorOmegaRadS,v.feedback.wheelPeripheralSpeedKph/3.6/DEFAULTS.wheelRadiusM);assert.equal(v.requestedBrakeNm,1800);
 for(const mode of [0,1,2]){const i=r.samples.findIndex(s=>s.controllerMode===mode);assert.equal(visualState(r,i).pumpIllustration,false);}
});
test('TCS reductions and controller-disabled braking never claim a hydraulic pump output',()=>{
 for(const name of ['TCS low-friction launch','Launch without TCS','Braking without ABS']){const r=simulate(PRESETS[name]);assert.ok(r.samples.every((_,i)=>!visualState(r,i).pumpIllustration));if(name==='TCS low-friction launch'){const index=r.samples.findIndex(s=>s.controllerMode===-3),v=visualState(r,index);assert.ok(v.feedback.driveSlip>.18);assert.equal(v.driveCue,'Reduce drive torque');assert.equal(v.requestedDriveNm,1200);assert.equal(v.row.brakeTorqueNm,0);}}
});
test('presentation leaves original simulation samples and exports unchanged',()=>{const r=simulate(DEFAULTS),copy=JSON.stringify(r);for(const i of [0,1,1000,1500,12000])visualState(r,i);assert.equal(JSON.stringify(r),copy);const zero=visualState(r,0);assert.equal(zero.feedbackTimeS,0);assert.equal(zero.outputTimeS,0);});
