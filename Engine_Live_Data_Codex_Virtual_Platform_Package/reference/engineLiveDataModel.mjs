/**
 * Dependency-free reference engine for the Engine Live-Data Virtual Laboratory.
 *
 * This is a simplified educational model. It is not Toyota 1NZ, OEM or
 * production ECU calibration data and must not be used to control hardware.
 */

export const ENGINE_STATES = Object.freeze({
  OFF: 0,
  PRIME: 1,
  CRANK: 2,
  RUN: 3,
  SHUTDOWN: 4,
});

export const ENGINE_STATE_LABELS = Object.freeze({
  [ENGINE_STATES.OFF]: "OFF",
  [ENGINE_STATES.PRIME]: "PRIME",
  [ENGINE_STATES.CRANK]: "CRANK",
  [ENGINE_STATES.RUN]: "RUN",
  [ENGINE_STATES.SHUTDOWN]: "SHUTDOWN",
});

export const INPUT_DEFINITIONS = Object.freeze({
  BatteryVoltage: { min: 8.0, max: 14.9, default: 13.8, unit: "V" },
  EngineSpeed: { min: 0, max: 6500, default: 800, unit: "rpm" },
  ThrottlePosition: { min: 0, max: 100, default: 2, unit: "%" },
  ManifoldPressure: { min: 20, max: 105, default: 35, unit: "kPa" },
  O2SensorVoltage: { min: 0.05, max: 0.95, default: 0.45, unit: "V" },
  ECT1Voltage: { min: 0.2, max: 4.8, default: 1.0, unit: "V" },
  ECT2Voltage: { min: 0.2, max: 4.8, default: 1.1, unit: "V" },
  AccessoryLoad: { min: 0, max: 100, default: 10, unit: "%" },
  IgnitionSwitch: { min: 0, max: 1, default: 0, unit: "state" },
  StartAuthorisation: { min: 0, max: 1, default: 0, unit: "state" },
  StartRequest: { min: 0, max: 1, default: 0, unit: "state" },
  StopRequest: { min: 0, max: 1, default: 0, unit: "state" },
  EmergencyStop: { min: 0, max: 1, default: 0, unit: "state" },
  ACRequest: { min: 0, max: 1, default: 0, unit: "state" },
});

export const DEFAULT_INPUTS = Object.freeze(
  Object.fromEntries(
    Object.entries(INPUT_DEFINITIONS).map(([name, definition]) => [name, definition.default]),
  ),
);

export function clamp(value, minimum, maximum) {
  const numeric = Number(value);
  const safeValue = Number.isFinite(numeric) ? numeric : minimum;
  return Math.min(Math.max(safeValue, minimum), maximum);
}

export function sanitizeInputs(rawInputs = {}) {
  const accepted = {};
  const clampedFields = {};

  for (const [name, definition] of Object.entries(INPUT_DEFINITIONS)) {
    const rawValue = rawInputs[name] ?? definition.default;
    const acceptedValue = clamp(rawValue, definition.min, definition.max);
    accepted[name] = acceptedValue;
    clampedFields[name] = Number(rawValue) !== acceptedValue;
  }

  return { accepted, clampedFields };
}

export function ectVoltageToTemperature(voltage) {
  const v = clamp(voltage, 0.2, 4.8);
  let temperature;

  if (v >= 4.3) {
    temperature = -20 + (4.8 - v) * 40;
  } else if (v >= 3.5) {
    temperature = (4.3 - v) * 31.25;
  } else if (v >= 2.5) {
    temperature = 25 + (3.5 - v) * 25;
  } else if (v >= 1.5) {
    temperature = 50 + (2.5 - v) * 25;
  } else if (v >= 1.0) {
    temperature = 75 + (1.5 - v) * 30;
  } else if (v >= 0.6) {
    temperature = 90 + (1.0 - v) * 37.5;
  } else if (v >= 0.3) {
    temperature = 105 + (0.6 - v) * (20 / 0.3);
  } else {
    temperature = 125 + (0.3 - v) * 100;
  }

  return clamp(temperature, -20, 135);
}

export function createInitialInternalState() {
  return {
    engineState: ENGINE_STATES.OFF,
    elapsedInState: 0,
    simulationTime: 0,
  };
}

export function updateStartRunState(inputs, previousState, dtSeconds = 0.05) {
  const dt = Math.max(0, Number(dtSeconds) || 0);
  let engineState = previousState?.engineState ?? ENGINE_STATES.OFF;
  let elapsedInState = (previousState?.elapsedInState ?? 0) + dt;
  const simulationTime = (previousState?.simulationTime ?? 0) + dt;

  const ignitionOn = inputs.IgnitionSwitch > 0.5;
  const authorised = inputs.StartAuthorisation > 0.5;
  const startRequested = inputs.StartRequest > 0.5;
  const stopRequested = inputs.StopRequest > 0.5;
  const emergencyStop = inputs.EmergencyStop > 0.5;

  const safeStart =
    ignitionOn &&
    authorised &&
    startRequested &&
    !emergencyStop &&
    inputs.BatteryVoltage >= 9.5;

  const transitionTo = (nextState) => {
    engineState = nextState;
    elapsedInState = 0;
  };

  switch (engineState) {
    case ENGINE_STATES.OFF:
      if (safeStart) transitionTo(ENGINE_STATES.PRIME);
      break;

    case ENGINE_STATES.PRIME:
      if (emergencyStop || stopRequested || !ignitionOn) {
        transitionTo(ENGINE_STATES.SHUTDOWN);
      } else if (elapsedInState >= 2.0) {
        transitionTo(ENGINE_STATES.CRANK);
      }
      break;

    case ENGINE_STATES.CRANK:
      if (
        emergencyStop ||
        stopRequested ||
        !ignitionOn ||
        inputs.BatteryVoltage < 8.5
      ) {
        transitionTo(ENGINE_STATES.SHUTDOWN);
      } else if (inputs.EngineSpeed >= 500) {
        transitionTo(ENGINE_STATES.RUN);
      } else if (elapsedInState >= 5.0) {
        transitionTo(ENGINE_STATES.SHUTDOWN);
      }
      break;

    case ENGINE_STATES.RUN:
      if (emergencyStop || stopRequested || !ignitionOn) {
        transitionTo(ENGINE_STATES.SHUTDOWN);
      }
      break;

    case ENGINE_STATES.SHUTDOWN:
    default:
      if (elapsedInState >= 0.5) transitionTo(ENGINE_STATES.OFF);
      break;
  }

  return {
    internalState: { engineState, elapsedInState, simulationTime },
    outputs: {
      EngineState: engineState,
      EngineStateLabel: ENGINE_STATE_LABELS[engineState],
      StateElapsedTime: elapsedInState,
      SafeStartCondition: Number(safeStart),
      FuelPumpState: Number(
        engineState === ENGINE_STATES.PRIME ||
          engineState === ENGINE_STATES.CRANK ||
          engineState === ENGINE_STATES.RUN,
      ),
      StarterState: Number(engineState === ENGINE_STATES.CRANK),
      InjectionEnable: Number(
        engineState === ENGINE_STATES.CRANK || engineState === ENGINE_STATES.RUN,
      ),
      IgnitionEnable: Number(
        engineState === ENGINE_STATES.CRANK || engineState === ENGINE_STATES.RUN,
      ),
      StartPermitted: Number(
        engineState === ENGINE_STATES.PRIME ||
          engineState === ENGINE_STATES.CRANK ||
          engineState === ENGINE_STATES.RUN,
      ),
    },
  };
}

export function calculateFuel(inputs, ect1Temperature, startRunOutputs) {
  const rpm = clamp(inputs.EngineSpeed, 0, 6500);
  const map = clamp(inputs.ManifoldPressure, 20, 105);
  const tps = clamp(inputs.ThrottlePosition, 0, 100);
  const o2 = clamp(inputs.O2SensorVoltage, 0.05, 0.95);
  const battery = clamp(inputs.BatteryVoltage, 8.0, 14.9);

  const EngineLoad = clamp(0.55 * ((map - 20) / 85) * 100 + 0.45 * tps, 0, 100);
  const LambdaEstimate = clamp(1.0 + (0.45 - o2) * 0.35, 0.75, 1.25);
  const ClosedLoopActive = Number(
    startRunOutputs.InjectionEnable > 0.5 && ect1Temperature >= 70 && rpm >= 600,
  );
  const STFT = ClosedLoopActive
    ? clamp((LambdaEstimate - 1.0) * 120, -25, 25)
    : 0;
  const WarmupEnrichment = clamp((70 - ect1Temperature) * 0.5, 0, 40);
  const BatteryCompensation = clamp((13.8 - battery) * 0.18, 0, 1.2);
  const BaseInjectorPW = clamp(
    1.0 + 0.00035 * rpm + 0.025 * (map - 20) + 0.012 * tps,
    1.0,
    15.0,
  );
  const InjectorPW = startRunOutputs.InjectionEnable
    ? clamp(
        (BaseInjectorPW + BatteryCompensation) *
          (1 + (STFT + WarmupEnrichment) / 100),
        0,
        20,
      )
    : 0;

  return {
    EngineLoad,
    LambdaEstimate,
    STFT,
    BaseInjectorPW,
    WarmupEnrichment,
    BatteryCompensation,
    InjectorPW,
    ClosedLoopActive,
  };
}

export function calculateIdleIgnition(inputs, ect1Temperature, startRunOutputs) {
  const rpm = clamp(inputs.EngineSpeed, 0, 6500);
  const tps = clamp(inputs.ThrottlePosition, 0, 100);
  const map = clamp(inputs.ManifoldPressure, 20, 105);
  const accessoryLoad = clamp(inputs.AccessoryLoad, 0, 100);

  const TargetIdleRPM = 750 + clamp((80 - ect1Temperature) * 5.625, 0, 450);
  const IdleActive = Number(
    startRunOutputs.EngineState === ENGINE_STATES.RUN && tps <= 5 && rpm < 2000,
  );
  const RPMError = IdleActive ? TargetIdleRPM - rpm : 0;
  const IdleControlDuty = IdleActive
    ? clamp(25 + 0.06 * RPMError + 0.25 * accessoryLoad, 0, 100)
    : 0;

  let IgnitionTiming;
  if (startRunOutputs.IgnitionEnable <= 0.5) {
    IgnitionTiming = 0;
  } else if (startRunOutputs.EngineState === ENGINE_STATES.CRANK) {
    IgnitionTiming = 5;
  } else {
    IgnitionTiming = clamp(
      10 + 0.004 * (rpm - 800) - 0.08 * (map - 35) + 0.015 * RPMError,
      -5,
      45,
    );
  }

  return {
    TargetIdleRPM,
    RPMError,
    IdleControlDuty,
    IgnitionTiming,
    IdleActive,
  };
}

export function calculateCooling(inputs, startRunOutputs) {
  const ECT1Temp = ectVoltageToTemperature(inputs.ECT1Voltage);
  const ECT2Temp = ectVoltageToTemperature(inputs.ECT2Voltage);
  const SensorDifference = Math.abs(ECT1Temp - ECT2Temp);
  const SensorDisagreement = Number(SensorDifference > 15);
  const ControlTemperature = Math.max(ECT1Temp, ECT2Temp);

  let FanDuty = 0;
  let WaterPumpDuty = 0;

  if (inputs.EmergencyStop > 0.5 || inputs.BatteryVoltage < 8.0) {
    FanDuty = 0;
    WaterPumpDuty = 0;
  } else if (SensorDisagreement > 0.5) {
    FanDuty = 100;
    WaterPumpDuty = 100;
  } else {
    if (ControlTemperature < 88) {
      FanDuty = 0;
    } else if (ControlTemperature < 95) {
      FanDuty = 20 + (ControlTemperature - 88) * (30 / 7);
    } else if (ControlTemperature < 105) {
      FanDuty = 50 + (ControlTemperature - 95) * 5;
    } else {
      FanDuty = 100;
    }

    if (inputs.ACRequest > 0.5 && startRunOutputs.EngineState >= ENGINE_STATES.CRANK) {
      FanDuty = Math.max(FanDuty, 35);
    }

    if (startRunOutputs.EngineState === ENGINE_STATES.RUN) {
      if (ControlTemperature < 50) {
        WaterPumpDuty = 35;
      } else if (ControlTemperature < 90) {
        WaterPumpDuty = 35 + (ControlTemperature - 50) * (35 / 40);
      } else if (ControlTemperature < 110) {
        WaterPumpDuty = 70 + (ControlTemperature - 90) * 1.5;
      } else {
        WaterPumpDuty = 100;
      }
    } else if (ControlTemperature > 95) {
      WaterPumpDuty = 60;
    }
  }

  FanDuty = clamp(FanDuty, 0, 100);
  WaterPumpDuty = clamp(WaterPumpDuty, 0, 100);

  return {
    ECT1Temp,
    ECT2Temp,
    SensorDifference,
    SensorDisagreement,
    ControlTemperature,
    FanDuty,
    WaterPumpDuty,
    CoolingLoopActive: Number(FanDuty > 0 || WaterPumpDuty > 0),
  };
}

export function stepEngineModel(rawInputs, previousInternalState, dtSeconds = 0.05) {
  const { accepted: inputs, clampedFields } = sanitizeInputs(rawInputs);
  const startRun = updateStartRunState(inputs, previousInternalState, dtSeconds);
  const cooling = calculateCooling(inputs, startRun.outputs);
  const fuel = calculateFuel(inputs, cooling.ECT1Temp, startRun.outputs);
  const idleIgnition = calculateIdleIgnition(inputs, cooling.ECT1Temp, startRun.outputs);

  return {
    inputs,
    clampedFields,
    internalState: startRun.internalState,
    outputs: {
      ...startRun.outputs,
      ...fuel,
      ...idleIgnition,
      ...cooling,
    },
  };
}

export function describeCurrentRelationship(result) {
  const { inputs, outputs } = result;

  const fuelDirection =
    outputs.STFT > 0.5
      ? "positive fuel correction adds fuel"
      : outputs.STFT < -0.5
        ? "negative fuel correction removes fuel"
        : "fuel correction is near zero";

  const idleMessage = outputs.IdleActive
    ? `actual RPM is ${outputs.RPMError >= 0 ? "below" : "above"} target by ${Math.abs(outputs.RPMError).toFixed(0)} rpm`
    : "idle control is inactive";

  const coolingMessage = outputs.SensorDisagreement
    ? "ECT disagreement activates the virtual full-duty fail-safe"
    : `control temperature is ${outputs.ControlTemperature.toFixed(1)} °C`;

  return {
    fuel: `O2 ${inputs.O2SensorVoltage.toFixed(2)} V gives lambda ${outputs.LambdaEstimate.toFixed(3)}; ${fuelDirection}.`,
    idle: `${idleMessage}; idle duty is ${outputs.IdleControlDuty.toFixed(1)}%.`,
    cooling: `${coolingMessage}; fan ${outputs.FanDuty.toFixed(1)}%, virtual pump ${outputs.WaterPumpDuty.toFixed(1)}%.`,
    startRun: `Engine state is ${outputs.EngineStateLabel}; fuel pump ${outputs.FuelPumpState ? "ON" : "OFF"}, starter ${outputs.StarterState ? "ON" : "OFF"}.`,
  };
}
