import { parameters, contract, examples } from "./catalog.mjs";
import { calculate, initialState, lookup } from "./graph.mjs";
const MODEL_HASH = "6ff353c6fd9cbb994c163e26ad183b9e6f780f45d4ac4ec788bcbc4528cf8987";
const defaults = () => ({ schemaVersion: 1, modelVersion: MODEL_HASH, duration_s: 3600, fixedStep_s: 1, parameters: Object.fromEntries(parameters.map((p) => [p.key, structuredClone(p.default_value)])), name: "Default cycle", priceNote: "" });
function validateScenario(input) {
  const errors = [], warnings = [];
  const s = input;
  if (!s || typeof s !== "object" || s.schemaVersion !== 1 || s.modelVersion !== MODEL_HASH || s.fixedStep_s !== 1) return { scenario: null, errors: ["Unsupported scenario schema, model hash or timestep."], warnings };
  if (!Number.isInteger(s.duration_s) || s.duration_s < 1 || s.duration_s > 14400) errors.push("Duration must be a whole number from 1 to 14400 seconds (browser resource limit).");
  const p = s.parameters;
  if (!p || typeof p !== "object" || Array.isArray(p)) return { scenario: null, errors: ["Settings must be an object."], warnings };
  if (Object.keys(p).some((k) => !parameters.some((x) => x.key === k))) errors.push("Unknown parameter in scenario.");
  for (const c of parameters) {
    const v = p[c.key], a = Array.isArray(v) ? v : [v];
    if (Array.isArray(c.default_value) !== Array.isArray(v) || a.some((x) => typeof x !== "number" || !Number.isFinite(x) || Math.abs(x) > 1e9) || Array.isArray(v) && v.length !== c.default_value.length) errors.push(`${c.label}: enter finite numeric values of the specified size (magnitude \u2264 1e9).`);
  }
  if (errors.length) return { scenario: null, errors, warnings };
  const n = (k) => p[k], arr = (k) => p[k];
  const need = (ok, msg) => {
    if (!ok) errors.push(msg);
  };
  const inc = (a) => a.every((v, i) => !i || v > a[i - 1]);
  for (const c of parameters) {
    if (Array.isArray(p[c.key])) continue;
    const k = c.key, v = n(k);
    if (k.includes("efficiency") || k === "maximum_modulation_index") need(v > 0 && v <= 1, `${c.label} must be in (0, 1].`);
    else if (!/temperature|temp_C|road_gradient|target_speed|auxiliary_electrical/.test(k)) need(v >= 0, `${c.label} cannot be negative.`);
  }
  for (const k of ["battery_ns", "battery_np", "motor_pole_pairs"]) need(Number.isInteger(n(k)) && n(k) >= 1, `${k} must be a positive integer.`);
  for (const k of ["battery_cell_capacity_Ah", "battery_cell_nominal_V", "battery_cell_resistance_ohm", "battery_mass_kg", "battery_cp_J_kgK", "converted_kerb_mass_kg", "diesel_kerb_mass_kg", "loaded_wheel_radius_m", "electric_reduction_ratio", "hydrogen_lhv_kwh_per_kg", "diesel_lhv_kwh_per_litre", "regulated_dc_link_voltage_v", "fuel_cell_nominal_output_voltage_v", "motor_pm_flux_wb", "scaled_dq_inductance_h", "scaled_phase_resistance_ohm", "gross_mass_screen_kg"]) need(n(k) > 0, `${k} must be positive.`);
  for (const k of ["fuel_cell_enable_1_or_0", "overrun_fuel_cut_enable_1_or_0", "profile_1_cycle_0_constant"]) need([0, 1].includes(n(k)), `${k} must be 0 or 1.`);
  const volts = arr("battery_cell_voltage_limits_V"), soc = arr("battery_soc_levels_pct"), bp = arr("battery_ocv_soc_pct"), ocv = arr("battery_ocv_cell_V");
  need(inc(volts) && volts[0] > 0, "Cell voltage limits must be increasing and positive.");
  need(n("battery_cell_nominal_V") >= volts[0] && n("battery_cell_nominal_V") <= volts[1], "Nominal cell voltage must be within voltage limits.");
  need(inc(soc) && soc[0] >= 0 && soc[3] <= 100, "SOC thresholds must increase within 0\u2013100%.");
  need(n("battery_initial_soc_pct") >= soc[0] && n("battery_initial_soc_pct") <= soc[3], "Initial SOC must be within the battery operating window.");
  need(arr("battery_current_ratings_C").every((x) => x >= 0), "Charge/discharge C-rates cannot be negative.");
  need(arr("battery_coulombic_efficiencies").every((x) => x > 0 && x <= 1), "Coulombic efficiencies must be in (0, 1].");
  for (const k of ["battery_charge_temp_limits_C", "battery_discharge_temp_limits_C"]) need(inc(arr(k)), `${k}: four strictly increasing temperatures required.`);
  need(inc(bp) && bp[0] === 0 && bp[12] === 100, "OCV requires 13 strictly increasing SOC entries from 0 to 100.");
  need(ocv.every((v, i) => v >= volts[0] && v <= volts[1] && (!i || v >= ocv[i - 1])), "OCV voltages must be nondecreasing and within voltage limits.");
  need(n("fuel_cell_on_threshold_percent") < n("fuel_cell_off_threshold_percent") && n("fuel_cell_off_threshold_percent") <= 100, "Fuel-cell ON threshold must be below OFF, within 0\u2013100%.");
  for (const [k, lo, hi] of [["target_speed_km_per_h", 0, 100], ["road_gradient_percent", -20, 20], ["auxiliary_electrical_load_kw", 0, 20]]) {
    if (n(k) < lo || n(k) > hi) warnings.push(`${k}: model effective value is ${Math.max(lo, Math.min(hi, n(k)))}; original input retained.`);
  }
  if (typeof s.name !== "string" || s.name.length > 120 || typeof s.priceNote !== "string" || s.priceNote.length > 500) errors.push("Scenario name/price note is missing or too long.");
  return { scenario: errors.length ? null : structuredClone(s), errors, warnings };
}
function environment(p) {
  const e = {};
  for (const c of parameters) if (c.scope !== "operating_and_components") e[c.parameter] = structuredClone(p[c.key]);
  e.initial_soc = e.initial_soc_pct / 100;
  [e.soc_min, e.soc_reserve, e.soc_taper, e.soc_max] = e.soc_levels_pct.map((x) => x / 100);
  [e.cell_min_V, e.cell_max_V] = e.cell_voltage_limits_V;
  [e.charge_rate_C, e.discharge_rate_C] = e.current_ratings_C;
  [e.charge_T1_C, e.charge_T2_C, e.charge_T3_C, e.charge_T4_C] = e.charge_temp_limits_C;
  [e.discharge_T1_C, e.discharge_T2_C, e.discharge_T3_C, e.discharge_T4_C] = e.discharge_temp_limits_C;
  [e.eta_charge, e.eta_discharge] = e.coulombic_efficiencies;
  e.ocv_soc = e.ocv_soc_pct.map((x) => x / 100);
  e.dt_s = 1;
  const xs = [...e.ocv_soc.filter((x) => x < e.initial_soc), e.initial_soc];
  const areas = [];
  for (let i = 1; i < xs.length; i++) areas.push((xs[i] - xs[i - 1]) * (lookup(xs[i], e.ocv_soc, e.ocv_cell_V) + lookup(xs[i - 1], e.ocv_soc, e.ocv_cell_V)) / 2);
  const integral = areas.reduce((total, area) => total + area, 0);
  e.initial_stored_energy_kWh = e.ns * e.np * e.cell_capacity_Ah / 1e3 * integral;
  return e;
}
function createSimulation(input) {
  const { scenario, errors } = validateScenario(input);
  if (!scenario) throw Error(errors.join("\n"));
  const e = environment(scenario.parameters);
  return { scenario, time_s: 0, delays: initialState(e), environment: e };
}
function stepSimulation(state) {
  if (state.time_s > state.scenario.duration_s) throw Error("Simulation is complete.");
  const r = calculate(state.time_s, state.delays, state.scenario.parameters, state.environment);
  if (!Object.values(r.streams).flat().every(Number.isFinite) || !r.nextState.every(Number.isFinite)) throw Error(`Nonfinite result at ${state.time_s} s. Review component settings.`);
  return { sample: { time_s: state.time_s, streams: r.streams }, nextState: { ...state, time_s: state.time_s + 1, delays: r.nextState } };
}
function runScenario(s, cancel = () => false, runId = "local") {
  let state = createSimulation(s);
  const samples = [];
  while (state.time_s <= state.scenario.duration_s) {
    if (cancel()) throw Error("Cancelled");
    const r = stepSimulation(state);
    samples.push(r.sample);
    state = r.nextState;
  }
  return { schemaVersion: 1, runId, scenario: state.scenario, samples };
}
function named(sample, stream = "comparison") {
  return Object.fromEntries(contract.streams[stream].columns.map((c, i) => [c.key, sample.streams[stream][i]]));
}
function toDisplaySample(sample, scenario) {
  const v = named(sample), e = named(sample, "electric"), d = named(sample, "diesel");
  const prices = ["electricity_ghs_per_kwh", "delivered_hydrogen_ghs_per_kg", "diesel_ghs_per_litre"].every((k) => scenario.parameters[k] > 0);
  const reason = v.commanded_distance_km <= 1e-4 ? "Zero commanded distance" : e.dc_unmet_energy_kwh >= 1e-6 || d.diesel_unmet_energy_kwh >= 1e-6 ? "Requested demand not fully supported" : "";
  const costReason = !prices ? "Enter all three energy prices" : reason || (v.battery_depletion_kwh < -1e-3 ? "Battery ended with a surplus" : "");
  return { values: v, electric: e, diesel: d, comparisonReason: reason, costReason, pricesEntered: prices, energySaving: v.comparison_feasible === 1 ? v.energy_saving_pct : null, costSaving: v.cost_valid === 1 ? v.cost_saving_ghs : null, electricRefill: prices ? v.electric_refill_ghs : null, dieselRefill: prices ? v.diesel_refill_ghs : null };
}
function exportScenario(s) {
  const v = validateScenario(s);
  if (!v.scenario) throw Error(v.errors.join("\n"));
  return JSON.stringify(v.scenario, null, 2);
}
function importScenario(s) {
  if (s.length > 5e4) throw Error("Scenario file is too large.");
  const v = validateScenario(JSON.parse(s));
  if (!v.scenario) throw Error(v.errors.join("\n"));
  return v.scenario;
}
function exportResultsCsv(r, stream = "comparison") {
  if (!contract.streams[stream]) throw Error("Unknown stream");
  return r.samples.map((s) => [s.time_s, ...s.streams[stream]].join(",")).join("\n") + "\n";
}
const exportResultsJson = (r) => JSON.stringify({ ...r, outputContract: contract });
function exampleScenario(id) {
  const c = examples.find((x) => x.id === id);
  if (!c) throw Error("Unknown example");
  const s = defaults();
  s.duration_s = c.duration_s;
  s.name = c.id.replaceAll("_", " ");
  for (const p of c.overrides) s.parameters[p.key] = structuredClone(p.value);
  if (c.overrides.some((x) => /ghs/.test(x.key))) s.priceNote = "Illustrative test prices; not market quotations.";
  return s;
}
export {
  MODEL_HASH,
  contract,
  createSimulation,
  defaults,
  environment,
  exampleScenario,
  examples,
  exportResultsCsv,
  exportResultsJson,
  exportScenario,
  importScenario,
  named,
  parameters,
  runScenario,
  stepSimulation,
  toDisplaySample,
  validateScenario
};
