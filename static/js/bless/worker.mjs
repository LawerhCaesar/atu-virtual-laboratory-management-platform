import {createStudy,advanceStudy,finishStudy} from './study.mjs';
let active=null;
self.onmessage=async({data})=>{
 if(data.type==='CANCEL'){if(active?.runId===data.runId)active.cancelled=true;return;}
 if(!['RUN','INITIALIZE'].includes(data.type))return;
 if(active)active.cancelled=true;const job={runId:data.runId,id:data.id,cancelled:false};active=job;
 try{const task=createStudy(data.scenario,data.study||{mode:'duration',compareBatteryOnly:false},job.runId);
  while(!task.done){if(job.cancelled)return;for(let i=0;i<100&&!task.done;i++)advanceStudy(task);self.postMessage({type:'PROGRESS',id:job.id,runId:job.runId,progress:task.state.time_s/(task.requested.duration_s+1)});await new Promise(resolve=>setTimeout(resolve,0));}
  if(!job.cancelled)self.postMessage({type:'COMPLETE',id:job.id,runId:job.runId,result:finishStudy(task)});
 }catch(error){if(!job.cancelled)self.postMessage({type:'ERROR',id:job.id,runId:job.runId,message:error.message});}
};
