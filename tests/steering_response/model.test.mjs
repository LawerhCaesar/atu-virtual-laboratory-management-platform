import test from 'node:test';
import assert from 'node:assert/strict';
import {DEFAULT_VEHICLE as V,DEFAULT_SCENARIO as S,simulateSteeringResponse as simulate,OUTPUT_VECTOR_ORDER,platformVector,resultCsv,validateInputs,steeringAtTime,sampleAtTime} from '../../static/js/steering-response/model.mjs';
const near=(actual,expected,tolerance)=>assert.ok(Math.abs(actual-expected)<=tolerance,`${actual} differs from ${expected}`);
test('reference RK4 case matches all eleven outputs and maintains contract order',()=>{
 const r=simulate();assert.equal(r.samples.length,1001);assert.equal(r.solver.internalSubsteps,1);assert.deepEqual(r.parameters,V);assert.deepEqual(r.scenario,S);
 const expected=[4.7027,-.17837,1.36797,.13945,200.615,41.876,153.963,51.465,1172.54,879.41,16];
 r.platformVector.forEach((v,i)=>near(v,expected[i],Math.max(.00001,Math.abs(expected[i])*.001)));
 assert.deepEqual(r.outputVectorOrder,['yawRateDegPerS','sideslipDeg','lateralAccelerationMps2','lateralAccelerationG','turningRadiusM','headingDeg','xM','yM','frontLateralForceN','rearLateralForceN','steeringWheelAngleDeg']);
 assert.deepEqual(r.platformVector,platformVector(r.final));assert.equal(r.final.timeS,10);assert.equal(r.samples[0].xM,0);
});
test('zero steering, sign symmetry, amplitude and payload response',()=>{
 const zero=simulate(V,{...S,steeringAmplitudeDeg:0});for(const key of ['yawRateDegPerS','sideslipDeg','lateralAccelerationMps2','yM','frontLateralForceN','rearLateralForceN'])near(zero.final[key],0,1e-12);near(zero.final.xM,60/3.6*10,1e-8);
 const positive=simulate(),negative=simulate(V,{...S,steeringAmplitudeDeg:-1}),double=simulate(V,{...S,steeringAmplitudeDeg:2});
 for(const key of ['yawRateDegPerS','sideslipDeg','lateralAccelerationMps2','headingDeg','yM'])near(negative.final[key],-positive.final[key],1e-10);
 near(double.final.yawRateDegPerS,2*positive.final.yawRateDegPerS,1e-8);
 const payload=simulate({...V,payloadKg:500});assert.notEqual(payload.samples[150].yawRateDegPerS,positive.samples[150].yawRateDegPerS);
});
test('profile generators, partial final steps and CSV sample parity',()=>{
 assert.equal(steeringAtTime(.9,S),0);assert.equal(steeringAtTime(1,S),1);
 near(steeringAtTime(2,{...S,profile:'sine'}),1,1e-12);
 assert.equal(steeringAtTime(2.1,{...S,profile:'doublet'}),-1);assert.equal(steeringAtTime(3.1,{...S,profile:'doublet'}),0);
 const r=simulate(V,{...S,durationS:2.005});assert.equal(r.final.timeS,2.005);assert.ok(r.samples.every((row,i)=>i===0||row.timeS>r.samples[i-1].timeS));
 assert.equal(sampleAtTime(r,2.005),r.final);assert.equal(sampleAtTime(r,2.004),r.final);assert.equal(sampleAtTime(r,-1),r.samples[0]);assert.equal(sampleAtTime(r,100),r.final);
 const lines=resultCsv(r).split('\r\n');assert.equal(lines.length,r.samples.length+1);const keys=lines[0].split(','),last=lines.at(-1).split(',').map(Number);for(const key of OUTPUT_VECTOR_ORDER)assert.equal(last[keys.indexOf(key)],r.final[key]);
});
test('protections, low-speed numerical stability and finite output',()=>{
 const r=simulate({...V,speedKmh:0});assert.equal(r.effective.speedMps,.5);assert.ok(r.solver.internalSubsteps>1);assert.ok(r.warnings.some(x=>x.includes('Speed protection')));assert.ok(r.samples.every(row=>Object.values(row).every(Number.isFinite)));
 const mass=simulate({...V,baseMassKg:0},{...S,durationS:.2,stepTimeS:.1});assert.equal(mass.effective.totalMassKg,100);assert.ok(mass.warnings.some(x=>x.includes('Mass protection')));
 const high=simulate({...V,baseMassKg:60000},{...S,durationS:.2,stepTimeS:.1});assert.equal(high.effective.totalMassKg,50000);
});
test('invalid inputs and excessive numerical work fail clearly',()=>{
 for(const patch of [{speedKmh:-1},{yawInertiaKgM2:0},{cgToFrontM:NaN},{rearCorneringStiffnessNPerRad:0}])assert.throws(()=>simulate({...V,...patch}));
 for(const patch of [{timeStepS:.1},{stepTimeS:20},{durationS:0},{profile:'unknown'},{sineFrequencyHz:0},{durationS:100000}])assert.ok(Object.keys(validateInputs(V,{...S,...patch})).length);
 assert.throws(()=>simulate({...V,yawInertiaKgM2:1e-12}),/numerical work/);
});
