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
