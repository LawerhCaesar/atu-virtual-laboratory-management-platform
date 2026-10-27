import {simulate} from "./model.mjs";
self.onmessage = event => {
  try { self.postMessage({ok:true,result:simulate(event.data)}); }
  catch (error) { self.postMessage({ok:false,error:error.message}); }
};
