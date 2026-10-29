# Yankson engine starting virtual platform implementation

Implement Emmanuel Yankson Sackey's educational starting laboratory in the user's virtual platform. Use this complete file as the Codex task specification. The companion Programmer Guide explains the architecture and interfaces. Keep the approved title and ownership details: Emmanuel Yankson Sackey, 01250377M, supervisor Dr. Peter Nyanor.


## Four delivered files and self-contained model

The entire delivery consists of Yankson_Engine_Starting_Lab.slx, Yankson_User_Guide.pdf, this Markdown prompt, and Yankson_Programmer_Guide.pdf. Do not require loose MATLAB, JavaScript, adapter or CSV files beside the model. The SLX contains the controller, engine, scenarios, control desk, device adapter and original test evidence as embedded resources. Its PostLoadFcn unpacks helpers only into a process-specific system temporary folder and redirects Simulink cache generation there. Closing the model restores the previous cache settings. The working folder must contain only the four permanent deliverables after the model closes. MATLAB may temporarily create a .slx.autosave recovery file beside an open modified model; keep this protection enabled. Simulation caches and test outputs stay outside the delivery folder.

Open the SLX in MATLAB, then use getappdata(0,'YanksonBundleRoot') to locate temporary resources. The bundle is also inspectable using get_param('Yankson_Engine_Starting_Lab/11 Control desk','UserData').files. Each entry has path and bytes fields. The model itself runs without the guides; its guide button expects the user PDF beside the SLX. Double-click 11 Control desk to operate it; select ALL Run all 33 checks and click Run scenario to repeat native verification.

The JavaScript executable is fully included below in this prompt. Extract it into the destination platform's source tree; an extra JS file is not part of the four delivered project files. Use the Programmer Guide for the parameter and signal contracts. No ESP32 upload is requested. No platform repository has yet been integrated; this is the complete implementation brief and numerical reference for that work.

### Project scope

The purpose is advanced engineering education: develop and test virtual and physical versions of an authenticated starting demonstrator for the Toyota 1NZ engine. Stage one is this virtual model; stage two is the manually movable engine stand with a dedicated control panel, fuel tank, radiator and diagnostic connection. Proposed components are the usEFI/uaEFI 121-pin ECU (exact donor compatibility and pinout to be verified), SN65HVD230 3.3 V CAN transceiver, ESP32-WROOM-32, R503 fingerprint scanner, DFRobot voice recognition module and relay control system. The current virtual interface emulates their control-level signals; it is not a physical hardware validation.

The four objectives are virtual Simulink modelling, script integration into the virtual platform, construction of the physical demonstrator, and testing of both starting routes. Selected Concept One is a long matched fingerprint touch for direct start and a short matched touch before a fresh voice start. Mobile face ID, remote start, powered stand mobility and AI diagnostics are later extensions, not implemented features. Voice recognition identifies a command, not the speaker.

### Review boundaries

Keep the 0.01 s integration step, the two distinct starter/run outputs, original crank deadline, contact re-arming, voice authorization epoch and CAN validity checks. Read each recorded assertion before changing code. Require a written change reason and repeat the native and JavaScript checks after changing model logic. A successful deterministic simulation is not evidence of real recognition accuracy or physical engine calibration. Microphone access stalled on this computer; Windows exposed zero compatible fingerprint sensors. Real human voice and fingerprint testing remain unverified.

## Start here

1. Inspect the target platform repository and its existing navigation and design. If none is provided, prepare a local integration module and clearly state that integration into the target platform remains outstanding.
2. Extract the single JavaScript block between BEGIN_EXECUTABLE_ENGINE and END_EXECUTABLE_ENGINE into Yankson_Virtual_Engine.js. Preserve UTF-8, LF newlines and the final newline. Its SHA-256 is `7e34037a0d2c797f9594d8a9cca8dcb43ca1e8f60336bac74da27dfdb1360279`.
3. Run `node Yankson_Virtual_Engine.js --self-test`.
4. Run `node Yankson_Virtual_Engine.js --verify-csv "<embedded-runtime>/validation"` when the native CSV evidence is available. If absent, state that native parity was not repeated; never fabricate the reference from JavaScript itself.
5. Integrate the tested engine through its API. Do not replace unrelated platform features. Supply build, operation and acceptance evidence for the resulting integration.

## Required experience

Build a clear, colourful educational interface with these separate areas: finger contact and match status, voice authorization and its countdown, a five-state supervisor, engine RPM and CAN validity, separate starter/run-supply outputs, fault injection, equation explanations and recorded results. Hover tips must explain the subsystem, its equation mapping and an experiment. Layout must remain readable on narrower screens without overlapping controls.

Provide simulated short and long contacts, and explicitly label all simulated inputs. A long matched contact requests one start at 1.50 s. A matched short contact from 0.15 s to less than 1.50 s grants 10 s voice permission on release. A start event must be fresh, unique and associated with the current permission. Never treat command recognition as speaker authentication.

The native Windows adapter is a separate local process. The current machine exposes no compatible biometric sensor. Do not claim that a built-in fingerprint reader or browser WebAuthn result measures finger-hold duration. Do not silently replace a fingerprint with a PIN. A future supported reader must provide a documented identity result and, for real gesture timing, a separate contact signal. Microphone capture must be user initiated. Keep speech/device work away from the control clock and preserve the authorization epoch when results return.

## Numerical and integration rules

Use the exact 0.01 s sampled engine below. Preserve the one-step plant command delay and all 28 output columns. Use a worker or an explicit time accumulator; animation rate must not become the integration step. Pausing freezes model time and is visibly labelled. Reset and stop have priority. Monitoring loss never grants permission or extends a crank.

Use the parameter and signal contracts in the Programmer Guide. Invalid or stale RPM inhibits a new crank. During an accepted crank, lost CAN feedback leaves the original 3 s deadline active. Qualified running speed removes starter command while preserving run supply. Faults require deliberate recovery and a fresh request; there is no automatic retry.

The demo CAN ID 0x100 and byte format are not the installed rusEFI DBC. Torque, inertia, structural and supply values are provisional teaching assumptions. There is no physical actuator endpoint in this work. Do not add an ESP32 upload, remote engine start or live relay control as part of this platform implementation.

## Verification evidence

The native MATLAB R2024b suite passed 33 scenario cases with 316 assertions. The JavaScript engine matched 52,833 native samples and 1,479,324 scalar values, maximum absolute discrepancy about 5.12e-13. Native traces and inputs remain separate in validation. The synthetic offline speech pipeline check is not a human recognition-accuracy trial. Hardware verification unavailable on this machine remains not performed.

Keep deterministic replay, live interactive samples and human recognition trials distinguishable in exported results. Preserve case ID, model/configuration version, input timestamps, named outputs, expected result, observed result and pass/fail/not-performed status. Add UI tests for touch release, expired permission, stale device responses, rapid repeated requests, faults, paused execution and export. Inspect the actual interface visually before delivery.

## Executable reference

BEGIN_EXECUTABLE_ENGINE
```javascript
/* Emmanuel Yankson Sackey - Concept One. A faithful 10 ms virtual controller.
   No actuator interface. Engine and demo CAN parameters require calibration. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.YanksonEngine=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const defaults=[.01,.15,1.5,10,3,600,.2,.1,.02,1,0,50,8000,.25,8,25,.28,3,.35,100,.5,256];
const columns=['time_s','state','authorized','starter','rpm_CAN','CAN_valid','event_code','run_supply','rpm_plant','short_event','long_event','failed_match','touch_duration_s','start_request','voice_accepted','voice_reject_reason','running_confirmed','qualification_s','CAN_age_s','CAN_raw','CAN_frame_accepted','combustion','monitor_connected','crank_start_s','authentication_time_s','voice_sequence','voice_timestamp_s','hard_stop'];
const inputNames=['fingerPresent','matchEvent','voiceSequence','voiceCaptureTime','voiceID','emergencyStop','reset','powerGood','interlockOK','CANdrop','badID','badDLC','badRange','monitorConnected','ignitionAllowed','extraLoadNm','overrideRPM','useRPMoverride'];
function defaultInput(){return [0,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0];}
function validateParameters(p){if(!Array.isArray(p)||p.length!==22||!p.every(Number.isFinite))throw Error('22 finite parameters required');if(p[0]!==.01)throw Error('Validated model uses a 0.01 s step');if(!(p[1]>0&&p[2]>p[1]&&p[3]>0&&p[4]>0&&p[5]>p[11]&&p[6]>=p[0]&&p[7]>=p[8]&&p[8]>=p[0]&&p[9]>0&&p[12]>p[5]&&p[13]>0&&p[16]>0&&p[20]>0))throw Error('Invalid thresholds or physical parameters');return p;}
function createEngine(parameters=defaults){
 const p=validateParameters(parameters.slice());let k=0,previous=[0,0,0,0],cmdPrev=[0,0];
 let present=false,t0=0,matched=false,failed=false,fired=false,armed=false,Q=false,ta=-1e6,lastSeq=0;
 let omega=0,z=false,crankTime=0,lastFrame=-1e6,lastGood=-1e6,rpm=0,raw=0,flags=false,c=0;
 let q=0,runSupply=0,event=0,tStart=0;
 function step(u=defaultInput()){
  if(!Array.isArray(u)||u.length!==18||!u.every(Number.isFinite))throw Error('18 finite input values required');
  const t=k*p[0],hard=u[5]>0||u[6]>0||u[7]<.5||u[8]<.5;
  let short=0,long=0,bad=0,duration=0;
  if(hard){present=false;matched=false;failed=false;fired=false;armed=false;}
  else if(u[0]<.5){if(present){duration=t-t0;if(matched&&!failed&&!fired&&duration>=p[1]-1e-9&&duration<p[2]-1e-9)short=1;}present=false;matched=false;failed=false;fired=false;armed=true;}
  else if(armed){if(!present){present=true;t0=t;matched=false;failed=false;fired=false;}duration=t-t0;if(u[1]<0){failed=true;matched=false;bad=1;}if(u[1]>0&&!failed)matched=true;if(matched&&!failed&&!fired&&duration>=p[2]-1e-9){long=1;fired=true;}}
  let req=0,accepted=0,reason=0,fresh=0;const newVoice=u[2]>lastSeq;if(newVoice)lastSeq=u[2];
  if(hard||bad>0||previous[0]>=2)Q=false;if(t-ta>=p[3]-1e-9)Q=false;if(short>0&&!hard&&previous[0]<2){Q=true;ta=t;}
  let A=Q&&t-ta>=0&&t-ta<p[3]-1e-9;
  if(newVoice){fresh=+(u[3]>ta+1e-9&&u[3]<=t+1e-9&&t-u[3]<=p[20]+1e-9);if(u[4]!==1)reason=3;else if(!A)reason=1;else if(!fresh)reason=2;else{accepted=1;req=1;}}
  if(long>0){req=1;Q=false;}if(req)Q=false;if(hard||bad>0){req=0;accepted=0;A=false;}
  // Explicit one-sample actuation delay, followed by the chapter's Euler balance.
  if(cmdPrev[0]>.5)crankTime+=p[0];else crankTime=0;
  if(cmdPrev[1]<.5||u[14]<.5)z=false;
  const rpmBefore=omega*60/(2*Math.PI);
  if(cmdPrev[1]>.5&&u[14]>.5&&crankTime>=p[18]-1e-9&&rpmBefore>=p[19])z=true;
  const torque=p[14]*cmdPrev[0]+p[15]*(+z)-p[16]*omega-p[17]-u[15];omega=Math.max(0,omega+p[0]/p[13]*torque);
  let plantRPM=omega*60/(2*Math.PI);if(u[17]>.5)plantRPM=Math.max(0,u[16]);
  let frameAccepted=0;
  if(t-lastFrame>=p[8]-1e-9){lastFrame=t;if(u[9]<.5){const id=p[21]+(u[10]>.5?1:0),dlc=8-4*(u[11]>.5?1:0);raw=Math.round((plantRPM-p[10])/p[9]);if(u[12]>.5)raw=65535;raw=Math.max(0,Math.min(65535,raw));const decoded=p[9]*(raw%256+256*Math.floor(raw/256))+p[10];flags=id===p[21]&&dlc===8&&decoded>=0&&decoded<=p[12];if(flags){rpm=decoded;lastGood=t;frameAccepted=1;}}}
  const age=Math.max(0,t-lastGood),valid=flags&&age<=p[7]+1e-9;
  if(valid&&rpm>=p[5]&&u[6]<.5&&u[7]>.5)c+=p[0];else c=0;const qualified=c>=p[6]-1e-9;
  // Same transition priorities as the native five-state Stateflow supervisor.
  const hardChart=u[5]>0||u[7]<.5||u[8]<.5,reset=u[6]>0&&u[5]<.5&&u[7]>.5&&u[8]>.5;
  if(k>0){
   if(q===4){if(reset){q=0;event=30;}}
   else if(hardChart){q=4;event=20;}
   else if(q!==0&&reset){q=0;event=30;}
   else if(q===0||q===1){if(qualified&&u[6]<.5){q=3;event=11;}else if(req>0&&valid&&rpm<=p[11]&&u[6]<.5){q=2;tStart=t;event=10;}else if(q===0&&Q&&u[6]<.5){q=1;event=1;}else if(q===1&&!Q){q=0;event=2;}}
   else if(q===2){if(qualified){q=3;event=11;}else if(t-tStart>=p[4]-1e-9){q=4;event=21;}}
   else if(q===3&&valid&&rpm<=p[11]){q=0;event=3;}
  }
  runSupply=+(q===2||q===3);const starter=+(q===2&&!hard&&t-tStart<p[4]-1e-9&&!qualified),run=+(runSupply>.5&&!hard);
  const row=[t,q,+Q,starter,rpm,+valid,event,run,plantRPM,short,long,bad,duration,req,accepted,reason,+qualified,c,Math.min(age,1e6),raw,frameAccepted,+z,u[13],tStart,ta,u[2],u[3],+hard];
  previous=[q,runSupply,event,tStart];cmdPrev=[starter,run];k++;return row;
 }
 return {step,get time(){return k*p[0];},parameters:p.slice(),columns:columns.slice()};
}
function simulate(inputs,p=defaults){const e=createEngine(p);return inputs.map(row=>{if(row.length!==19||Math.abs(row[0]-e.time)>1e-7)throw Error('Input time does not match fixed-step clock');return e.step(row.slice(1));});}
function engineering(starter=0){const Pout=4.68,R=.0175*4/1.5,Wd=2*180*9.81,I=(40**4-34**4)/12,F=Wd/2,M=F*700/4;return [Pout,Pout/(.85*12)+.15*starter,R,5*R,25*R,Wd,Wd/3,I,M*20/I,F*700**3/(48*200000*I),180*9.81*.4/.65];}
function metrics(a,i,r,g,c,s,n){const counts=[a,i,r,g,c,s,n];if(counts.some(v=>!Number.isInteger(v)||v<0)||a>i||r>g||c>s)throw Error('Invalid trial counts');return {FAR_percent:i?100*a/i:null,FRR_percent:g?100*r/g:null,voice_percent:s?100*c/s:null,upper95:n?1-.05**(1/n):null};}
return {createEngine,simulate,engineering,metrics,defaults:defaults.slice(),columns,inputNames,defaultInput,validateParameters};
});
if(typeof module==='object'&&require.main===module){
 const fs=require('node:fs'),path=require('node:path'),api=module.exports;
 const mode=process.argv[2];
 if(mode==='--verify-csv'){
  const folder=process.argv[3];if(!folder)throw Error('Supply the Simulink validation directory');
  const files=fs.readdirSync(folder).filter(f=>f.endsWith('_inputs.csv')).sort();let samples=0,maxError=0;const cases=[];
  for(const f of files){const id=f.replace('_inputs.csv',''),parse=s=>s.trim().split(/\r?\n/).map(l=>l.split(',').map(Number));const inputs=parse(fs.readFileSync(path.join(folder,f),'utf8'));const expected=parse(fs.readFileSync(path.join(folder,id+'_trace.csv'),'utf8').split(/\r?\n/).slice(1).join('\n'));const actual=api.simulate(inputs);if(expected.length!==actual.length)throw Error(id+' row count');let worst=0;
   for(let i=0;i<actual.length;i++)for(let j=0;j<28;j++){const err=Math.abs(expected[i][j]-actual[i][j]);worst=Math.max(worst,err);const tolerance=1e-8*Math.max(1,Math.abs(expected[i][j]));if(err>tolerance)throw Error(`${id} sample ${i}, ${api.columns[j]} MATLAB=${expected[i][j]} JS=${actual[i][j]}`);}
   cases.push({id,rows:actual.length,maxAbsoluteError:worst});samples+=actual.length;maxError=Math.max(maxError,worst);
  }
  const report={passed:true,scenarios:cases.length,samples,values:samples*28,maxAbsoluteError:maxError,cases};fs.writeFileSync(path.join(folder,'javascript_parity.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }else if(mode==='--self-test'){
  let checks=0;const assert=(c,m)=>{if(!c)throw Error(m);checks++;};
  let e=api.createEngine(),rows=[];for(let i=0;i<=1600;i++){let u=api.defaultInput();if(i>=50&&i<220)u[0]=1;if(i===50)u[1]=1;rows.push(e.step(u));}
  assert(rows[200][3]===1,'long touch');assert(rows.at(-1)[1]===3,'running');assert(rows.at(-1)[3]===0,'release');assert(rows.at(-1)[7]===1,'run supply');assert(rows.reduce((a,r)=>a+r[10],0)===1,'one shot');
  e=api.createEngine();rows=[];for(let i=0;i<=600;i++){let u=api.defaultInput();u[14]=0;if(i>=50&&i<220)u[0]=1;if(i===50)u[1]=1;rows.push(e.step(u));}
  assert(rows[499][3]===1&&rows[500][3]===0,'deadline');assert(rows.at(-1)[1]===4,'latched fault');assert(Math.abs(api.engineering()[7]-101972)<1e-9,'beam equation');assert(api.metrics(0,0,0,0,0,0,0).FAR_percent===null,'undefined rates');
  let rejected=false;try{api.createEngine([1]);}catch{rejected=true;}assert(rejected,'invalid parameter rejection');console.log(JSON.stringify({passed:true,checks}));
 }else console.log('Use --self-test or --verify-csv "path/to/validation". Browser API: YanksonEngine.createEngine().step(input18).');
}
```
END_EXECUTABLE_ENGINE
