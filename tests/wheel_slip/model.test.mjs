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
