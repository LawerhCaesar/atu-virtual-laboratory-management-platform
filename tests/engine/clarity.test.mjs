import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {EngineSimulation} from '../../static/js/engine-live-data/controller.mjs';
import {evidencePackage} from '../../static/js/engine-live-data/evidence.mjs';
import {initialState,stepEngineModel,DEFAULT_INPUTS,STATES} from '../../static/js/engine-live-data/reference.mjs';
const close=(a,b,t=1e-7)=>assert.ok(Math.abs(a-b)<=t,`${a} != ${b}`);
const records=[];
function running(change={}){return stepEngineModel({...DEFAULT_INPUTS,IgnitionSwitch:1,...change},{engineState:STATES.RUN,elapsedInState:1,sampleIndex:30}).outputs;}
for(const [name,changes,expected] of [
 ['warm',{}, {ECT1Temp:90,ECT2Temp:87,LambdaEstimate:1,STFT:0,BaseInjectorPW:1.679,InjectorPW:1.679,TargetIdleRPM:750,RPMError:-50,IdleControlDuty:24.5,IgnitionTiming:9.25,FanDuty:28.5714286,WaterPumpDuty:70}],
 ['lean',{O2SensorVoltage:.1},{LambdaEstimate:1.1225,STFT:14.7,InjectorPW:1.925813}],
 ['rich',{O2SensorVoltage:.9},{LambdaEstimate:.8425,STFT:-18.9,InjectorPW:1.361669}],
 ['idle-load',{EngineSpeed:650,AccessoryLoad:80},{TargetIdleRPM:750,RPMError:100,IdleControlDuty:51,IgnitionTiming:10.9}],
 ['high-speed',{EngineSpeed:2500,ThrottlePosition:25,ManifoldPressure:70,AccessoryLoad:80},{IdleActive:0,IdleControlDuty:0,IgnitionTiming:14,InjectorPW:3.425}],
 ['ac',{ACRequest:1},{FanDuty:35,WaterPumpDuty:70}],
 ['hot',{ECT1Voltage:.4,ECT2Voltage:.5},{ECT1Temp:118.3333333,ECT2Temp:111.6666667,SensorDisagreement:0,FanDuty:100,WaterPumpDuty:100}],
 ['hot-disagreement',{ECT1Voltage:.4,ECT2Voltage:2},{SensorDifference:55.8333333,SensorDisagreement:1,FanDuty:100,WaterPumpDuty:100}],
 ['isolated-disagreement',{ECT2Voltage:2},{ECT1Temp:90,ECT2Temp:62.5,SensorDifference:27.5,ControlTemperature:90,SensorDisagreement:1,FanDuty:100,WaterPumpDuty:100}],
 ['cold-low-voltage',{ECT1Voltage:3.5,ECT2Voltage:3.5,BatteryVoltage:10.5},{ECT1Temp:25,ClosedLoopActive:0,WarmupEnrichment:22.5,BatteryCompensation:.594,InjectorPW:2.784425,TargetIdleRPM:1059.375,IdleControlDuty:43.0625}],
 ['cold-clamped',{ECT1Voltage:3.5,ECT2Voltage:3.5,BatteryVoltage:20},{BatteryCompensation:0,InjectorPW:2.056775}],
])test('brief engine anchor '+name,()=>{const o=running(changes);for(const[k,v]of Object.entries(expected))close(o[k],v);records.push({name,changes,expected,observed:o});});
for(const [state,threshold,ticks]of [[STATES.PRIME,2,40],[STATES.CRANK,5,101],[STATES.SHUTDOWN,.5,11]])test('approved floating-point threshold '+state,()=>{
 const u={...DEFAULT_INPUTS,IgnitionSwitch:1,EngineSpeed:200};let s={...initialState(),engineState:state,elapsedInState:0};const rows=[];
 for(let i=1;i<=ticks+1;i++){const r=stepEngineModel(u,s);rows.push({tick:i,elapsed:r.outputs.StateElapsedTime,state:r.outputs.EngineState});s=r.internalState;}
 assert.equal(rows[ticks-2].state,state);assert.notEqual(rows[ticks-1].state,state);assert.equal(rows[ticks-1].elapsed,0);
 records.push({name:'timing-'+state,thresholdS:threshold,expectedTick:ticks,boundaryRows:rows.slice(ticks-3)});
});
for(const state of [STATES.PRIME,STATES.CRANK,STATES.RUN])for(const [key,value]of [['EmergencyStop',1],['StopRequest',1],['IgnitionSwitch',0]])test(`precedence ${state} ${key}`,()=>{
 const r=stepEngineModel({...DEFAULT_INPUTS,IgnitionSwitch:1,EngineSpeed:800,[key]:value},{engineState:state,elapsedInState:5,sampleIndex:100});assert.equal(r.outputs.EngineState,STATES.SHUTDOWN);assert.equal(r.outputs.StarterState+r.outputs.InjectionEnable+r.outputs.IgnitionEnable+r.outputs.FuelPumpState,0);if(key==='EmergencyStop')assert.equal(r.outputs.FanDuty+r.outputs.WaterPumpDuty,0);
});
test('evidence package keeps identical CSV values, units, UUID, retained window and source hash',()=>{
 const s=new EngineSimulation(),id=s.runId;for(let i=0;i<1500;i++)s.step();
 const p=evidencePackage(s,'2026-11-16T00:00:00.000Z');assert.equal(p.csv.content,s.csv());assert.equal(p.signalDictionary.length,46);assert(p.signalDictionary.every(x=>x.unit));assert.equal(p.window.totalSamples,1500);assert.equal(p.window.retainedSamples,1201);assert(p.window.truncated);assert.equal(p.runId,id);assert.equal(p.sampleIntervalS,.05);
 assert.match(p.build.sourceSha256['reference.mjs'],/^[a-f0-9]{64}$/);close(p.window.lastTimeS-p.window.firstTimeS,60);
 s.reset();assert.notEqual(s.runId,id);assert.equal(s.events.length,0);records.push({name:'export',metadata:p});
});
test.after(()=>{fs.mkdirSync('test-results/corrections',{recursive:true});fs.writeFileSync('test-results/corrections/engine-acceptance.json',JSON.stringify(records,null,2));});
