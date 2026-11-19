import { INPUTS, DT } from "./reference.mjs";
import { SPEC } from "./spec.mjs";
import { ENGINE_BUILD } from "./build.mjs";

export function evidencePackage(
  simulation,
  exportedAt = new Date().toISOString(),
) {
  const csv = simulation.csv();
  const columns = csv.split("\r\n", 1)[0].split(",");
  const definitions = Object.fromEntries(
    SPEC.outputs.map((signal) => [signal.name, signal]),
  );
  const labels = {
    StartAuthorisation: "Simulated authorisation",
    WaterPumpDuty: "Virtual electric-water-pump duty",
    SafeStartCondition: "Start request accepted",
  };
  const history = simulation.history;
  const first = history[0],
    last = history.at(-1);
  return {
    schema: "atu.engine-live-data.evidence.v1",
    module: "Engine Live Data Demonstration",
    student: "Kofi Frempong",
    runId: simulation.runId,
    caseName: simulation.caseName,
    exportedAt,
    build: ENGINE_BUILD,
    deployment: typeof document !== "undefined" ? JSON.parse(document.getElementById("platform-deployment")?.textContent || "null") : null,
    sampleIntervalS: DT,
    sampleConvention:
      "First call is sample 0 at time 0. Outputs follow the transition evaluated on that call. State elapsed accumulates double precision as specified by the approved guide.",
    timing: {
      nominalThresholdsS: { PRIME: 2, CRANK: 5, SHUTDOWN: 0.5 },
      observedUninterruptedTicks: { PRIME: 40, CRANK: 101, SHUTDOWN: 11 },
      nativeSlxVerification:
        "Canonical SLX embedded source reviewed on 19 November 2026 and compared with the original browser exports. Source-level timing/branch ordering agrees; no MATLAB solver execution.",
    },
    window: {
      firstTimeS: first?.SimulationTime ?? null,
      lastTimeS: last?.SimulationTime ?? null,
      retainedSamples: history.length,
      totalSamples: simulation.internal.sampleIndex + 1,
      capSeconds: 60,
      capSamples: 1201,
      truncated: simulation.internal.sampleIndex + 1 > history.length,
      warning:
        "CSV retains the latest 60 seconds, up to 1201 samples. This package does not reconstruct discarded samples.",
    },
    transitions: {
      events: simulation.events.map((event) => ({ ...event })),
      totalTransitions: simulation.totalTransitions,
      retainedTransitionCount: simulation.events.filter(
        (event) => event.fromState !== undefined,
      ).length,
      eventLimit: 100,
      warning:
        "Event log retains its most recent 100 entries; sample counts are not independent vehicle observations.",
    },
    pendingInputs: { ...simulation.rawInputs },
    signalDictionary: columns.map((name) => ({
      name,
      label: labels[name] || definitions[name]?.label || name,
      role:
        name === "SimulationTime"
          ? "sample time"
          : Object.hasOwn(INPUTS, name)
            ? "accepted input"
            : "calculated output",
      unit:
        name === "SimulationTime"
          ? "s"
          : INPUTS[name]?.unit ||
            definitions[name]?.unit ||
            (name === "ActualRPM"
              ? "rpm"
              : name === "SafeStartCondition"
                ? "0/1"
                : "text"),
    })),
    csv: {
      fileName: "engine-live-data-virtual.csv",
      content: csv,
      columns,
      numericColumnsCompatible: true,
    },
    scope:
      "Educational virtual accepted inputs and calculated commands. Not vehicle measurements, OEM calibration, biometric recognition or physical engine testing.",
  };
}
