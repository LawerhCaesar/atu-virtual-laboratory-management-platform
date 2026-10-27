import test from "node:test";
import assert from "node:assert/strict";
import {GUIDES,guideFor} from "../../static/js/walkthrough/steps.mjs";

test("every current and retained guide includes useful checkpoints",()=>{
  for(const route of ["core:fuel_delivery","core:brakelab","core:wheel_slip","core:engine_live_data"]){
    const steps=guideFor(route,"Example");
    assert.equal(steps,GUIDES[route]);
    assert.ok(steps.length>=4);
    for(const step of steps){assert.ok(step.title && step.description && step.tip && step.check);}
  }
});

test("an unknown registered model gets a general guide without assumed results",()=>{
  const steps=guideFor("future:simulation","Future model");
  assert.ok(steps[0].title.includes("Future model"));
  assert.ok(steps.some(step=>step.check.includes("same settings")));
  assert.ok(steps.every(step=>step.title && step.description));
});
