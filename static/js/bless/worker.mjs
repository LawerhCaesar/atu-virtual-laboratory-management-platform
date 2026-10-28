import {createSimulation,stepSimulation} from './engine.mjs';
let active=null;
self.onmessage=async({data})=>{
 if(data.type==='CANCEL'){if(active?.runId===data.runId)active.cancelled=true;return;}
 if(data.type!=='RUN'&&data.type!=='INITIALIZE')return;
 if(active)active.cancelled=true;
 const job={runId:data.runId,id:data.id,cancelled:false};active=job;
 try{let state=createSimulation(data.scenario);const samples=[];
  while(state.time_s<=state.scenario.duration_s){
   if(job.cancelled)return;
   for(let i=0;i<100&&state.time_s<=state.scenario.duration_s;i++){const r=stepSimulation(state);samples.push(r.sample);state=r.nextState;}
   self.postMessage({type:'PROGRESS',id:job.id,runId:job.runId,progress:samples.length/(state.scenario.duration_s+1)});
   await new Promise(resolve=>setTimeout(resolve,0));
  }
  if(!job.cancelled)self.postMessage({type:'COMPLETE',id:job.id,runId:job.runId,result:{schemaVersion:1,runId:job.runId,scenario:state.scenario,samples}});
 }catch(error){if(!job.cancelled)self.postMessage({type:'ERROR',id:job.id,runId:job.runId,message:error.message});}
};
