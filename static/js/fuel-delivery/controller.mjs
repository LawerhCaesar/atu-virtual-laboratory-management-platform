import {DEFAULTS, MODULE_ID, MODULE_VERSION, evaluate, initialState, stepFuelDeliveryModel} from "./model.mjs";

export class FuelSimulation {
  constructor(inputs = DEFAULTS) { this.reset(inputs); }
  reset(inputs = DEFAULTS) {
    this.inputs = {...inputs}; this.state = initialState(); this.running = false;
    this.history = []; this.comparison = null; this.result = evaluate(this.inputs, this.state);
  }
  edit(inputs) {
    // Preserve the recorded run and its per-sample inputs; editing pauses it.
    const result = evaluate(inputs, this.state);
    this.running = false; this.inputs = {...inputs}; this.result = result; this.comparison = null;
  }
  start() { this.reset(this.inputs); this.running = true; }
  resume() { if (this.state.simulationTimeS < this.inputs.simulationDurationS - 1e-9) this.running = true; }
  tick() {
    if (!this.running) return false;
    const remaining = this.inputs.simulationDurationS - this.state.simulationTimeS;
    const dt = Math.min(this.inputs.timeStepS, remaining);
    if (dt <= 1e-9) { this.running = false; return false; }
    this.result = stepFuelDeliveryModel(this.inputs, this.state, dt); this.state = this.result.state;
    this.history.push({simulationTimeS: this.state.simulationTimeS, inputs: {...this.inputs}, outputs: {...this.result.outputs}});
    if (this.inputs.simulationDurationS - this.state.simulationTimeS <= 1e-9) this.running = false;
    return true;
  }
  payload() {
    return {moduleId: MODULE_ID, moduleVersion: MODULE_VERSION, simulationTimeS: this.state.simulationTimeS,
      simulationSettings: {durationS: this.inputs.simulationDurationS, timeStepS: this.inputs.timeStepS},
      inputs: {...this.inputs}, outputs: {...this.result.outputs}, integrationVector: [...this.result.integrationVector],
      status: {...this.result.status, warnings: [...this.result.status.warnings]}};
  }
  compare() {
    const solve = scale => {
      const run = new FuelSimulation({...this.inputs, fuelOptimisationScale: scale});
      run.start(); while (run.running) run.tick(); return run.payload();
    };
    this.comparison = {basis: "Two fresh full-duration runs with identical current inputs except optimisation scale; not a replay of edited history.",
      baseline: solve(1), adjusted: solve(this.inputs.fuelOptimisationScale)};
    return this.comparison;
  }
  csv() {
    const inputKeys = Object.keys(this.inputs), outputKeys = Object.keys(this.result.outputs);
    const columns = ["simulationTimeS", ...inputKeys.map(k => `input_${k}`), ...outputKeys];
    return [columns.join(","), ...this.history.map(row => [row.simulationTimeS, ...inputKeys.map(k => row.inputs[k]), ...outputKeys.map(k => row.outputs[k])].join(","))].join("\r\n");
  }
}
