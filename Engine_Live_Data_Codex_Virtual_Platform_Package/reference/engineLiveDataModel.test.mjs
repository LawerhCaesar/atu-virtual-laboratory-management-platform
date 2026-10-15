import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_INPUTS,
  ENGINE_STATES,
  calculateCooling,
  calculateFuel,
  calculateIdleIgnition,
  createInitialInternalState,
  ectVoltageToTemperature,
  sanitizeInputs,
  stepEngineModel,
} from "./engineLiveDataModel.mjs";

const closeTo = (actual, expected, tolerance = 1e-9) => {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `Expected ${actual} to be within ${tolerance} of ${expected}`,
  );
};

test("input values are capped", () => {
  const { accepted, clampedFields } = sanitizeInputs({
    ...DEFAULT_INPUTS,
    BatteryVoltage: 16,
    EngineSpeed: -100,
    ThrottlePosition: 120,
    ManifoldPressure: 10,
  });

  assert.equal(accepted.BatteryVoltage, 14.9);
  assert.equal(accepted.EngineSpeed, 0);
  assert.equal(accepted.ThrottlePosition, 100);
  assert.equal(accepted.ManifoldPressure, 20);
  assert.equal(clampedFields.BatteryVoltage, true);
});

test("ECT conversion matches reference checkpoints", () => {
  const cases = [
    [4.8, -20],
    [4.3, 0],
    [3.5, 25],
    [2.5, 50],
    [1.5, 75],
    [1.0, 90],
    [0.6, 105],
    [0.3, 125],
    [0.2, 135],
  ];

  for (const [voltage, expected] of cases) {
    closeTo(ectVoltageToTemperature(voltage), expected, 1e-9);
  }
});

test("warm stoichiometric fuel condition", () => {
  const inputs = {
    ...DEFAULT_INPUTS,
    EngineSpeed: 800,
    ManifoldPressure: 35,
    ThrottlePosition: 2,
    O2SensorVoltage: 0.45,
    BatteryVoltage: 13.8,
  };
  const startRun = { InjectionEnable: 1 };
  const fuel = calculateFuel(inputs, 90, startRun);

  closeTo(fuel.EngineLoad, 10.605882352941178);
  closeTo(fuel.LambdaEstimate, 1);
  closeTo(fuel.STFT, 0);
  closeTo(fuel.BaseInjectorPW, 1.679);
  closeTo(fuel.InjectorPW, 1.679);
  assert.equal(fuel.ClosedLoopActive, 1);
});

test("lean O2 indication produces positive correction", () => {
  const inputs = {
    ...DEFAULT_INPUTS,
    EngineSpeed: 800,
    ManifoldPressure: 35,
    ThrottlePosition: 2,
    O2SensorVoltage: 0.1,
    BatteryVoltage: 13.8,
  };
  const fuel = calculateFuel(inputs, 90, { InjectionEnable: 1 });

  closeTo(fuel.LambdaEstimate, 1.1225);
  closeTo(fuel.STFT, 14.7, 1e-12);
  closeTo(fuel.InjectorPW, 1.925813, 1e-12);
});

test("rich O2 indication produces negative correction", () => {
  const inputs = {
    ...DEFAULT_INPUTS,
    EngineSpeed: 800,
    ManifoldPressure: 35,
    ThrottlePosition: 2,
    O2SensorVoltage: 0.9,
    BatteryVoltage: 13.8,
  };
  const fuel = calculateFuel(inputs, 90, { InjectionEnable: 1 });

  closeTo(fuel.LambdaEstimate, 0.8425);
  closeTo(fuel.STFT, -18.9, 1e-12);
  closeTo(fuel.InjectorPW, 1.361669, 1e-12);
});

test("idle and ignition calculations match reference", () => {
  const inputs = {
    ...DEFAULT_INPUTS,
    EngineSpeed: 620,
    ThrottlePosition: 2,
    ManifoldPressure: 45,
    AccessoryLoad: 80,
  };
  const outputs = calculateIdleIgnition(inputs, 90, {
    EngineState: ENGINE_STATES.RUN,
    IgnitionEnable: 1,
  });

  closeTo(outputs.TargetIdleRPM, 750);
  closeTo(outputs.RPMError, 130);
  closeTo(outputs.IdleControlDuty, 52.8);
  closeTo(outputs.IgnitionTiming, 10.43);
  assert.equal(outputs.IdleActive, 1);
});

test("normal warm cooling calculation", () => {
  const inputs = {
    ...DEFAULT_INPUTS,
    ECT1Voltage: 1.0,
    ECT2Voltage: 1.1,
    BatteryVoltage: 13.8,
    ACRequest: 0,
    EmergencyStop: 0,
  };
  const cooling = calculateCooling(inputs, { EngineState: ENGINE_STATES.RUN });

  closeTo(cooling.ECT1Temp, 90);
  closeTo(cooling.ECT2Temp, 87);
  closeTo(cooling.SensorDifference, 3);
  closeTo(cooling.FanDuty, 28.57142857142857);
  closeTo(cooling.WaterPumpDuty, 70);
  assert.equal(cooling.SensorDisagreement, 0);
});

test("ECT disagreement invokes full-duty fail-safe", () => {
  const inputs = {
    ...DEFAULT_INPUTS,
    ECT1Voltage: 1.0,
    ECT2Voltage: 2.0,
    BatteryVoltage: 13.8,
    EmergencyStop: 0,
  };
  const cooling = calculateCooling(inputs, { EngineState: ENGINE_STATES.RUN });

  closeTo(cooling.ECT1Temp, 90);
  closeTo(cooling.ECT2Temp, 62.5);
  closeTo(cooling.SensorDifference, 27.5);
  assert.equal(cooling.SensorDisagreement, 1);
  assert.equal(cooling.FanDuty, 100);
  assert.equal(cooling.WaterPumpDuty, 100);
});

test("low battery blocks safe start", () => {
  const inputs = {
    ...DEFAULT_INPUTS,
    IgnitionSwitch: 1,
    StartAuthorisation: 1,
    StartRequest: 1,
    BatteryVoltage: 9.0,
  };
  const result = stepEngineModel(inputs, createInitialInternalState(), 0.05);
  assert.equal(result.outputs.EngineState, ENGINE_STATES.OFF);
  assert.equal(result.outputs.StartPermitted, 0);
});

test("normal start advances through prime, crank and run", () => {
  const inputs = {
    ...DEFAULT_INPUTS,
    IgnitionSwitch: 1,
    StartAuthorisation: 1,
    StartRequest: 1,
    BatteryVoltage: 13.8,
    EngineSpeed: 800,
  };

  let internal = createInitialInternalState();
  let result = stepEngineModel(inputs, internal, 0.05);
  internal = result.internalState;
  assert.equal(result.outputs.EngineState, ENGINE_STATES.PRIME);

  for (let index = 0; index < 40; index += 1) {
    result = stepEngineModel(inputs, internal, 0.05);
    internal = result.internalState;
  }
  assert.equal(result.outputs.EngineState, ENGINE_STATES.CRANK);
  assert.equal(result.outputs.StarterState, 1);

  result = stepEngineModel(inputs, internal, 0.05);
  assert.equal(result.outputs.EngineState, ENGINE_STATES.RUN);
  assert.equal(result.outputs.StarterState, 0);
  assert.equal(result.outputs.FuelPumpState, 1);
  assert.equal(result.outputs.InjectionEnable, 1);
  assert.equal(result.outputs.IgnitionEnable, 1);
});

test("emergency stop from RUN moves to shutdown", () => {
  const internal = {
    engineState: ENGINE_STATES.RUN,
    elapsedInState: 1,
    simulationTime: 3,
  };
  const inputs = {
    ...DEFAULT_INPUTS,
    IgnitionSwitch: 1,
    StartAuthorisation: 1,
    EmergencyStop: 1,
  };
  const result = stepEngineModel(inputs, internal, 0.05);

  assert.equal(result.outputs.EngineState, ENGINE_STATES.SHUTDOWN);
  assert.equal(result.outputs.FuelPumpState, 0);
  assert.equal(result.outputs.StarterState, 0);
  assert.equal(result.outputs.InjectionEnable, 0);
  assert.equal(result.outputs.IgnitionEnable, 0);
  assert.equal(result.outputs.FanDuty, 0);
  assert.equal(result.outputs.WaterPumpDuty, 0);
});
