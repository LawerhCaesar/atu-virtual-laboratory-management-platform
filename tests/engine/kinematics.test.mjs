import test from "node:test";
import assert from "node:assert/strict";
import { CutawayClock, GEOMETRY, FIRING_ORDER, pistonPosition, cylinderPose } from "../../static/js/engine-live-data/kinematics.mjs";
import { EngineSimulation } from "../../static/js/engine-live-data/controller.mjs";

test("generic slider-crank geometry preserves rod length and exact dead centres", () => {
  const { crankRadius: r, rodLength: l } = GEOMETRY;
  assert.equal(pistonPosition(0), l + r);
  assert.equal(pistonPosition(180), l - r);
  for (let angle = 0; angle <= 720; angle++) {
    const p = cylinderPose(1, angle);
    assert.ok(p.piston >= l - r - 1e-10 && p.piston <= l + r + 1e-10);
    assert.ok(Math.abs(Math.hypot(p.piston - p.pinY, p.pinZ) - l) < 1e-10);
  }
  assert.throws(() => pistonPosition(0, 1, .5), RangeError);
});

test("assumed firing order, idealised strokes and commanded spark advance are explicit", () => {
  for (const [index, cylinder] of FIRING_ORDER.entries()) assert.equal(cylinderPose(cylinder, index * 180).cycle, 0);
  assert.equal(cylinderPose(1, 90).stroke, "Power");
  assert.equal(cylinderPose(1, 270).exhaust, true);
  assert.equal(cylinderPose(1, 450).intake, true);
  assert.equal(cylinderPose(1, 630).stroke, "Compression");
  assert.equal(cylinderPose(1, 700, { IgnitionEnable: 1, IgnitionTiming: 20 }).spark, true);
  assert.equal(cylinderPose(1, 700, { IgnitionEnable: 0, IgnitionTiming: 20 }).spark, false);
  assert.equal(cylinderPose(1, 10, { IgnitionEnable: 1, IgnitionTiming: -10 }).spark, true);
  assert.throws(() => cylinderPose(5, 0), RangeError);
});

test("presentation clock gates motion, scales RPM and never mutates solver snapshots", () => {
  const clock = new CutawayClock();
  const result = { inputs: { EngineSpeed: 1000, EmergencyStop: 0 }, outputs: { EngineState: 0 } };
  clock.advance(result, .05); assert.equal(clock.angle, 0);
  result.outputs.EngineState = 1; clock.advance(result, .05); assert.equal(clock.angle, 0);
  result.outputs.EngineState = 2;
  const before = structuredClone(result);
  clock.advance(result, .05); assert.equal(clock.angle, 6);
  assert.deepEqual(result, before);
  clock.scale = .1; clock.advance(result, .05); assert.equal(clock.angle, 36);
  result.inputs.EmergencyStop = 1; clock.advance(result, 1); assert.equal(clock.angle, 36);
  clock.reset(); assert.equal(clock.angle, 0);
});

test("adding a cutaway observer cannot alter calculations, history or CSV", () => {
  const a = new EngineSimulation(), b = new EngineSimulation(), clock = new CutawayClock();
  for (const s of [a, b]) {
    s.setInput("IgnitionSwitch", 1); s.setInput("StartAuthorisation", 1);
    s.pulse("StartRequest"); s.running = true;
  }
  for (let tick = 0; tick < 100; tick++) { a.step(); b.step(); clock.advance(b.result, .05); }
  assert.deepEqual(a.result, b.result);
  assert.equal(a.csv(), b.csv());
  assert.ok(clock.angle > 0);
});
