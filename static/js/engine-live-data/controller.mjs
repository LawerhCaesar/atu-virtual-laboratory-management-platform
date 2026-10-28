import { DEFAULT_INPUTS, INPUTS, STATES, STATE_NAMES, DT, acceptInputs,
  initialState, previewEngineModel, stepEngineModel } from './reference.mjs';
import { SPEC } from './spec.mjs';

export const STEP = DT;
export const HISTORY_SECONDS = 60;
const EXTRA_PRESETS = [
  {name:'Rich oxygen response',values:{O2SensorVoltage:.90}},
  {name:'Low battery',values:{BatteryVoltage:9}},
  {name:'Cold engine signals',values:{ECT1Voltage:3.5,ECT2Voltage:3.5}},
  {name:'Slow cranking',values:{EngineSpeed:200}},
];
export const PRESETS = [...SPEC.presets,...EXTRA_PRESETS];

/** Single owner of accepted inputs, sampled output, request pulses and history. */
export class EngineSimulation {
  constructor(){this.reset();}
  reset(){
    this.rawInputs={...DEFAULT_INPUTS};this.internal={...initialState(),simulationTime:0};
    this.running=false;this.history=[];this.events=[];this.pulses={};this.clampedFields={};
    this.result=previewEngineModel(this.rawInputs);this.pending=false;
  }
  setInput(name,value){
    if(!Object.hasOwn(INPUTS,name))throw new Error('Unknown engine input');
    if(name==='EmergencyStop'&&this.rawInputs.EmergencyStop&&!value)return;
    const {inputs,clampedFields}=acceptInputs({...this.rawInputs,[name]:value});
    this.rawInputs=inputs;this.clampedFields[name]=clampedFields[name];this.pending=true;
  }
  clearEmergency(){this.rawInputs.EmergencyStop=0;this.pending=true;}
  loadPreset(index){
    const preset=PRESETS[index];if(!preset)throw new Error('Unknown preset');
    const emergency=this.rawInputs.EmergencyStop;
    this.reset();this.rawInputs={...DEFAULT_INPUTS,...preset.values,EmergencyStop:emergency};
    this.result=previewEngineModel(this.rawInputs);this.events.push({time:0,message:`Loaded ${preset.name}; experiment reset and paused.`});
  }
  pulse(name){
    if(!['StartRequest','StopRequest'].includes(name))throw new Error('Not a momentary input');
    if(!this.running)throw new Error('Run or resume the simulation first.');
    if(name==='StartRequest'){
      if(this.internal.engineState!==STATES.OFF)return;
      const reasons=[];if(!this.rawInputs.IgnitionSwitch)reasons.push('ignition is off');
      if(!this.rawInputs.StartAuthorisation)reasons.push('authorisation is off');
      if(this.rawInputs.BatteryVoltage<9.5)reasons.push('battery below 9.5 V');
      if(this.rawInputs.EmergencyStop)reasons.push('emergency is latched');
      if(reasons.length)this.events.push({time:this.internal.simulationTime,message:`Start blocked: ${reasons.join('; ')}.`});
      this.rawInputs.StopRequest=0;delete this.pulses.StopRequest;
    }else{this.rawInputs.StartRequest=0;delete this.pulses.StartRequest;}
    this.rawInputs[name]=1;this.pulses[name]=10;this.pending=true;
  }
  emergencyStop(){this.rawInputs.EmergencyStop=1;this.pending=true;}
  step(){
    const previous=this.internal.engineState;
    const snapshot=stepEngineModel(this.rawInputs,this.internal);
    this.internal={...snapshot.internalState,simulationTime:snapshot.simulationTime};
    this.result=snapshot;this.pending=false;
    const row={SimulationTime:snapshot.simulationTime,...snapshot.inputs,...snapshot.outputs};
    this.history.push(row);if(this.history.length>1201)this.history.shift();
    if(previous!==this.internal.engineState){
      let reason='';const i=snapshot.inputs;
      if(this.internal.engineState===STATES.SHUTDOWN){
        reason=i.EmergencyStop?'Emergency stop':i.StopRequest?'Stop requested':!i.IgnitionSwitch?'Ignition off':i.BatteryVoltage<8.5?'Battery below crank threshold':'Crank timeout';
      }else if(this.internal.engineState===STATES.PRIME)reason='Safe start conditions met';
      else if(this.internal.engineState===STATES.CRANK)reason='Priming complete';
      else if(this.internal.engineState===STATES.RUN)reason='Imposed RPM reached 500';
      else reason='Shutdown interval complete';
      this.events.push({time:snapshot.simulationTime,message:`${STATE_NAMES[previous]} → ${STATE_NAMES[this.internal.engineState]}: ${reason}.`});
    }
    if(this.events.length>100)this.events.shift();
    for(const name of Object.keys(this.pulses))if(--this.pulses[name]<=0){this.rawInputs[name]=0;delete this.pulses[name];}
    return snapshot;
  }
  csv(){
    const columns=['SimulationTime',...Object.keys(INPUTS),...Object.keys(this.result.outputs).filter(k=>k!=='EngineStateLabel'),'EngineStateLabel'];
    return [columns.join(','),...this.history.map(row=>columns.map(key=>row[key]).join(','))].join('\r\n');
  }
}
