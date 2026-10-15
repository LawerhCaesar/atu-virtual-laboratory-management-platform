import {
  DEFAULT_INPUTS, ENGINE_STATES, ENGINE_STATE_LABELS, sanitizeInputs,
  createInitialInternalState, stepEngineModel, calculateFuel,
  calculateIdleIgnition, calculateCooling,
} from "./model.mjs";
import { SPEC } from "./spec.mjs";

export const STEP = 0.05;
export const HISTORY_SECONDS = 60;

export class EngineSimulation {
  constructor() { this.reset(); }

  reset() {
    this.rawInputs = { ...DEFAULT_INPUTS };
    this.internal = createInitialInternalState();
    this.history = [];
    this.running = false;
    this.pulses = {};
    this.result = this.evaluate();
  }

  evaluate() {
    const { accepted: inputs, clampedFields } = sanitizeInputs(this.rawInputs);
    const s = this.internal.engineState;
    const enabled = Number(s === ENGINE_STATES.CRANK || s === ENGINE_STATES.RUN);
    const active = Number([ENGINE_STATES.PRIME, ENGINE_STATES.CRANK, ENGINE_STATES.RUN].includes(s));
    const start = {
      EngineState: s, EngineStateLabel: ENGINE_STATE_LABELS[s],
      StateElapsedTime: this.internal.elapsedInState,
      SafeStartCondition: Number(inputs.IgnitionSwitch > 0.5 && inputs.StartAuthorisation > 0.5 &&
        inputs.StartRequest > 0.5 && inputs.EmergencyStop < 0.5 && inputs.BatteryVoltage >= 9.5),
      FuelPumpState: active, StarterState: Number(s === ENGINE_STATES.CRANK),
      InjectionEnable: enabled, IgnitionEnable: enabled, StartPermitted: active,
    };
    const cooling = calculateCooling(inputs, start);
    return { inputs, clampedFields, internalState: { ...this.internal }, outputs: {
      ...start, ...calculateFuel(inputs, cooling.ECT1Temp, start),
      ...calculateIdleIgnition(inputs, cooling.ECT1Temp, start), ...cooling,
    } };
  }

  setInput(name, value) {
    if (!(name in DEFAULT_INPUTS)) throw new Error("Unknown engine input");
    if (name === "EmergencyStop" && this.rawInputs.EmergencyStop) return;
    this.rawInputs[name] = value;
    this.result = this.evaluate();
  }

  loadPreset(index) {
    const preset = SPEC.presets[index];
    if (!preset) throw new Error("Unknown preset");
    Object.assign(this.rawInputs, preset.values);
    this.result = this.evaluate();
  }

  pulse(name) {
    if (!["StartRequest", "StopRequest"].includes(name)) throw new Error("Not a momentary input");
    this.rawInputs[name] = 1;
    this.pulses[name] = 10;
    this.result = this.evaluate();
  }

  emergencyStop() {
    this.rawInputs.EmergencyStop = 1;
    if ([1, 2, 3].includes(this.internal.engineState)) {
      this.internal.engineState = ENGINE_STATES.SHUTDOWN;
      this.internal.elapsedInState = 0;
    }
    this.result = this.evaluate();
  }

  step() {
    if (!this.running) return this.result;
    this.result = stepEngineModel(this.rawInputs, this.internal, STEP);
    this.internal = this.result.internalState;
    this.history.push(this.row());
    const earliest = this.internal.simulationTime - HISTORY_SECONDS;
    this.history = this.history.filter(row => row.SimulationTime >= earliest - 1e-8);
    for (const name of Object.keys(this.pulses)) {
      this.pulses[name] -= 1;
      if (this.pulses[name] <= 0) {
        this.rawInputs[name] = 0;
        delete this.pulses[name];
      }
    }
    // Retain the recorded pulse in history; current controls show its release.
    this.result = this.evaluate();
    return this.result;
  }

  row() {
    return { SimulationTime: this.internal.simulationTime, ...this.result.inputs, ...this.result.outputs };
  }

  csv() {
    const columns = ["SimulationTime", ...SPEC.inputs.map(x => x.name),
      ...SPEC.outputs.map(x => x.name), "EngineStateLabel", "SafeStartCondition"];
    const rows = [...this.history];
    const current = this.row();
    if (rows.length && Math.abs(rows.at(-1).SimulationTime - current.SimulationTime) < 1e-8) rows[rows.length - 1] = current;
    else rows.push(current);
    return [columns.join(","), ...rows.map(row => columns.map(key => row[key]).join(","))].join("\r\n");
  }
}
