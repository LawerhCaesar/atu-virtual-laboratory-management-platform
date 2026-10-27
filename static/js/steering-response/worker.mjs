import {simulateSteeringResponse} from './model.mjs';
self.onmessage=event=>{try{self.postMessage({ok:true,result:simulateSteeringResponse(event.data.vehicle,event.data.scenario)});}catch(error){self.postMessage({ok:false,error:error.message});}};
