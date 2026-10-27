import {DEFAULTS, MODULE_ID, MODULE_VERSION, evaluate, initialState, stepFuelDeliveryModel} from "./model.mjs";

/** @typedef {{moduleId:string, moduleVersion:string, simulationTimeS:number,
 * simulationSettings:{durationS:number,timeStepS:number}, inputs:import('./model.mjs').FuelInputs,
 * outputs:import('./model.mjs').FuelOutputs, integrationVector:import('./model.mjs').FuelIntegrationVector,
 * status:import('./model.mjs').FuelStatus}} FuelPayload
 */
export class FuelSimulation {
  constructor(inputs = DEFAULTS) { this.reset(inputs); }
  reset(inputs = DEFAULTS) {
    const state = initialState(), result = evaluate(inputs, state);
    this.inputs = {...inputs}; this.state = state; this.running = false; this.error = null;
    this.history = []; this.comparison = null; this.result = result;
  }
  edit(inputs) {
    // Preserve the recorded run and its per-sample inputs; editing pauses it.
    this.running = false;
    if (inputs.simulationDurationS < this.state.simulationTimeS - 1e-9)
      throw Object.assign(new Error(`Duration cannot be shorter than the ${this.state.simulationTimeS.toFixed(2)} s already recorded. Reset before choosing a shorter run; existing history has been preserved.`), {field: "simulationDurationS"});
    const result = evaluate(inputs, this.state);
    this.inputs = {...inputs}; this.result = result; this.comparison = null; this.error = null;
  }
  start() { this.reset(this.inputs); this.running = true; }
  resume() { if (!this.error && this.state.simulationTimeS < this.inputs.simulationDurationS - 1e-9) this.running = true; }
  fail(error) {
    this.running = false; this.comparison = null; this.error = error.message || String(error);
    this.result = {...this.result, status: {...this.result.status, valid: false, severity: "error", optimisationAcceptable: false}};
  }
  tick() {
    if (!this.running) return false;
    const remaining = this.inputs.simulationDurationS - this.state.simulationTimeS;
    const dt = Math.min(this.inputs.timeStepS, remaining);
    if (dt <= 1e-9) { this.running = false; return false; }
    try { this.result = stepFuelDeliveryModel(this.inputs, this.state, dt); }
    catch (error) { this.fail(error); return false; }
    this.state = this.result.state;
    this.history.push({simulationTimeS: this.state.simulationTimeS, inputs: {...this.inputs}, outputs: {...this.result.outputs}});
    if (this.inputs.simulationDurationS - this.state.simulationTimeS <= 1e-9) this.running = false;
    return true;
  }
  assertHealthy() { if (this.error) throw new Error(`Calculation error: ${this.error} Correct inputs or Reset before comparing or exporting last-valid readings.`); }
  /** @returns {FuelPayload} */
  payload() {
    this.assertHealthy();
    return {moduleId: MODULE_ID, moduleVersion: MODULE_VERSION, simulationTimeS: this.state.simulationTimeS,
      simulationSettings: {durationS: this.inputs.simulationDurationS, timeStepS: this.inputs.timeStepS},
      inputs: {...this.inputs}, outputs: {...this.result.outputs}, integrationVector: [...this.result.integrationVector],
      status: {...this.result.status, warnings: [...this.result.status.warnings]}};
  }
  compare() {
    this.assertHealthy(); this.running = false; this.comparison = null;
    const solve = scale => {
      const run = new FuelSimulation({...this.inputs, fuelOptimisationScale: scale});
      run.start(); while (run.running) run.tick(); return run.payload();
    };
    try {
      this.comparison = {basis: "Two fresh full-duration runs with identical current inputs except optimisation scale; not a replay of edited history.",
        baseline: solve(1), adjusted: solve(this.inputs.fuelOptimisationScale)};
    } catch (error) {
      const failure = new Error(`Comparison failed: ${error.message}`);
      this.fail(failure); throw failure;
    }
    return this.comparison;
  }
  csv() {
    this.assertHealthy();
    const inputKeys = Object.keys(this.inputs), outputKeys = Object.keys(this.result.outputs);
    const columns = ["simulationTimeS", ...inputKeys.map(k => `input_${k}`), ...outputKeys];
    return [columns.join(","), ...this.history.map(row => [row.simulationTimeS, ...inputKeys.map(k => row.inputs[k]), ...outputKeys.map(k => row.outputs[k])].join(","))].join("\r\n");
  }
}
