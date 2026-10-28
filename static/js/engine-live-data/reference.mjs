const DT = 0.05;
const STATES = Object.freeze({ OFF: 0, PRIME: 1, CRANK: 2, RUN: 3, SHUTDOWN: 4 });
const STATE_NAMES = Object.freeze(["OFF", "PRIME", "CRANK", "RUN", "SHUTDOWN"]);
const INPUTS = Object.freeze({
  BatteryVoltage: { min: 8, max: 14.9, default: 13.8, unit: "V" },
  EngineSpeed: { min: 0, max: 6500, default: 800, unit: "rpm" },
  ThrottlePosition: { min: 0, max: 100, default: 2, unit: "%" },
  ManifoldPressure: { min: 20, max: 105, default: 35, unit: "kPa" },
  O2SensorVoltage: { min: 0.05, max: 0.95, default: 0.45, unit: "V" },
  ECT1Voltage: { min: 0.2, max: 4.8, default: 1, unit: "V" },
  ECT2Voltage: { min: 0.2, max: 4.8, default: 1.1, unit: "V" },
  AccessoryLoad: { min: 0, max: 100, default: 10, unit: "%" },
  IgnitionSwitch: { min: 0, max: 1, default: 0, unit: "0/1" },
  StartAuthorisation: { min: 0, max: 1, default: 0, unit: "0/1" },
  StartRequest: { min: 0, max: 1, default: 0, unit: "0/1" },
  StopRequest: { min: 0, max: 1, default: 0, unit: "0/1" },
  EmergencyStop: { min: 0, max: 1, default: 0, unit: "0/1" },
  ACRequest: { min: 0, max: 1, default: 0, unit: "0/1" }
});
const DEFAULT_INPUTS = Object.freeze({
  BatteryVoltage: INPUTS.BatteryVoltage.default,
  EngineSpeed: INPUTS.EngineSpeed.default,
  ThrottlePosition: INPUTS.ThrottlePosition.default,
  ManifoldPressure: INPUTS.ManifoldPressure.default,
  O2SensorVoltage: INPUTS.O2SensorVoltage.default,
  ECT1Voltage: INPUTS.ECT1Voltage.default,
  ECT2Voltage: INPUTS.ECT2Voltage.default,
  AccessoryLoad: INPUTS.AccessoryLoad.default,
  IgnitionSwitch: INPUTS.IgnitionSwitch.default,
  StartAuthorisation: INPUTS.StartAuthorisation.default,
  StartRequest: INPUTS.StartRequest.default,
  StopRequest: INPUTS.StopRequest.default,
  EmergencyStop: INPUTS.EmergencyStop.default,
  ACRequest: INPUTS.ACRequest.default
});
const clip = (x, low, high) => Math.min(Math.max(x, low), high);
function acceptInputs(raw = DEFAULT_INPUTS) {
  const inputs = {}, clampedFields = {};
  for (const key of Object.keys(INPUTS)) {
    const def = INPUTS[key];
    let value = raw[key] === void 0 ? def.default : raw[key];
    if (def.unit === "0/1" && typeof value === "boolean") value = Number(value);
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new TypeError(`${key} must be one finite number.`);
    }
    inputs[key] = clip(value, def.min, def.max);
    clampedFields[key] = inputs[key] !== value;
  }
  return { inputs, clampedFields };
}
function ectTemperature(voltage) {
  const v = clip(voltage, 0.2, 4.8);
  let t;
  if (v >= 4.3) t = -20 + (4.8 - v) * 40;
  else if (v >= 3.5) t = (4.3 - v) * 31.25;
  else if (v >= 2.5) t = 25 + (3.5 - v) * 25;
  else if (v >= 1.5) t = 50 + (2.5 - v) * 25;
  else if (v >= 1) t = 75 + (1.5 - v) * 30;
  else if (v >= 0.6) t = 90 + (1 - v) * 37.5;
  else if (v >= 0.3) t = 105 + (0.6 - v) * (20 / 0.3);
  else t = 125 + (0.3 - v) * 100;
  return clip(t, -20, 135);
}
function initialState() {
  return { engineState: STATES.OFF, elapsedInState: 0, sampleIndex: -1 };
}
const safeStart = (u) => u.IgnitionSwitch > 0.5 && u.StartAuthorisation > 0.5 && u.StartRequest > 0.5 && u.EmergencyStop <= 0.5 && u.BatteryVoltage >= 9.5;
function advanceState(u, previous) {
  const state = previous.engineState;
  let next = state, elapsed = previous.elapsedInState + DT;
  const abort = u.EmergencyStop > 0.5 || u.StopRequest > 0.5 || u.IgnitionSwitch <= 0.5;
  switch (state) {
    case STATES.OFF:
      if (safeStart(u)) next = STATES.PRIME;
      break;
    case STATES.PRIME:
      if (abort) next = STATES.SHUTDOWN;
      else if (elapsed >= 2) next = STATES.CRANK;
      break;
    case STATES.CRANK:
      if (abort || u.BatteryVoltage < 8.5) next = STATES.SHUTDOWN;
      else if (u.EngineSpeed >= 500) next = STATES.RUN;
      else if (elapsed >= 5) next = STATES.SHUTDOWN;
      break;
    case STATES.RUN:
      if (abort) next = STATES.SHUTDOWN;
      break;
    case STATES.SHUTDOWN:
      if (elapsed >= 0.5) next = STATES.OFF;
      break;
    default:
      throw new RangeError("Unknown internal engine state");
  }
  if (next !== state) elapsed = 0;
  return { engineState: next, elapsedInState: elapsed, sampleIndex: previous.sampleIndex + 1 };
}
function calculateOutputs(u, s) {
  const state = s.engineState;
  const FuelPumpState = Number(state === 1 || state === 2 || state === 3);
  const StarterState = Number(state === 2);
  const InjectionEnable = Number(state === 2 || state === 3);
  const IgnitionEnable = InjectionEnable;
  const ECT1Temp = ectTemperature(u.ECT1Voltage);
  const ECT2Temp = ectTemperature(u.ECT2Voltage);
  const EngineLoad = clip(0.55 * ((u.ManifoldPressure - 20) / 85) * 100 + 0.45 * u.ThrottlePosition, 0, 100);
  const LambdaEstimate = clip(1 + (0.45 - u.O2SensorVoltage) * 0.35, 0.75, 1.25);
  const ClosedLoopActive = Number(InjectionEnable > 0.5 && ECT1Temp >= 70 && u.EngineSpeed >= 600);
  const STFT = ClosedLoopActive ? clip((LambdaEstimate - 1) * 120, -25, 25) : 0;
  const WarmupEnrichment = clip((70 - ECT1Temp) * 0.5, 0, 40);
  const BatteryCompensation = clip((13.8 - u.BatteryVoltage) * 0.18, 0, 1.2);
  const BaseInjectorPW = clip(1 + 35e-5 * u.EngineSpeed + 0.025 * (u.ManifoldPressure - 20) + 0.012 * u.ThrottlePosition, 1, 15);
  const InjectorPW = InjectionEnable ? clip((BaseInjectorPW + BatteryCompensation) * (1 + (STFT + WarmupEnrichment) / 100), 0, 20) : 0;
  const ActualRPM = u.EngineSpeed;
  const TargetIdleRPM = 750 + clip((80 - ECT1Temp) * 5.625, 0, 450);
  const IdleActive = Number(state === 3 && u.ThrottlePosition <= 5 && u.EngineSpeed < 2e3);
  const RPMError = IdleActive ? TargetIdleRPM - ActualRPM : 0;
  const IdleControlDuty = IdleActive ? clip(25 + 0.06 * RPMError + 0.25 * u.AccessoryLoad, 0, 100) : 0;
  const IgnitionTiming = !IgnitionEnable ? 0 : state === 2 ? 5 : clip(
    10 + 4e-3 * (u.EngineSpeed - 800) - 0.08 * (u.ManifoldPressure - 35) + 0.015 * RPMError,
    -5,
    45
  );
  const SensorDifference = Math.abs(ECT1Temp - ECT2Temp);
  const SensorDisagreement = Number(SensorDifference > 15);
  const ControlTemperature = Math.max(ECT1Temp, ECT2Temp);
  const T = ControlTemperature;
  let FanDuty = 0, WaterPumpDuty = 0;
  if (u.EmergencyStop > 0.5 || u.BatteryVoltage < 8) {
    FanDuty = 0;
    WaterPumpDuty = 0;
  } else if (SensorDisagreement) {
    FanDuty = 100;
    WaterPumpDuty = 100;
  } else {
    if (T < 88) FanDuty = 0;
    else if (T < 95) FanDuty = 20 + (T - 88) * (30 / 7);
    else if (T < 105) FanDuty = 50 + (T - 95) * 5;
    else FanDuty = 100;
    if (u.ACRequest > 0.5 && state >= 2) FanDuty = Math.max(FanDuty, 35);
    if (state === 3) {
      if (T < 50) WaterPumpDuty = 35;
      else if (T < 90) WaterPumpDuty = 35 + (T - 50) * (35 / 40);
      else if (T < 110) WaterPumpDuty = 70 + (T - 90) * 1.5;
      else WaterPumpDuty = 100;
    } else if (T > 95) WaterPumpDuty = 60;
  }
  FanDuty = clip(FanDuty, 0, 100);
  WaterPumpDuty = clip(WaterPumpDuty, 0, 100);
  return {
    EngineState: state,
    EngineStateLabel: STATE_NAMES[state],
    StateElapsedTime: s.elapsedInState,
    FuelPumpState,
    StarterState,
    InjectionEnable,
    IgnitionEnable,
    StartPermitted: FuelPumpState,
    SafeStartCondition: Number(safeStart(u)),
    InjectorPW,
    STFT,
    LambdaEstimate,
    ClosedLoopActive,
    EngineLoad,
    BaseInjectorPW,
    WarmupEnrichment,
    BatteryCompensation,
    ActualRPM,
    TargetIdleRPM,
    RPMError,
    IdleControlDuty,
    IgnitionTiming,
    IdleActive,
    ECT1Temp,
    ECT2Temp,
    FanDuty,
    WaterPumpDuty,
    SensorDifference,
    ControlTemperature,
    SensorDisagreement,
    CoolingLoopActive: Number(FanDuty > 0 || WaterPumpDuty > 0)
  };
}
function stepEngineModel(rawInputs, previous = initialState()) {
  const { inputs, clampedFields } = acceptInputs(rawInputs);
  const internalState = advanceState(inputs, previous);
  return {
    inputs,
    clampedFields,
    internalState,
    simulationTime: internalState.sampleIndex * DT,
    outputs: calculateOutputs(inputs, internalState)
  };
}
function previewEngineModel(rawInputs = DEFAULT_INPUTS, internalState = initialState()) {
  const { inputs, clampedFields } = acceptInputs(rawInputs);
  return {
    inputs,
    clampedFields,
    internalState,
    simulationTime: Math.max(0, internalState.sampleIndex) * DT,
    outputs: calculateOutputs(inputs, internalState)
  };
}
export {
  DEFAULT_INPUTS,
  DT,
  INPUTS,
  STATES,
  STATE_NAMES,
  acceptInputs,
  advanceState,
  calculateOutputs,
  clip,
  ectTemperature,
  initialState,
  previewEngineModel,
  stepEngineModel
};
