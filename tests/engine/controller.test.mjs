import test from "node:test";
import assert from "node:assert/strict";
import { EngineSimulation } from "../../static/js/engine-live-data/controller.mjs";
import { DEFAULT_INPUTS, ENGINE_STATES, calculateCooling, calculateFuel, sanitizeInputs, stepEngineModel } from "../../static/js/engine-live-data/model.mjs";
import { SPEC } from "../../static/js/engine-live-data/spec.mjs";

test("every canonical signal definition agrees with the engineering specification", () => {
  for (const definition of SPEC.inputs) {
    const result = sanitizeInputs({ [definition.name]: definition.max + 10 });
    assert.equal(result.accepted[definition.name], definition.max);
    assert.equal(sanitizeInputs({ [definition.name]: definition.min - 10 }).accepted[definition.name], definition.min);
    assert.equal(DEFAULT_INPUTS[definition.name], definition.default);
  }
});

test("OFF and pause preserve state; preset never bypasses normal start; reset restores safe defaults", () => {
  const sim = new EngineSimulation();
  sim.loadPreset(2);
  assert.equal(sim.internal.engineState, ENGINE_STATES.OFF);
  assert.equal(sim.rawInputs.IgnitionSwitch, 0);
  assert.equal(sim.rawInputs.StartAuthorisation, 0);
  sim.step();
  assert.equal(sim.internal.simulationTime, 0);
  sim.running = true;
  sim.step();
  sim.running = false;
  const frozen = structuredClone({ state: sim.internal, history: sim.history });
  sim.step();
  assert.deepEqual({ state: sim.internal, history: sim.history }, frozen);
  sim.reset();
  assert.deepEqual(sim.rawInputs, DEFAULT_INPUTS);
  assert.equal(sim.history.length, 0);
  assert.equal(sim.internal.engineState, 0);
});

test("crank timeout and shutdown obey their independent timers", () => {
  const sim = new EngineSimulation();
  sim.setInput("IgnitionSwitch", 1); sim.setInput("StartAuthorisation", 1);
  sim.setInput("EngineSpeed", 0); sim.pulse("StartRequest"); sim.running = true;
  sim.step();
  assert.equal(sim.internal.engineState, 1);
  for (let i = 0; i < 40; i++) sim.step();
  assert.equal(sim.internal.engineState, 2);
  for (let i = 0; i < 99; i++) sim.step();
  assert.equal(sim.internal.engineState, 2);
  // The supplied floating-point reference can cross exactly 5 s one tick late.
  sim.step(); if (sim.internal.engineState === 2) sim.step();
  assert.equal(sim.internal.engineState, 4);
  for (let i = 0; i < 9; i++) sim.step();
  assert.equal(sim.internal.engineState, 4);
  sim.step(); if (sim.internal.engineState === 4) sim.step();
  assert.equal(sim.internal.engineState, 0);
});

test("emergency stop is immediate while paused and cannot be cleared by a preset or input edit", () => {
  const sim = new EngineSimulation();
  sim.internal = { engineState: 3, elapsedInState: 1, simulationTime: 4 };
  sim.emergencyStop();
  assert.equal(sim.internal.engineState, 4);
  assert.equal(sim.internal.simulationTime, 4);
  sim.setInput("EmergencyStop", 0);
  sim.loadPreset(4);
  assert.equal(sim.result.inputs.EmergencyStop, 1);
  for (const key of ["FuelPumpState", "StarterState", "InjectionEnable", "IgnitionEnable", "FanDuty", "WaterPumpDuty"]) assert.equal(sim.result.outputs[key], 0);
  sim.reset();
  assert.equal(sim.result.inputs.EmergencyStop, 0);
});

test("momentary requests clear after ten fixed 0.05-second steps", () => {
  const sim = new EngineSimulation();
  sim.pulse("StartRequest"); sim.running = true;
  for (let i = 0; i < 9; i++) sim.step();
  assert.equal(sim.rawInputs.StartRequest, 1);
  sim.step();
  assert.equal(sim.rawInputs.StartRequest, 0);
  assert.ok(Math.abs(sim.internal.simulationTime - 0.5) < 1e-8);
});

test("history retains sixty virtual seconds; CSV contains every accepted input and canonical output", () => {
  const sim = new EngineSimulation();
  sim.setInput("BatteryVoltage", 16); sim.running = true;
  for (let i = 0; i < 1400; i++) sim.step();
  assert.ok(sim.history.length >= 1200 && sim.history.length <= 1201);
  assert.ok(Math.abs(sim.history.at(-1).SimulationTime - sim.history[0].SimulationTime - 60) < 0.051);
  const [header, ...rows] = sim.csv().split("\r\n");
  const columns = header.split(",");
  for (const signal of [...SPEC.inputs, ...SPEC.outputs]) assert.ok(columns.includes(signal.name));
  assert.equal(Number(rows.at(-1).split(",")[columns.indexOf("BatteryVoltage")]), 14.9);
  assert.ok(rows.every(row => row.split(",").length === columns.length));
});

test("closed loop disables below either the coolant or RPM threshold", () => {
  for (const [rpm, temperature] of [[800, 69.9], [599, 90]]) {
    const fuel = calculateFuel({ ...DEFAULT_INPUTS, EngineSpeed: rpm }, temperature, { InjectionEnable: 1 });
    assert.equal(fuel.ClosedLoopActive, 0);
    assert.equal(fuel.STFT, 0);
  }
});

test("high cooling demand with AC matches the package acceptance values", () => {
  const result = calculateCooling({ ...DEFAULT_INPUTS, ECT1Voltage: 0.55, ECT2Voltage: 0.62, ACRequest: 1 }, { EngineState: 3 });
  for (const [key, expected] of Object.entries({ ECT1Temp: 108.3333333333, ECT2Temp: 104.25, SensorDisagreement: 0, FanDuty: 100, WaterPumpDuty: 97.5 })) {
    assert.ok(Math.abs(result[key] - expected) < 1e-6, key);
  }
});

test("stop and ignition-off outrank starting; low cranking voltage outranks RPM", () => {
  for (const changes of [{ StopRequest: 1 }, { IgnitionSwitch: 0 }, { BatteryVoltage: 8.4 }]) {
    const result = stepEngineModel({ ...DEFAULT_INPUTS, IgnitionSwitch: 1, EngineSpeed: 800, ...changes }, { engineState: 2, elapsedInState: 0, simulationTime: 2 }, 0.05);
    assert.equal(result.outputs.EngineState, 4);
  }
});
