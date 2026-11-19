import {
  DEFAULTS,
  MODULE_ID,
  MODULE_VERSION,
  evaluate,
  initialState,
  stepFuelDeliveryModel,
} from "./model.mjs";

/** @typedef {{moduleId:string, moduleVersion:string, simulationTimeS:number,
 * simulationSettings:{durationS:number,timeStepS:number}, inputs:import('./model.mjs').FuelInputs,
 * outputs:import('./model.mjs').FuelOutputs, integrationVector:import('./model.mjs').FuelIntegrationVector,
 * status:import('./model.mjs').FuelStatus}} FuelPayload
 */
export class FuelSimulation {
  constructor(inputs = DEFAULTS) {
    this.reset(inputs);
  }
  reset(inputs = DEFAULTS) {
    const state = initialState(),
      result = evaluate(inputs, state);
    this.runId =
      globalThis.crypto?.randomUUID?.() ??
      `local-run-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    this.inputs = { ...inputs };
    this.state = state;
    this.running = false;
    this.error = null;
    this.history = [];
    this.comparison = null;
    this.result = result;
  }
  edit(inputs) {
    // Preserve the recorded run and its per-sample inputs; editing pauses it.
    this.running = false;
    if (inputs.simulationDurationS < this.state.simulationTimeS - 1e-9)
      throw Object.assign(
        new Error(
          `Duration cannot be shorter than the ${this.state.simulationTimeS.toFixed(2)} s already recorded. Reset before choosing a shorter run; existing history has been preserved.`,
        ),
        { field: "simulationDurationS" },
      );
    const result = evaluate(inputs, this.state);
    this.inputs = { ...inputs };
    this.result = result;
    this.comparison = null;
    this.error = null;
  }
  start() {
    this.reset(this.inputs);
    this.running = true;
  }
  resume() {
    if (
      !this.error &&
      this.state.simulationTimeS < this.inputs.simulationDurationS - 1e-9
    )
      this.running = true;
  }
  fail(error) {
    this.running = false;
    this.comparison = null;
    this.error = error.message || String(error);
    this.result = {
      ...this.result,
      status: {
        ...this.result.status,
        valid: false,
        severity: "error",
        optimisationAcceptable: false,
      },
    };
  }
  tick() {
    if (!this.running) return false;
    const remaining =
      this.inputs.simulationDurationS - this.state.simulationTimeS;
    const dt = Math.min(this.inputs.timeStepS, remaining);
    if (dt <= 1e-9) {
      this.running = false;
      return false;
    }
    try {
      this.result = stepFuelDeliveryModel(this.inputs, this.state, dt);
    } catch (error) {
      this.fail(error);
      return false;
    }
    this.state = this.result.state;
    this.history.push({
      simulationTimeS: this.state.simulationTimeS,
      inputs: { ...this.inputs },
      outputs: { ...this.result.outputs },
    });
    if (this.inputs.simulationDurationS - this.state.simulationTimeS <= 1e-9)
      this.running = false;
    return true;
  }
  assertHealthy() {
    if (this.error)
      throw new Error(
        `Calculation error: ${this.error} Correct inputs or Reset before comparing or exporting last-valid readings.`,
      );
  }
  /** @returns {FuelPayload} */
  payload() {
    this.assertHealthy();
    return {
      moduleId: MODULE_ID,
      moduleVersion: MODULE_VERSION,
      simulationTimeS: this.state.simulationTimeS,
      simulationSettings: {
        durationS: this.inputs.simulationDurationS,
        timeStepS: this.inputs.timeStepS,
      },
      inputs: { ...this.inputs },
      outputs: { ...this.result.outputs },
      integrationVector: [...this.result.integrationVector],
      status: {
        ...this.result.status,
        warnings: [...this.result.status.warnings],
      },
    };
  }
  compare() {
    this.assertHealthy();
    this.running = false;
    this.comparison = null;
    const solve = (scale) => {
      const run = new FuelSimulation({
        ...this.inputs,
        fuelOptimisationScale: scale,
      });
      run.start();
      while (run.running) run.tick();
      return run.payload();
    };
    try {
      this.comparison = {
        basis:
          "Two fresh full-duration runs with identical current inputs except optimisation scale; not a replay of edited history.",
        baseline: solve(1),
        adjusted: solve(this.inputs.fuelOptimisationScale),
      };
    } catch (error) {
      const failure = new Error(`Comparison failed: ${error.message}`);
      this.fail(failure);
      throw failure;
    }
    return this.comparison;
  }
  contexts() {
    const first = this.history[0],
      last = this.history.at(-1);
    const changedKeys = last
      ? Object.keys(this.inputs).filter(
          (key) => this.inputs[key] !== last.inputs[key],
        )
      : [];
    const inputSegments = this.history.reduce(
      (count, row, index) =>
        count +
        Number(
          index === 0 ||
            Object.keys(row.inputs).some(
              (key) => row.inputs[key] !== this.history[index - 1].inputs[key],
            ),
        ),
      0,
    );
    return {
      currentPreview: {
        label: "Current preview",
        inputs: { ...this.inputs },
        outputs: { ...this.result.outputs },
        simulationTimeS: this.state.simulationTimeS,
        differsFromLastRecordedSample: changedKeys.length > 0,
        changedKeys,
      },
      lastRecordedRun: last
        ? {
            label: "Last recorded run",
            runId: this.runId,
            sampleCount: this.history.length,
            firstTimeS: first.simulationTimeS,
            lastTimeS: last.simulationTimeS,
            firstInputs: { ...first.inputs },
            lastInputs: { ...last.inputs },
            lastOutputs: { ...last.outputs },
            inputSegments,
            basis:
              "Each history/CSV row retains its own inputs. Resume can record changed inputs in the same history.",
          }
        : null,
      freshComparison: this.comparison
        ? {
            label: "Fresh comparison",
            basis: this.comparison.basis,
            inputs: { ...this.inputs },
          }
        : null,
    };
  }
  evidence() {
    return {
      ...this.payload(),
      deployment: typeof document !== "undefined" ? JSON.parse(document.getElementById("platform-deployment")?.textContent || "null") : null,
      runId: this.runId,
      exportedAt: new Date().toISOString(),
      topLevelValueRole:
        "Current preview; recorded values are in history and contexts.lastRecordedRun",
      contexts: this.contexts(),
      history: this.history,
      comparison: this.comparison,
    };
  }
  csv() {
    this.assertHealthy();
    const inputKeys = Object.keys(this.inputs),
      outputKeys = Object.keys(this.result.outputs);
    const columns = [
      "simulationTimeS",
      ...inputKeys.map((k) => `input_${k}`),
      ...outputKeys,
    ];
    return [
      columns.join(","),
      ...this.history.map((row) =>
        [
          row.simulationTimeS,
          ...inputKeys.map((k) => row.inputs[k]),
          ...outputKeys.map((k) => row.outputs[k]),
        ].join(","),
      ),
    ].join("\r\n");
  }
}
