import test from 'node:test';
import assert from 'node:assert/strict';
import { EngineSimulation,PRESETS } from '../../static/js/engine-live-data/controller.mjs';
import {DEFAULT_INPUTS,STATES,INPUTS,acceptInputs,initialState,stepEngineModel,ectTemperature} from '../../static/js/engine-live-data/reference.mjs';
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`);
function reference(overrides={},end=3){let state=initialState(),result;for(let i=0;i<=Math.round(end/.05);i++){result=stepEngineModel({...DEFAULT_INPUTS,IgnitionSwitch:1,StartAuthorisation:1,StartRequest:1,...overrides},state);state=result.internalState;}return result;}
test('reference checkpoints and strict input contracts',()=>{
 for(const [v,t] of [[4.8,-20],[4.3,0],[3.5,25],[2.5,50],[1.5,75],[1,90],[.6,105],[.3,125],[.2,135]])close(ectTemperature(v),t);
 for(const [key,def] of Object.entries(INPUTS)){assert.equal(acceptInputs({...DEFAULT_INPUTS,[key]:def.max+2}).inputs[key],def.max);assert.equal(acceptInputs({...DEFAULT_INPUTS,[key]:def.min-2}).inputs[key],def.min);}
 for(const bad of ['',null,NaN,Infinity,[],{},'12'])assert.throws(()=>acceptInputs({...DEFAULT_INPUTS,BatteryVoltage:bad}),TypeError);
});
test('warm, lean, rich, cold, idle and hot reference equations',()=>{
 let r=reference(),o=r.outputs;assert.equal(r.simulationTime,3);assert.equal(r.internalState.sampleIndex,60);assert.equal(o.EngineState,3);
 for(const[k,v]of Object.entries({InjectorPW:1.679,LambdaEstimate:1,STFT:0,EngineLoad:10.605882352941178,TargetIdleRPM:750,RPMError:-50,IdleControlDuty:24.5,IgnitionTiming:9.25,ECT1Temp:90,ECT2Temp:87,FanDuty:28.57142857142857,WaterPumpDuty:70}))close(o[k],v);
 o=reference({O2SensorVoltage:.1}).outputs;close(o.InjectorPW,1.925813);close(o.STFT,14.7);
 o=reference({O2SensorVoltage:.9}).outputs;close(o.InjectorPW,1.361669);close(o.STFT,-18.9);
 o=reference({ECT1Voltage:3.5,ECT2Voltage:3.5}).outputs;close(o.InjectorPW,2.056775);close(o.TargetIdleRPM,1059.375);close(o.WaterPumpDuty,35);
 o=reference({BatteryVoltage:13,EngineSpeed:620,ManifoldPressure:45,AccessoryLoad:80,ACRequest:1}).outputs;close(o.InjectorPW,2.010);close(o.IdleControlDuty,52.8);close(o.FanDuty,35);
 o=reference({EngineSpeed:900,ThrottlePosition:3,ManifoldPressure:38,ECT1Voltage:.55,ECT2Voltage:.62,AccessoryLoad:20,ACRequest:1}).outputs;close(o.ECT1Temp,108.33333333333333);close(o.WaterPumpDuty,97.5);close(o.FanDuty,100);
});
test('state priority, sample time and cooling edge cases',()=>{
 let r=reference({EngineSpeed:200},7.4);assert.equal(r.outputs.EngineState,4);close(r.outputs.StateElapsedTime,.35);
 r=stepEngineModel({...DEFAULT_INPUTS,IgnitionSwitch:1,StartAuthorisation:1,StartRequest:1,StopRequest:1},initialState());assert.equal(r.outputs.EngineState,1);close(r.simulationTime,0);
 r=stepEngineModel({...DEFAULT_INPUTS,ECT1Voltage:.6,ECT2Voltage:.6},initialState());close(r.outputs.FanDuty,100);close(r.outputs.WaterPumpDuty,60);
 r=stepEngineModel({...DEFAULT_INPUTS,ECT1Voltage:1,ECT2Voltage:1.5},initialState());assert.equal(r.outputs.SensorDisagreement,0);
 r=stepEngineModel({...DEFAULT_INPUTS,ECT1Voltage:1,ECT2Voltage:2,EmergencyStop:1},initialState());assert.equal(r.outputs.SensorDisagreement,1);assert.equal(r.outputs.FanDuty,0);assert.equal(r.outputs.WaterPumpDuty,0);
});
test('paused edits preserve sampled values, pulses count samples and CSV is historical',()=>{
 const s=new EngineSimulation();assert.equal(s.history.length,0);assert.equal(s.csv().split('\r\n').length,1);
 s.setInput('IgnitionSwitch',1);s.setInput('StartAuthorisation',1);assert.equal(s.result.inputs.IgnitionSwitch,0);assert.throws(()=>s.pulse('StartRequest'));
 s.running=true;s.pulse('StartRequest');for(let i=0;i<61;i++)s.step();assert.equal(s.result.outputs.EngineState,STATES.RUN);assert.equal(s.history[0].SimulationTime,0);assert.equal(s.rawInputs.StartRequest,0);
 s.running=false;const before=structuredClone(s.result);s.setInput('O2SensorVoltage',.1);assert.deepEqual(s.result,before);assert.equal(s.history.at(-1).O2SensorVoltage,.45);
 s.step();close(s.result.outputs.InjectorPW,1.925813);assert.equal(s.history.at(-1).O2SensorVoltage,.1);
 s.emergencyStop();assert.equal(s.result.outputs.EngineState,STATES.RUN);s.step();assert.equal(s.result.outputs.EngineState,STATES.SHUTDOWN);assert.equal(s.result.outputs.FanDuty,0);
 s.loadPreset(0);assert.equal(s.rawInputs.EmergencyStop,1);assert.equal(s.history.length,0);s.clearEmergency();assert.equal(s.rawInputs.EmergencyStop,0);
 const rich=PRESETS.findIndex(x=>x.name==='Rich oxygen response');s.setInput('BatteryVoltage',12);s.loadPreset(rich);assert.equal(s.rawInputs.BatteryVoltage,13.8);assert.equal(s.rawInputs.O2SensorVoltage,.9);
});
test('rolling history retains exact sampled window and 30 output signals',()=>{
 const s=new EngineSimulation();s.running=true;for(let i=0;i<1400;i++)s.step();assert.equal(s.history.length,1201);close(s.history.at(-1).SimulationTime-s.history[0].SimulationTime,60);
 const lines=s.csv().split('\r\n'),columns=lines[0].split(',');assert.equal(lines.length,1202);assert.equal(columns.length,46);assert.ok(columns.includes('ActualRPM'));assert.ok(columns.includes('SafeStartCondition'));assert.ok(columns.includes('EngineStateLabel'));
});
test('low battery, zero RPM in RUN and A/C during shutdown follow the written contract',()=>{
 let r=reference({BatteryVoltage:9});assert.equal(r.outputs.EngineState,0);assert.equal(r.outputs.InjectorPW,0);close(r.outputs.FanDuty,28.57142857142857);
 const running={engineState:STATES.RUN,elapsedInState:1,sampleIndex:100};
 r=stepEngineModel({...DEFAULT_INPUTS,IgnitionSwitch:1,EngineSpeed:0},running);assert.equal(r.outputs.EngineState,STATES.RUN);assert.equal(r.outputs.ActualRPM,0);
 r=stepEngineModel({...DEFAULT_INPUTS,IgnitionSwitch:1,ACRequest:1,ECT1Voltage:3.5,ECT2Voltage:3.5},{engineState:STATES.SHUTDOWN,elapsedInState:0,sampleIndex:4});assert.equal(r.outputs.EngineState,STATES.SHUTDOWN);assert.equal(r.outputs.FanDuty,35);
});
