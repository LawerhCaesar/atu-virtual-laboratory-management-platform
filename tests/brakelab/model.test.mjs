import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {transformSync} from "esbuild";
import {DEFAULT_BRAKE_INPUTS as D,DEFAULT_BRAKE_CALIBRATION as C,FIELDS,OUTPUTS,calculateBrakeAllocation as calculate,validateInputs} from "../../static/js/brakelab/model.mjs";
import {BrakeSimulation,playbackFrame} from "../../static/js/brakelab/controller.mjs";
const fixture=JSON.parse(readFileSync(new URL("./source-contract.json",import.meta.url)));
const compiled=transformSync(fixture.referenceTypeScript,{loader:"ts",format:"esm",target:"es2022"}).code;
const reference=await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
const near=(actual,expected,tolerance=1e-9)=>assert.ok(Math.abs(actual-expected)<=tolerance*Math.max(1,Math.abs(expected)),`${actual} != ${expected}`);
const run=changes=>calculate({...D,...changes});

test("all supplied baseline outputs, inputs and calibration match the canonical contract",()=>{
  assert.deepEqual(D,reference.DEFAULT_BRAKE_INPUTS); assert.deepEqual(C,reference.DEFAULT_BRAKE_CALIBRATION);
  assert.equal(FIELDS.length,11);assert.equal(OUTPUTS.length,25);for(const f of FIELDS)assert.ok(f.purpose.length>35);
  const r=run();
  const expected={requestedDecelerationMps2:1.4,requestedForceN:2100,requestedWheelTorqueNm:651,
    vehicleSpeedMps:60/3.6,wheelSpeedRpm:513.403042232,motorSpeedRpm:4620.627380087,
    torqueForceLimitN:4807.741935484,powerForceLimitN:3000,batteryForceLimitN:2863.636363636,
    regenerativeForceN:2100,frictionForceN:0,mechanicalRegenPowerKw:35,batteryChargePowerKw:30.8,
    regenerativeCurrentA:88,regenerativePercent:100,frictionPercent:0,forceBalanceResidualN:0};
  for(const [key,value] of Object.entries(expected))near(r[key],value);
  assert.equal(r.activeLimitCode,"DRIVER_DEMAND");assert.equal(r.activeLimitLabel,"Driver braking demand");
  near(r.visual.stopTimeEstimateS,11.90476190476);near(r.visual.stopDistanceEstimateM,99.20634920635);
  assert.equal(r.visual.animationDurationS,8);assert.deepEqual(r.warnings,[]);
});

test("reference equivalence and physical allocation bounds across 2500 seeded operating points",()=>{
  let seed=20261027;
  const random=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return (seed>>>0)/4294967296;};
  for(let n=0;n<2500;n++){
    const input={...D};
    for(const f of FIELDS)input[f.key]=typeof f.value==="boolean" ? random()>.5 : f.min+random()*(f.max-f.min);
    if(n%17===0)input.regenEnabled=.5;
    const before=JSON.stringify({input,C}), actual=calculate(input), expected=reference.calculateBrakeAllocation(input);
    assert.equal(JSON.stringify({input,C}),before);assert.deepEqual(actual,calculate(input));
    for(const [key] of OUTPUTS){assert.ok(Number.isFinite(actual[key]));near(actual[key],expected[key]);}
    for(const key of Object.keys(actual.visual))near(actual.visual[key],expected.visual[key]);
    assert.equal(actual.activeLimitCode,expected.activeLimitCode);assert.equal(actual.activeLimitLabel,expected.activeLimitLabel);
    near(actual.requestedForceN,actual.regenerativeForceN+actual.frictionForceN);
    assert.ok(actual.regenerativeForceN>=0&&actual.regenerativeForceN<=actual.requestedForceN+1e-9);
    assert.ok(actual.frictionForceN>=0&&Math.abs(actual.forceBalanceResidualN)<.001);
    assert.ok(actual.batteryChargePowerKw<=actual.allowedBatteryPowerKw+1e-9);
    assert.ok(actual.regenerativeCurrentA<=input.chargeCurrentLimitA+1e-9);
    assert.deepEqual(JSON.parse(JSON.stringify(actual)),actual);
  }
});

test("speed, SOC and cold/hot thresholds and both ramps follow the supplied formulas",()=>{
  for(const speed of [0,7.2]){const r=run({vehicleSpeedKph:speed});assert.equal(r.speedFactor,0);assert.equal(r.regenerativeForceN,0);near(r.frictionForceN,r.requestedForceN);}
  near(run({vehicleSpeedKph:12.6}).speedFactor,.5);near(run({vehicleSpeedKph:18}).speedFactor,1);
  near(run({batterySocPct:80}).socFactor,1);near(run({batterySocPct:87.5}).socFactor,.5);
  for(const soc of [95,100])assert.equal(run({batterySocPct:soc}).allowedBatteryPowerKw,0);
  for(const temp of [-5,55])assert.equal(run({batteryTempC:temp}).temperatureFactor,0);
  for(const temp of [15,25,40])assert.equal(run({batteryTempC:temp}).temperatureFactor,1);
  for(const temp of [5,47.5])near(run({batteryTempC:temp}).temperatureFactor,.5);
});

test("every final active-limit code, zero limits and deterministic ties are exercised",()=>{
  const cases=[ [{brakeDemand:0},"NO_BRAKING"],[{regenEnabled:false},"REGEN_DISABLED"],
    [{vehicleSpeedKph:7.2},"LOW_SPEED"],[{batterySocPct:95},"BATTERY_SOC"],[{batteryTempC:55},"BATTERY_TEMPERATURE"],
    [{},"DRIVER_DEMAND"],[{motorRegenTorqueLimitNm:20},"MOTOR_TORQUE"],[{motorRegenPowerLimitKw:5},"MOTOR_POWER"],
    [{chargeCurrentLimitA:10},"BATTERY_CURRENT"],[{chargePowerLimitKw:1},"BATTERY_POWER"],
    [{brakeDemand:1,batterySocPct:90},"BATTERY_SOC"],[{brakeDemand:1,batteryTempC:0},"BATTERY_TEMPERATURE"],
    [{motorRegenTorqueLimitNm:0,motorRegenPowerLimitKw:0,chargePowerLimitKw:0},"MOTOR_TORQUE"] ];
  for(const [input,code] of cases)assert.equal(run(input).activeLimitCode,code);
  const off=run({regenEnabled:false});assert.equal(off.regenerativeForceN,0);near(off.frictionForceN,2100);
  const partial=run({regenEnabled:.5});near(partial.regenerativeForceN,1050);near(partial.frictionForceN,1050);
  for(const key of ["chargeCurrentLimitA","chargePowerLimitKw","motorRegenTorqueLimitNm","motorRegenPowerLimitKw"]){const r=run({[key]:0});assert.equal(r.regenerativeForceN,0);near(r.frictionForceN,2100);}
});

test("normalisation is explicit, out-of-range values are not silently rejected, epsilon is retained",()=>{
  const input={...D,brakeDemand:2,batterySocPct:-20,vehicleSpeedKph:-5,regenEnabled:2};
  const r=calculate(input);near(r.requestedForceN,5250);assert.equal(r.vehicleSpeedMps,0);assert.equal(r.socFactor,1);
  assert.ok(r.warnings.some(w=>w.includes("raw")));assert.ok(r.warnings.some(w=>w.includes("normalised")));
  assert.equal(input.brakeDemand,2);assert.equal(validateInputs({...D,vehicleMassKg:4500}).valid,true);
  const tiny=run({brakeDemand:.5/(1500*3.5)});near(tiny.requestedForceN,.5);near(tiny.regenerativePercent,50);
  assert.equal(tiny.activeLimitCode,"NO_BRAKING");assert.equal(tiny.frictionPercent,0);
});

test("invalid inputs, enable factors, calibration and derived overflow never produce invalid JSON",()=>{
  for(const f of FIELDS.filter(f=>f.key!=="regenEnabled"))for(const value of [NaN,Infinity,-Infinity])assert.throws(()=>run({[f.key]:value}));
  for(const value of [NaN,Infinity,"true",null,undefined])assert.throws(()=>run({regenEnabled:value}));
  for(const key of ["vehicleMassKg","batteryVoltageV"])for(const value of [0,-1])assert.throws(()=>run({[key]:value}));
  for(const key of ["chargeCurrentLimitA","chargePowerLimitKw","motorRegenTorqueLimitNm","motorRegenPowerLimitKw"])assert.throws(()=>run({[key]:-1}));
  for(const key of Object.keys(C))assert.throws(()=>calculate(D,{...C,[key]:NaN}));
  for(const changes of [{wheelRadiusM:0},{gearRatio:0},{regenEfficiency:1.1},{drivetrainEfficiency:0},
    {minimumSpeedMps:0},{forceEpsilonN:0},{fullRegenSpeedMps:2},{socStopPct:80},{coldFullC:-5},{hotFullC:60}])assert.throws(()=>calculate(D,{...C,...changes}));
  assert.throws(()=>run({vehicleMassKg:1e308,brakeDemand:1}),/non-finite/);
  assert.throws(()=>run({vehicleSpeedKph:1e308}),/non-finite/);
  const custom={...C,wheelRadiusM:.35,gearRatio:8,regenEfficiency:.8};
  const actual=calculate(D,custom), expected=reference.calculateBrakeAllocation(D,custom);
  for(const [key] of OUTPUTS)near(actual[key],expected[key]);
});

test("scaled playback reaches a complete stop and suppresses flow without overwriting operating point",()=>{
  const sim=new BrakeSimulation(), other=new BrakeSimulation();sim.run(D);
  const snapshot=JSON.stringify(sim.result);const first=sim.frame();near(first.speedKph,60);assert.ok(first.regenIntensity>0);
  sim.tick(4);const half=sim.frame();near(half.speedKph,30);near(half.distanceM,sim.result.visual.stopDistanceEstimateM*.75);
  assert.notEqual(first.wheelAngleDeg,half.wheelAngleDeg);sim.pause();const elapsed=sim.elapsedS;sim.tick(1);near(sim.elapsedS,elapsed);
  sim.resume();sim.tick(4);assert.equal(sim.running,false);near(sim.frame().speedKph,0);
  near(sim.frame().distanceM,sim.result.visual.stopDistanceEstimateM);assert.equal(sim.frame().regenIntensity,0);assert.equal(sim.frame().chargeIntensity,0);
  assert.equal(JSON.stringify(sim.result),snapshot);assert.equal(other.elapsedS,0);
  sim.run({...D,regenEnabled:false});assert.equal(sim.frame().regenIntensity,0);assert.ok(sim.frame().frictionIntensity>0);
  sim.run(D,false);assert.equal(sim.running,false);near(sim.frame().speedKph,60);
  const payload=sim.payload();payload.result.visual.stopTimeEstimateS=0;payload.inputs.vehicleMassKg=1;
  assert.ok(sim.result.visual.stopTimeEstimateS>0);assert.equal(sim.inputs.vehicleMassKg,1500);
  sim.fail(new Error("Synthetic failure"));assert.throws(()=>sim.payload(),/last-valid/);sim.reset();assert.equal(sim.error,null);
});

test("no-braking sentinels and stationary input are not interpreted as an instantaneous stop",()=>{
  const r=run({brakeDemand:0});assert.equal(r.visual.stopTimeEstimateS,0);assert.equal(r.visual.stopDistanceEstimateM,0);
  const f=playbackFrame(r,10);near(f.speedKph,60);assert.equal(f.progress,0);assert.equal(f.regenIntensity,0);
  const sim=new BrakeSimulation();sim.run({...D,brakeDemand:0});assert.equal(sim.running,false);assert.match(sim.mode,/No braking/);
  sim.run({...D,vehicleSpeedKph:0});assert.equal(sim.running,false);assert.equal(sim.mode,"Stationary");
});
