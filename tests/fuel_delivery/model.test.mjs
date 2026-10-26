import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {DEFAULTS, PRESETS, evaluate, initialState, stepFuelDeliveryModel, validate} from "../../static/js/fuel-delivery/model.mjs";
import {FuelSimulation} from "../../static/js/fuel-delivery/controller.mjs";

const near = (actual, expected, tolerance = 1e-9) => assert.ok(Math.abs(actual-expected) <= tolerance, `${actual} != ${expected}`);
const complete = (inputs = DEFAULTS) => { const s = new FuelSimulation(inputs); s.start(); while(s.running) s.tick(); return s; };

test("all supplied rounded default results and exact integration order after 30 seconds", () => {
  const sim = complete(), o = sim.result.outputs;
  const expected = {baseFuelMgPerEvent:20.408, finalFuelMgPerEvent:20.408, injectorPulseWidthMs:8.471,
    injectorDutyCyclePct:17.648, predictedLambda:1, stftPct:0, ltftPct:0, fuelFlowGps:1.701,
    fuelFlowLph:8.218, cumulativeFuelG:51.020, brakePowerKw:20.944, bsfcGPerKWh:292.325,
    fuelSavingPct:0, recommendedFuelScale:1};
  for (const [key,value] of Object.entries(expected)) near(o[key], value, .000501);
  assert.equal(sim.history.length, 300); near(sim.state.simulationTimeS, 30);
  assert.deepEqual(sim.result.integrationVector, [o.finalFuelMgPerEvent,o.injectorPulseWidthMs,o.injectorDutyCyclePct,o.predictedLambda,o.fuelFlowGps,o.cumulativeFuelG,o.bsfcGPerKWh,o.fuelSavingPct]);
});

test("lean, rich, open-loop, cold, acceleration and rail pressure directions", () => {
  near(evaluate({...DEFAULTS,measuredLambda:1.05}).outputs.stftPct,6);
  near(evaluate({...DEFAULTS,measuredLambda:.95}).outputs.stftPct,-6);
  const lean = complete({...DEFAULTS,measuredLambda:1.05}); near(lean.state.ltftPct,.54);
  const rich = complete({...DEFAULTS,measuredLambda:.95}); near(rich.state.ltftPct,-.54);
  const open = stepFuelDeliveryModel({...DEFAULTS,closedLoopEnabled:false,measuredLambda:1.1},lean.state,.1);
  near(open.outputs.stftPct,0); near(open.state.ltftPct,lean.state.ltftPct);
  near(evaluate({...DEFAULTS,coolantTempC:20}).outputs.warmupFactor,1.25);
  near(evaluate({...DEFAULTS,engineLoadPct:100}).outputs.loadFactor,1.06);
  near(evaluate({...DEFAULTS,accelerationEnrichmentPct:10}).outputs.finalFuelMgPerEvent,evaluate(DEFAULTS).outputs.finalFuelMgPerEvent*1.1);
  assert.ok(evaluate({...DEFAULTS,fuelRailPressureKPa:400}).outputs.injectorPulseWidthMs < evaluate(DEFAULTS).outputs.injectorPulseWidthMs);
  const scaled = evaluate({...DEFAULTS,fuelOptimisationScale:.98}).outputs;
  near(scaled.fuelSavingPct,2); near(scaled.predictedLambda,1/.98);
});

test("SLX integrator precedes LTFT output saturation and retains wind-up", () => {
  const input = {...DEFAULTS,ltftLearningGainPerS:.01,targetLambda:.85,measuredLambda:1.2,simulationDurationS:120};
  const sim = complete(input); near(sim.state.ltftIntegralPct,30); near(sim.state.ltftPct,20);
  const next = stepFuelDeliveryModel({...input,targetLambda:1.1,measuredLambda:.8},sim.state,1);
  near(next.state.ltftIntegralPct,29.75); near(next.outputs.ltftPct,20);
});

test("reject invalid denominators, NaN and unbounded simulation requests", () => {
  for (const key of Object.keys(DEFAULTS).filter(k => k !== "closedLoopEnabled")) assert.equal(validate({...DEFAULTS,[key]:NaN}).valid,false);
  for (const key of ["engineSpeedRpm","targetLambda","airFlowGps","fuelRailPressureKPa","injectorRatedFlowCcMin","simulationDurationS","timeStepS"]) assert.throws(() => evaluate({...DEFAULTS,[key]:0}));
  for (const changes of [{timeStepS:.001},{simulationDurationS:1e6},{fuelOptimisationScale:.5},{injectorFlowBiasPct:-100},{brakeTorqueNm:-1},{closedLoopEnabled:1}]) assert.equal(validate({...DEFAULTS,...changes}).valid,false);
  assert.throws(() => stepFuelDeliveryModel(DEFAULTS,initialState(),0));
  assert.throws(() => evaluate(DEFAULTS,{...initialState(),ltftIntegralPct:Infinity}));
});

test("warnings are not silently corrected; saturation and near-zero BSFC stay explicit", () => {
  const saturation = evaluate({...DEFAULTS,airFlowGps:200,injectorRatedFlowCcMin:150});
  assert.equal(saturation.outputs.injectorDutyCyclePct,100);
  assert.ok(saturation.status.warnings.some(w => w.includes("saturation")));
  assert.equal(saturation.status.optimisationAcceptable,false);
  const nearZero = evaluate({...DEFAULTS,brakeTorqueNm:0});
  assert.ok(Number.isFinite(nearZero.outputs.bsfcGPerKWh));
  assert.ok(nearZero.status.warnings.some(w => w.includes("not meaningful")));
  const savings = evaluate({...DEFAULTS,fuelOptimisationScale:.85});
  assert.ok(savings.status.warnings.some(w => w.includes("Apparent fuel saving")));
  assert.ok(evaluate({...DEFAULTS,measuredLambda:1.05}).outputs.fuelSavingPct < 0);
});

test("runner handles partial final step, reset, pause, comparison and user isolation", () => {
  const run = complete({...DEFAULTS,simulationDurationS:5,timeStepS:.3}); near(run.state.simulationTimeS,5);
  near(run.result.outputs.cumulativeFuelG, evaluate(DEFAULTS).outputs.fuelFlowGps*5);
  const untouched = new FuelSimulation();
  run.edit({...run.inputs,measuredLambda:1.05}); const time=run.state.simulationTimeS;
  run.tick(); near(run.state.simulationTimeS,time);
  const savedState={...run.state}; const savedRows=run.history.length;
  run.compare(); assert.deepEqual(run.state,savedState); assert.equal(run.history.length,savedRows);
  assert.equal(untouched.state.simulationTimeS,0);
  run.reset(); assert.deepEqual(run.inputs,DEFAULTS); assert.equal(run.history.length,0);
  run.start(); run.tick(); const snapshot=run.history[0].inputs.measuredLambda;
  run.edit({...run.inputs,measuredLambda:1.1}); assert.equal(run.history[0].inputs.measuredLambda,snapshot);
  assert.ok(run.csv().includes("input_measuredLambda"));
  assert.equal(run.payload().moduleId,"fuel-delivery-optimisation");
});

test("scale-only fresh baseline comparison preserves trims and does not claim optimality", () => {
  const sim = new FuelSimulation({...DEFAULTS,fuelOptimisationScale:.98,measuredLambda:1.05});
  const {baseline,adjusted}=sim.compare(); near(adjusted.outputs.cumulativeFuelG/baseline.outputs.cumulativeFuelG,.98);
  near(baseline.outputs.ltftPct,adjusted.outputs.ltftPct);
  assert.equal(baseline.inputs.fuelOptimisationScale,1);
  near(sim.state.simulationTimeS,0);
});

// Independent reference evaluates the inspected SLX block graph, not copies of
// application formulas. Only the fixed, audited expression grammar is allowed.
const contract=JSON.parse(readFileSync(new URL("./source-contract.json",import.meta.url)));
const inputOrder=["engineSpeedRpm","engineLoadPct","airFlowGps","targetLambda","measuredLambda","coolantTempC","fuelRailPressureKPa","batteryVoltageV","injectorRatedFlowCcMin","injectorFlowBiasPct","accelerationEnrichmentPct","brakeTorqueNm","closedLoopEnabled","fuelOptimisationScale","ltftLearningGainPerS"];
function sourceGraph(input,state) {
  const lookup=new Map();
  function system(name,inValues=[]) {
    const s=contract.systems[name], map=new Map(s.blocks.map(b=>[b.sid,b])), wires=new Map();
    for(const wire of s.wires) for(const dst of wire.to) wires.set(dst,wire.from);
    const memo=new Map();
    const port=(sid,n=1)=>{
      const src=wires.get(`${sid}#in:${n}`); if(!src) throw Error(`Missing source ${name}:${sid}:${n}`);
      const [block,num]=src.split("#out:"); return get(block,Number(num));
    };
    function get(sid,portNumber=1) {
      const cacheKey=`${sid}:${portNumber}`; if(memo.has(cacheKey))return memo.get(cacheKey);
      const b=map.get(sid), p=b.parameters; let value;
      switch(b.type) {
        case "Constant": value=name==="system_root" ? Number(input[inputOrder[Number(sid)-1]]) : Number(p.Value); break;
        case "Inport": value=inValues[Number(p.Port||1)-1]; break;
        case "Outport": value=port(sid); break;
        case "Integrator": value=state[`${name}:${sid}`]||0; lookup.set(`${name}:${sid}`,()=>port(sid)); break;
        case "Gain": value=port(sid)*Number(p.Gain); break;
        case "Saturate": value=Math.min(Number(p.UpperLimit),Math.max(Number(p.LowerLimit),port(sid))); break;
        case "Mux": value=Array.from({length:Number(p.Inputs)},(_,j)=>port(sid,j+1)); break;
        case "Product": value=Array.from({length:Number(p.Inputs)},(_,j)=>port(sid,j+1)).reduce((a,b)=>a*b,1); break;
        case "Sum": value=[...p.Inputs].reduce((sum,sign,j)=>sum+(sign==="-"?-1:1)*port(sid,j+1),0); break;
        case "Fcn": {
          assert.doesNotMatch(p.Expr.replace(/u\(\d+\)|sqrt|pi/g,""),/[^0-9().+*/\s\-]/);
          const expression=p.Expr.replace(/u\((\d+)\)/g,(_,n)=>`v[${Number(n)-1}]`).replace(/sqrt/g,"Math.sqrt").replace(/\bpi\b/g,"Math.PI");
          const v=port(sid); value=Function("v",`return (${expression});`)(Array.isArray(v)?v:[v]); break;
        }
        case "SubSystem": {
          const childName=`system_${sid}`, child=contract.systems[childName];
          const count=child.blocks.filter(b=>b.type==="Inport").length;
          const out=system(childName,Array.from({length:count},(_,j)=>port(sid,j+1)));
          value=out[portNumber-1]; break;
        }
        default: throw Error(`Unsupported block ${b.type}`);
      }
      memo.set(cacheKey,value); return value;
    }
    return s.blocks.filter(b=>b.type==="Outport").sort((a,b)=>Number(a.parameters.Port||1)-Number(b.parameters.Port||1)).map(b=>get(b.sid));
  }
  const vector=system("system_root")[0];
  return {vector,derivative:key=>lookup.get(key)()};
}

test("computed vector agrees with the actual SLX expression and wiring graph across all presets", () => {
  for(const [,values] of PRESETS) {
    const input={...DEFAULTS,...values}, raw={"system_201:516":0,"system_203:715":0}; let current=initialState();
    for(let step=0;step<30;step++) {
      const before=sourceGraph(input,raw); raw["system_201:516"]+=before.derivative("system_201:516")*.1;
      const afterTrim=sourceGraph(input,raw); raw["system_203:715"]+=afterTrim.derivative("system_203:715")*.1;
      const reference=sourceGraph(input,raw).vector;
      const actual=stepFuelDeliveryModel(input,current,.1); current=actual.state;
      actual.integrationVector.forEach((value,j)=>near(value,reference[j],1e-8));
    }
  }
});
