# Codex follow-up: practical voice, touch and circuit laboratory

Implement this follow-up in the existing ATU Authenticated Engine Starting module. The requested outcome is a useful educational platform where a person can speak a command, use an available contact/authentication device, inspect the circuit and change parameters to understand why starting is accepted or rejected. A page of buttons that merely inject predetermined successful events is insufficient.

This is an implementation request for the next Codex session. The features below are requested changes, not features already delivered or verified.

## Ownership, source and working boundary

- Student: Emmanuel Yankson Sackey; index 01250377M; supervisor Dr. Peter Nyanor.
- Existing route: `/virtual-lab/ice/authenticated-engine-starting/`.
- Existing staging page: https://atu-virtual-laboratory-staging.onrender.com/virtual-lab/ice/authenticated-engine-starting/
- Upstream reference: https://github.com/LawerhCaesar/atu-virtual-laboratory-management-platform
- Uploaded source: `atu-virtual-laboratory-management-platform-main.zip`. On the owner's computer it is at `E:\Downloads\atu-virtual-laboratory-management-platform-main.zip`.
- Work in an isolated copy or fork. The owner explicitly said: **“Don't try to push to my repo.” Do not push to the upstream repository.** Do not deploy or modify the staging service. Return reviewable changes and evidence; publication requires a separate instruction. If GitHub access is unavailable, use the uploaded archive without asking the owner to resolve GitHub before doing local work.
- Preserve the existing Django authentication, academic roles, route, navigation, branding and other laboratory modules. This task concerns Emmanuel's engine-starting module.
- Do the implementation and appropriate tests. Do not stop at another proposal, describe planned controls as functioning, or substitute a new unrelated website.

## Verified starting point

The live page and uploaded source were inspected on 30 October 2026. The current module has simulated short/long-touch buttons, simulated voice events, a five-state supervisor, RPM graph, CAN fault switches and exports. It lacks microphone input, a customizable command, actual press-duration interaction, device capability checks and an interactive component circuit.

The following files exist in the supplied repository:

- `templates/core/yankson.html` — current page.
- `static/js/yankson/ui.js` — browser controls, simulation timing, graph and exports.
- `static/js/yankson/engine.js` — pure reference model.
- `static/css/yankson.css` — module styling.
- `docs/yankson.md` — integration and verification notes.
- `docs/reference/yankson/implementation.md` and `programmer-guide.pdf` — earlier handover.
- `tests/test_yankson.py` — reference hash and route-access checks.
- `tests/e2e/test_yankson_ui.py` — existing interaction and accessibility tests.

The live and uploaded `engine.js` both match SHA-256 `7e34037a0d2c797f9594d8a9cca8dcb43ca1e8f60336bac74da27dfdb1360279`. Its complete source is retained in the appendix below. Use this as the baseline; improve the interface and adapters without silently replacing the model.

## 1. Make the starting experience practical

Present a simple guided sequence: **Check devices → Authorize → Speak or hold → Observe the engine**. Put the starting controls and engine response first. Keep detailed engineering controls available in clearly labelled circuit and CAN sections.

Preserve both approved starting routes:

1. A matched short contact, from 0.15 s up to but excluding 1.50 s, grants 10 s of permission on release. A fresh recognized voice command within that permission requests a start.
2. A matched contact held for at least 1.50 s generates one direct start request. Continued contact must not repeatedly start the engine.

Voice recognition identifies a command; it does not identify the speaker. Do not quietly remove the fingerprint/identity requirement from the approved concept. If real identity verification is unavailable, offer a clearly selected **practice identity** mode so the learner can still test actual microphone and contact inputs. Label the identity result as simulated while labelling the microphone/contact source accurately.

Use separate status indicators for **voice source**, **contact source**, **identity source**, and **virtual engine state**. Replace the current blanket “all inputs are simulated” notice when live microphone or physical contact input is actually in use. Keep simulated input controls in a test section.

## 2. Add real voice input and personalization

- The default command is **“Hey Start”**.
- Provide an editable command field, Save command, Restore default, and a visible display of the active command. Retain the preference for that user/browser without exposing it to other users sharing the platform.
- Provide clear **Enable microphone / Listen** and **Stop listening** controls. Request microphone access through a deliberate user action. Display Listening, recognized words, command match/mismatch, and the reason a start is accepted or refused.
- Use the browser's supported speech-recognition API, or an explicitly configured supported alternative. Check runtime support and permissions; do not assume every laptop/browser can perform recognition. Some browser services require network access and may process audio remotely. Explain the actual recognition mode before enabling it; do not claim offline recognition when using a remote service.
- Compare the complete recognized phrase with the saved command, allowing documented case, whitespace and punctuation normalization. Do not use substring matching that accepts “do not hey start” or a different longer sentence.
- Handle permission denied, no microphone, no speech, recognition unavailable, network failure, cancellation and repeated Listen clicks. A failure must not become an accepted command. Do not store raw audio by default.
- Accept final recognition results only once. Bind each listening request to the current experiment generation and authorization epoch. Reject delayed results after expiry, reset, stop, a changed command, a new authorization, or navigation away. Preserve the reference model's timestamp, sequence and freshness rules.
- Real device interaction must use normal time. Do not let accelerated replay turn a real 0.4 s press into a long press, or change the time allowed to speak. Explain and enforce how live input differs from accelerated recorded replay.

## 3. Detect devices and measure actual contact duration honestly

Add a **Check this device** action and report supported, unavailable, denied or unknown states separately for microphone recognition, touchscreen/pointer contact and any supported identity-verification interface.

### Built-in fingerprint reader

Investigate the actual supported OS/vendor interface. Ordinary browser WebAuthn does not supply continuous fingerprint finger-down/finger-up timing or a fingerprint image. A platform-authenticator availability result does not prove that a fingerprint reader is usable, and successful device verification can use a PIN or face instead. Do not label a generic device-verification result as confirmed fingerprint recognition.

If a documented local bridge or device SDK is available, verify that it provides both an identity result and, where required, a separate contact signal. Measure a hold from actual contact events. Do not time how long an OS authentication dialog remains open and call it finger-contact duration. Do not install a new bridge, expose a local service, or alter OS authentication settings silently.

When the available reader cannot expose contact timing, state this clearly and offer the usable alternatives below. Device verification plus a separate on-screen hold may be offered only with those two actions labelled separately.

### Touchscreen, pointer and external reader

- On a touchscreen, provide a large touch target and measure actual down-to-up duration. Show elapsed hold time, the short/long thresholds and the resulting classification.
- On a non-touchscreen computer, allow a mouse/trackpad press-and-hold or accessible keyboard hold, labelled as that input method. A trackpad click is not a fingerprint scan.
- Handle pointer capture, release outside the target, pointer cancellation, lost focus, multiple contacts, keyboard repeat and page visibility changes. An interrupted contact must not accidentally grant permission or produce a delayed start.
- An ordinary touchscreen cannot be turned into a fingerprint scanner by an “online calibration” image. Contact-threshold calibration may adjust press timing for teaching, but must not claim biometric capability.
- If an external R503 or another reader is connected, use its documented transport and contact/identity interfaces. Only show it as connected after a real capability/communication check. Do not implement a fake success callback as a hardware adapter.
- Keep measured contact duration, identity result, source and simulation timestamps visible in the experiment record. Never present a practice identity checkbox as biometric evidence.

## 4. Build an interactive component and circuit workbench

Represent the intended physical components clearly:

1. Toyota 1NZ engine and starter.
2. usEFI/uaEFI 121-pin ECU, with the exact board revision and pinout to be confirmed.
3. ESP32-WROOM-32 controller.
4. SN65HVD230 3.3 V CAN transceiver.
5. R503 fingerprint reader.
6. DFRobot voice-recognition module; verify its exact model before giving a pin-specific connection.
7. Separate starter and run relay circuits, protected drivers and coil suppression.
8. Battery, fuse, regulated supplies, common reference, emergency stop and stand interlocks.

Show the actual logical paths:

- Fingerprint match plus finger-presence/contact timing → controller.
- Recognized voice-command ID → controller.
- Controller CAN interface → transceiver → CANH/CANL pair → ECU, with RPM feedback returning to the controller.
- Controller start output → suitable protected relay driver → starter relay/solenoid path.
- Separate run output → run-supply path, retained after starter release.
- Supply and emergency-stop/interlock paths that permit or inhibit operation.

Use a neat interactive schematic with readable terminals, distinct power/data/command/feedback colours, a legend, hover/focus explanations, and visible active signal paths. This must be more informative than a static controller-to-engine arrow.

Allow learners to inspect components and connect/disconnect relevant virtual wires or select valid terminal pairs. Include a known-good circuit preset and a clear reset. Detect incomplete/wrong wiring with a specific explanation, such as “ECU RPM feedback cannot reach the controller because CANL is disconnected.” Show the effect on permission, cranking and starter release.

Do not invent the ECU's 121-pin assignments or confuse module labels with IC pin numbers. Use functional terminal names until the actual hardware revision is verified. Consult manufacturer documentation for voltage levels, interfaces, relay drivers and CAN termination. Do not depict an ESP32 GPIO directly powering a relay coil or starter motor.

Tie each supported circuit fault to an implemented model effect. If a virtual preflight checker blocks an incomplete circuit, identify that as a teaching check rather than claiming the physical ECU automatically detects every broken wire. If analog circuit behaviour is not calculated, label the workbench as a functional circuit simulation. Do not claim SPICE-level voltages, currents, EMC behaviour or mechanical calibration from logical switches.

## 5. Make parameters and CAN experiments understandable

Expose bounded, explained controls for contact thresholds, authorization duration, maximum crank time, stopped/running RPM thresholds, running qualification duration, CAN freshness and frame period. Provide units, default values and Restore defaults. Update all labels, progress bars and countdowns from the actual selected parameters; the current UI hardcodes some defaults.

Apply configuration changes at a defined safe experiment boundary. Validate parameter relationships, keep the integration step fixed at 0.01 s, cancel old device requests, and require a fresh start request. Distinguish calibrated values from teaching assumptions.

Create guided CAN experiments with **Change → Expected effect → Observed effect → Why**:

- Missing RPM feedback before starting: a new crank is inhibited.
- CAN loss during an accepted crank: the original crank deadline remains active; no fresh timeout is started.
- Wrong identifier, wrong payload length, invalid RPM or stale frames: explain which validity check failed.
- Brief RPM spike: starter stays engaged until valid speed has remained above threshold for the qualification period.
- Qualified running speed: starter releases while run supply remains on.
- Failed ignition: cranking reaches the deadline and latches a fault.
- Monitoring/network display loss: local authorization and crank protection continue.
- Supply, emergency-stop or interlock failure: outputs are removed and deliberate recovery is required.

Explain that a valid CAN frame is not proof of user identity or cryptographic message authenticity. The current concept uses identity/voice authorization and RPM feedback as distinct conditions. Keep CAN identifiers and payload encoding labelled as demonstration settings until matched to the selected ECU's documentation.

Show a plain-language reason beside the engine state: for example, “Permission granted—say Hey Start within 8.2 s,” “Wrong command,” “RPM feedback is stale,” or “Running speed confirmed—starter released.”

## 6. Preserve the Simulink model contract

Use the existing reference model to drive the actual simulation, graphs, component states and explanations. Do not make an engine animation start independently of its supervisor.

Default model settings:

| Setting | Default |
| --- | --- |
| Integration step | 0.01 s |
| Short-contact minimum | 0.15 s |
| Long-contact threshold | 1.50 s |
| Voice permission | 10 s |
| Voice maximum event age | 0.50 s |
| Maximum cranking duration | 3 s from original crank acceptance |
| Stopped-speed upper bound | 50 RPM |
| Running qualification | At least 600 RPM continuously for 0.20 s |
| CAN frame period / freshness | 0.02 s / 0.10 s |
| Demonstration CAN ID | 0x100 |

Retain the five states, the one-sample plant-command delay, separate starter/run outputs, one request per long contact, release-to-rearm behaviour, fault recovery rules, 18 model inputs and 28 recorded outputs. Keep numerical integration independent of rendering rate. New circuit/device metadata can accompany the model signals without silently changing their meaning.

Keep the pure model unchanged where possible. If a new circuit behaviour genuinely requires a model change, document the equation/interface change and repeat applicable native-model and browser-reference checks. Do not weaken or delete the existing engine-hash test merely to conceal a changed model.

## 7. Verify the experience before handover

Extend the existing tests around the real user journey. At minimum cover:

1. Default “Hey Start” acceptance after current authorization; rejection without it.
2. Personalized command save/restore, successful match, mismatch and refusal of misleading longer phrases.
3. Device capability results and denied/unavailable/error paths.
4. Actual measured press boundaries, long one-shot behaviour, failed identity, cancellation, release and rearming.
5. Voice results arriving after expiry, reset, stop, command change or a different authorization epoch.
6. Missing, incorrect and restored virtual connections and their documented model effects.
7. Each CAN/RPM experiment above, including preservation of the original crank deadline.
8. Separate starter/run behaviour, emergency stop and deliberate recovery.
9. Parameters validated, restored and recorded; displayed countdowns consistent with them.
10. Live timing versus paused/accelerated replay, hidden tabs and repeated controls.
11. Responsive layout, keyboard operation, clear focus/labels, hover alternatives and no overlapping content.
12. CSV/JSON exports retaining full model data, selected parameters, input provenance, circuit configuration and meaningful event reasons.

Run the existing reference self-test, relevant Django tests and module browser tests. The repository already documents their commands. Use synthetic speech/device events for repeatable automated adapter tests, then record separately any human microphone or real reader trial performed. Passing a mocked speech test is not evidence that a microphone worked; a practice match is not a real fingerprint trial.

The earlier native package passed 33 scenarios and 316 assertions; its JavaScript matched 52,833 native samples across 28 signals. These are historical baseline results, not a claim that this revision has passed them. If native CSVs are needed, open the supplied SLX in MATLAB and use `getappdata(0,'YanksonBundleRoot')` to locate its embedded `validation` folder. Never generate supposed native reference traces from the JavaScript being tested.

## 8. Deliver a clear, reviewable result

- Return the changed source or a patch from the isolated working copy/fork, a local run procedure, screenshots and a concise test record.
- Update `docs/yankson.md`, the module walkthrough and relevant tests to match actual behaviour. Locate existing walkthrough registration before changing it.
- Report working live features, practice-only features and unavailable hardware separately. State clearly if real human microphone or fingerprint testing was not performed.
- Preserve the four-file delivery convention in `F:\Scripts for codex\Yankson`: one SLX, one user-guide PDF, this Codex Markdown file and one programmer-guide PDF. Keep source checkout, test evidence and backups outside that folder. Refresh the guides only when the revised implementation is complete and verified.
- Do not push to the original repository or deploy the staging site. The owner will review the result first.

## Technical references for implementation

- [W3C WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/) — device user verification and biometric privacy; do not infer raw fingerprint/contact access from this API.
- [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) — support limits, recognition events and possible remote processing.
- [DFRobot SEN0539 documentation](https://wiki.dfrobot.com/sen0539-en) — candidate voice-module interface; confirm the actual purchased model.
- [TI SN65HVD230 datasheet](https://www.ti.com/lit/ds/symlink/sn65hvd230.pdf) — transceiver electrical/interface information.

## Unchanged executable baseline

The original reference engine follows so this handover remains self-contained. In the existing platform, use `static/js/yankson/engine.js`; do not create duplicate engines. If extracting the code, preserve UTF-8, LF newlines and its final newline, then verify the SHA-256 shown above.


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
