import { EngineSimulation, STEP } from "./controller.mjs";
import { SPEC } from "./spec.mjs";
import { ENGINE_STATE_LABELS, describeCurrentRelationship } from "./model.mjs";

const root = document.querySelector("#engine-demo");
if (root) initialise();

function initialise() {
  const simulation = new EngineSimulation();
  let cutaway = null, pageGone = false, cutawayLoading = false, cutawayClosed = false;
  const byId = id => document.getElementById(id);
  const make = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const labels = {
    ECT1Voltage: "Virtual ECT1 sensor voltage", ECT2Voltage: "Virtual ECT2 sensor voltage",
    ECT1Temp: "Virtual ECT1 temperature", ECT2Temp: "Virtual ECT2 temperature",
    SensorDifference: "ECT sensor difference", ControlTemperature: "Control temperature",
    EngineLoad: "Engine load", LambdaEstimate: "Lambda estimate",
    STFT: "STFT / equivalent closed-loop fuel correction", WarmupEnrichment: "Warm-up enrichment",
    BatteryCompensation: "Battery compensation", BaseInjectorPW: "Base injector pulse width",
    TargetIdleRPM: "Target idle speed", RPMError: "RPM error",
    InjectorPW: "Final injector pulse width", IdleControlDuty: "Idle-control duty",
    IgnitionTiming: "Ignition timing", FanDuty: "PWM fan duty",
    WaterPumpDuty: "Virtual electric-water-pump duty", FuelPumpState: "Fuel-pump command",
    StarterState: "Starter command", InjectionEnable: "Injection enabled",
    IgnitionEnable: "Ignition enabled", StartPermitted: "Start permitted",
    ClosedLoopActive: "Closed-loop active", IdleActive: "Idle active",
    CoolingLoopActive: "Cooling-loop active", SensorDisagreement: "ECT sensor disagreement",
    EngineState: "Engine state", StateElapsedTime: "Elapsed time in state",
  };
  const meanings = {
    BatteryVoltage: "Used for safe-start permission and injector battery compensation.",
    EngineSpeed: "Student-selected RPM; affects starting, injection, idle and ignition.",
    ThrottlePosition: "TPS: throttle position; affects load, injection and idle activation.",
    ManifoldPressure: "MAP: manifold absolute pressure; affects load, injection and timing.",
    O2SensorVoltage: "Simplified oxygen feedback used to estimate lambda and fuel correction.",
    ECT1Voltage: "Virtual ECT1 input; affects fuel, idle and cooling calculations.",
    ECT2Voltage: "Virtual ECT2 input; used for cooling demand and sensor plausibility.",
    AccessoryLoad: "Represents the added idle-control demand of electrical accessories.",
    IgnitionSwitch: "Simulated ignition status; turning it off requests shutdown.",
    StartAuthorisation: "Simulates fingerprint permission; no biometric recognition is performed.",
    ACRequest: "Requests at least 35% fan duty when state code is CRANK or higher.",
    StartRequest: "A 0.5-second virtual voice/manual request; it cannot bypass safe-start checks.",
    StopRequest: "A 0.5-second virtual request for normal shutdown.",
    EmergencyStop: "Latched emergency request overrides engine and cooling commands.",
    ECT1Temp: "Educational temperature calculated from virtual ECT1 voltage.",
    ECT2Temp: "Educational temperature calculated from virtual ECT2 voltage.",
    SensorDifference: "Absolute difference between the two calculated temperatures.",
    ControlTemperature: "The hotter calculated coolant temperature controls cooling.",
    EngineLoad: "Weighted load estimate from MAP and TPS.",
    LambdaEstimate: "Simplified air/fuel indication: above 1 is lean, below 1 is rich.",
    STFT: "Positive correction adds fuel; negative correction removes fuel when closed loop is active.",
    WarmupEnrichment: "Additional fuel percentage below 70 °C.",
    BatteryCompensation: "Injector delay compensation at lower battery voltage.",
    BaseInjectorPW: "Uncorrected injection duration derived from RPM, MAP and TPS.",
    TargetIdleRPM: "Coolant-dependent idle target, from 750 to 1200 rpm.",
    RPMError: "Target minus actual RPM while idle control is active.",
    InjectorPW: "Corrected injection duration; zero when injection is disabled.",
    IdleControlDuty: "Idle actuator duty based on speed error and accessory load.",
    IgnitionTiming: "Commanded ignition advance in degrees before top dead centre.",
    FanDuty: "Virtual pulse-width-modulated fan command.",
    WaterPumpDuty: "Virtual electric pump command; no electric pump exists in the physical 1NZ setup.",
    FuelPumpState: "Fuel-pump relay is on during PRIME, CRANK and RUN.",
    StarterState: "Starter relay is on only during CRANK.",
    InjectionEnable: "Injection is allowed only during CRANK and RUN.",
    IgnitionEnable: "Ignition is allowed only during CRANK and RUN.",
    StartPermitted: "Indicates an active PRIME, CRANK or RUN sequence.",
    ClosedLoopActive: "Requires enabled injection, ECT1 at least 70 °C and RPM at least 600.",
    IdleActive: "Requires RUN, TPS at most 5% and RPM below 2000.",
    CoolingLoopActive: "At least one virtual cooling actuator has nonzero duty.",
    SensorDisagreement: "Set when virtual ECT temperatures differ by more than 15 °C.",
    EngineState: "OFF, PRIME, CRANK, RUN or SHUTDOWN.",
    StateElapsedTime: "Virtual seconds since the current engine state was entered.",
  };
  const metadata = Object.fromEntries([...SPEC.inputs, ...SPEC.outputs].map(signal => [signal.name, signal]));
  const categories = { measured: "Measured/status input", calculated: "ECU-calculated value",
    commanded: "Commanded output", status: "Operating status" };
  const systems = {
    fuel: { title: "Fuel and injection", flow: SPEC.ui.dependencyFlows[0],
      measured: ["O2SensorVoltage", "EngineSpeed", "ManifoldPressure", "ThrottlePosition", "BatteryVoltage"],
      calculated: ["ECT1Temp", "EngineLoad", "LambdaEstimate", "STFT", "WarmupEnrichment", "BatteryCompensation", "BaseInjectorPW"],
      commanded: ["InjectorPW", "InjectionEnable"], status: ["ClosedLoopActive"] },
    idle: { title: "Idle and ignition", flow: SPEC.ui.dependencyFlows[1],
      measured: ["EngineSpeed", "ThrottlePosition", "ManifoldPressure", "AccessoryLoad"],
      calculated: ["ECT1Temp", "TargetIdleRPM", "RPMError"],
      commanded: ["IdleControlDuty", "IgnitionTiming"], status: ["IdleActive"] },
    cooling: { title: "Cooling", flow: SPEC.ui.dependencyFlows[2],
      measured: ["ECT1Voltage", "ECT2Voltage", "ACRequest", "BatteryVoltage"],
      calculated: ["ECT1Temp", "ECT2Temp", "SensorDifference", "ControlTemperature"],
      commanded: ["FanDuty", "WaterPumpDuty"], status: ["SensorDisagreement", "CoolingLoopActive"] },
    startRun: { title: "Start and run", flow: SPEC.ui.dependencyFlows[3],
      measured: ["IgnitionSwitch", "StartAuthorisation", "StartRequest", "StopRequest", "EmergencyStop", "BatteryVoltage", "EngineSpeed"],
      calculated: [], commanded: ["FuelPumpState", "StarterState", "InjectionEnable", "IgnitionEnable"],
      status: ["EngineState", "StateElapsedTime", "StartPermitted"] },
  };
  const label = key => labels[key] || metadata[key]?.label || key;
  const unit = key => ({ degC: "°C", "deg BTDC": "° BTDC", code: "code" }[metadata[key]?.unit] || metadata[key]?.unit || "");
  function valueText(key, result = simulation.result) {
    const value = key in result.inputs ? result.inputs[key] : result.outputs[key];
    if (key === "EngineState") return `${result.outputs.EngineStateLabel} (${value})`;
    if (metadata[key]?.unit === "state") return value ? "ON / ACTIVE" : "OFF / INACTIVE";
    const places = ["EngineSpeed", "TargetIdleRPM", "RPMError"].includes(key) ? 0
      : ["InjectorPW", "BaseInjectorPW", "LambdaEstimate"].includes(key) ? 4 : 2;
    return `${Number(value).toFixed(places)} ${unit(key)}`;
  }
  let activeView = Object.hasOwn(systems, root.dataset.initialView) ? root.dataset.initialView : "overview";
  let viewAnimation = null;
  let interval = null;
  const inputs = {};

  for (const group of SPEC.ui.inputGroups) {
    const fieldset = make("fieldset", undefined, "engine-input-group");
    fieldset.append(make("legend", group.title));
    for (const name of group.signals) {
      const definition = metadata[name];
      if (["StartRequest", "StopRequest", "EmergencyStop"].includes(name)) continue;
      const wrapper = make("div", undefined, "engine-input");
      wrapper.dataset.inputSearch = `${label(name)} ${definition.label} ${name} ${meanings[name]}`.toLowerCase();
      const help = make("small", meanings[name]);
      help.id = `help-${name}`;
      if (definition.control === "toggle") {
        wrapper.classList.add("form-check", "form-switch");
        const control = make("input");
        control.type = "checkbox"; control.className = "form-check-input"; control.id = `input-${name}`;
        control.setAttribute("aria-describedby", help.id);
        const text = make("label", definition.label, "form-check-label");
        text.htmlFor = control.id;
        control.addEventListener("change", () => { simulation.setInput(name, Number(control.checked)); render(); });
        wrapper.append(control, text, help);
        inputs[name] = { control };
      } else {
        const text = make("label", `${label(name)} (${definition.unit})`, "form-label fw-semibold");
        const number = make("input"); number.type = "number"; number.className = "form-control form-control-sm";
        number.id = `input-${name}`; text.htmlFor = number.id;
        number.min = definition.min; number.max = definition.max;
        number.step = definition.unit === "V" ? "0.01" : "1";
        number.value = definition.default;
        number.setAttribute("aria-describedby", `${help.id} accepted-${name}`);
        number.inputMode = definition.unit === "V" ? "decimal" : "numeric";
        const range = make("input"); range.type = "range"; range.className = "form-range";
        range.min = definition.min; range.max = definition.max; range.step = number.step; range.value = definition.default;
        range.setAttribute("aria-label", `${label(name)} slider`);
        range.setAttribute("aria-describedby", help.id);
        const bounds = make("small", `Allowed: ${definition.min}–${definition.max} ${definition.unit}`);
        const accepted = make("div", "", "engine-accepted");
        accepted.id = `accepted-${name}`; accepted.setAttribute("role", "status");
        const editNumber = () => {
          simulation.setInput(name, number.value === "" ? NaN : Number(number.value));
          render();
        };
        number.addEventListener("input", editNumber);
        number.addEventListener("change", editNumber);
        range.addEventListener("input", () => {
          simulation.setInput(name, Number(range.value)); number.value = range.value; render();
        });
        const adjustment = make("div", undefined, "engine-number-adjustment");
        const step = name === "EngineSpeed" ? 50 : Number(number.step);
        for (const [symbol, direction, verb] of [["−", -1, "Decrease"], ["+", 1, "Increase"]]) {
          const button = make("button", symbol, "btn btn-outline-secondary engine-nudge");
          button.type = "button";
          button.setAttribute("aria-label", `${verb} ${label(name)}`);
          button.title = `${verb} by ${step} ${definition.unit}`;
          button.addEventListener("click", () => {
            const value = simulation.result.inputs[name] + direction * step;
            const bounded = Math.min(definition.max, Math.max(definition.min, value));
            number.value = Number(bounded.toFixed(2));
            simulation.setInput(name, Number(number.value)); render();
          });
          adjustment.append(button);
        }
        adjustment.insertBefore(number, adjustment.lastChild);
        const restore = make("button", `Default: ${definition.default} ${definition.unit}`, "btn btn-sm btn-outline-secondary engine-input-default");
        restore.type = "button";
        restore.setAttribute("aria-label", `Restore ${label(name)} default`);
        restore.addEventListener("click", () => {
          number.value = definition.default;
          simulation.setInput(name, definition.default); render();
        });
        wrapper.append(text, adjustment, range, bounds, restore, help, accepted);
        inputs[name] = { number, range, accepted };
      }
      fieldset.append(wrapper);
    }
    byId("engine-inputs").append(fieldset);
  }
  const filterInputs = () => {
    const query = byId("engine-input-search").value.trim().toLowerCase();
    let visible = 0;
    root.querySelectorAll(".engine-input-group").forEach(group => {
      let groupVisible = 0;
      group.querySelectorAll(".engine-input").forEach(input => {
        input.hidden = !input.dataset.inputSearch.includes(query);
        if (!input.hidden) groupVisible += 1;
      });
      group.hidden = groupVisible === 0; visible += groupVisible;
    });
    byId("engine-input-search-status").textContent = query ? `${visible} matching inputs. Hidden inputs keep their values.` : "All inputs shown.";
  };
  byId("engine-input-search").addEventListener("input", filterInputs);
  byId("engine-input-search-clear").addEventListener("click", () => {
    byId("engine-input-search").value = ""; filterInputs(); byId("engine-input-search").focus();
  });
  for (const [code, stateLabel] of Object.entries(ENGINE_STATE_LABELS)) {
    const item = make("li", stateLabel); item.dataset.state = code;
    byId("engine-stepper").append(item);
  }
  for (const [key, title] of [["overview", "Overview"], ...Object.entries(systems).map(([key, x]) => [key, x.title])]) {
    const button = make("button", title, "btn btn-sm btn-outline-primary");
    button.type = "button"; button.dataset.view = key;
    button.addEventListener("click", () => { activeView = key; renderStructure(); render(); });
    byId("engine-tabs").append(button);
  }
  SPEC.presets.forEach((preset, index) => {
    const option = make("option", preset.name); option.value = index; byId("engine-preset").append(option);
  });

  function startReason() {
    const { inputs: i, outputs: o } = simulation.result;
    if (i.EmergencyStop) return "Emergency stop is latched. All engine and cooling commands are off. Press Reset to release.";
    if (o.EngineState !== 0) return `Sequence active: ${o.EngineStateLabel}. Prime 2.0 s; maximum cranking 5.0 s.`;
    const reasons = [];
    if (!i.IgnitionSwitch) reasons.push("ignition is off");
    if (!i.StartAuthorisation) reasons.push("fingerprint authorisation is not active");
    if (i.BatteryVoltage < 9.5) reasons.push("battery is below 9.5 V");
    if (reasons.length) return `Start blocked because ${reasons.join("; ")}.`;
    return simulation.running ? "Ready for a voice/manual start request." : "Ready. Press Start and Run to advance virtual time.";
  }
  function explanations() {
    const text = describeCurrentRelationship(simulation.result);
    text.startRun = startReason();
    if (simulation.result.inputs.EmergencyStop) text.cooling = "Emergency stop overrides the sensor fail-safe: virtual fan and pump commands are both 0%.";
    if (!simulation.result.outputs.ClosedLoopActive) text.fuel += " Closed-loop correction is inactive; STFT is zero.";
    return text;
  }
  function metric(key, category) {
    const card = make("div", undefined, "engine-metric");
    card.append(make("dt", label(key)));
    const output = make("dd"); output.dataset.signal = key; output.dataset.category = category;
    card.append(output, make("dd", meanings[key], "engine-meaning"));
    return card;
  }
  function renderStructure() {
    viewAnimation?.cancel();
    if (byId("engine-system").animate && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      viewAnimation = byId(activeView === "overview" ? "engine-overview" : "engine-system").animate(
        [{ transform: "translateY(7px)" }, { transform: "translateY(0)" }],
        { duration: 220, easing: "ease-out" },
      );
    }
    byId("engine-overview").hidden = activeView !== "overview";
    byId("engine-system").hidden = activeView === "overview";
    for (const button of byId("engine-tabs").children) {
      const selected = button.dataset.view === activeView;
      button.setAttribute("aria-pressed", String(selected));
      button.classList.toggle("btn-primary", selected);
      button.classList.toggle("btn-outline-primary", !selected);
    }
    if (activeView === "overview") {
      byId("engine-values").replaceChildren();
      const overview = byId("engine-overview"); overview.replaceChildren();
      overview.append(make("p", "Data categories: Measured/status input → ECU-calculated value → Commanded output → Operating status.", "small text-secondary"));
      const grid = make("div", undefined, "engine-overview-grid");
      for (const [key, system] of Object.entries(systems)) {
        const card = make("article", undefined, "content-panel");
        const title = make("h2", system.title, "h5");
        const open = make("button", `Open ${system.title.toLowerCase()}`, "btn btn-sm btn-outline-primary");
        open.type = "button";
        open.addEventListener("click", () => { activeView = key; renderStructure(); render(); });
        const sentence = make("p", "", "small"); sentence.dataset.explanation = key;
        const values = make("dl", undefined, "engine-metrics");
        for (const signal of system.commanded.slice(0, 2)) values.append(metric(signal, "commanded"));
        card.append(title, make("p", system.flow, "engine-flow"), sentence, values, open); grid.append(card);
      }
      overview.append(grid); return;
    }
    byId("engine-overview").replaceChildren();
    const system = systems[activeView];
    byId("engine-system-title").textContent = system.title;
    byId("engine-flow").textContent = system.flow;
    const values = byId("engine-values"); values.replaceChildren();
    for (const category of ["measured", "calculated", "commanded", "status"]) {
      if (!system[category].length) continue;
      values.append(make("h3", categories[category], "engine-category"));
      const list = make("dl", undefined, "engine-metrics");
      for (const key of system[category]) list.append(metric(key, category));
      values.append(list);
    }
  }

  function drawChart() {
    if (activeView === "overview") return;
    const svg = byId("engine-chart"), ns = "http://www.w3.org/2000/svg";
    svg.replaceChildren();
    function add(tag, attrs, text) {
      const node = document.createElementNS(ns, tag);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      if (text !== undefined) node.textContent = text;
      svg.append(node); return node;
    }
    add("title", { id: "engine-chart-title" }, `${systems[activeView].title} signal trends in virtual seconds`);
    const series = SPEC.ui.charts[activeView];
    const data = simulation.history;
    const end = Math.max(60, simulation.internal.simulationTime), begin = end - 60;
    const colors = ["#145ca8", "#8b3a12", "#336b35", "#6b3888", "#374151"];
    const band = 390 / series.length;
    series.forEach((key, index) => {
      const definition = metadata[key];
      const numericRange = definition.range?.match(/^(-?\d+(?:\.\d+)?)\.\.(-?\d+(?:\.\d+)?)$/);
      const minimum = definition.min ?? (numericRange ? Number(numericRange[1]) : key === "IgnitionTiming" ? -5 : 0);
      const maximum = definition.max ?? (numericRange ? Number(numericRange[2]) : key === "IgnitionTiming" ? 45 : 1);
      const top = 30 + band * index, bottom = top + band - 30;
      add("text", { x: 12, y: top - 10 }, `${key === "WaterPumpDuty" ? "Virtual pump duty" : key} (${unit(key)}) · ${minimum}–${maximum}`);
      add("line", { x1: 40, y1: bottom, x2: 620, y2: bottom, stroke: "#dce4ed" });
      const points = data.map(row => {
        const x = 40 + ((row.SimulationTime - begin) / 60) * 580;
        const y = bottom - ((Number(row[key]) - minimum) / (maximum - minimum)) * (bottom - top);
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      }).join(" ");
      const line = add("polyline", { points, fill: "none", stroke: colors[index], "stroke-width": 2 });
      const tooltip = document.createElementNS(ns, "title");
      tooltip.textContent = `${label(key)}: ${valueText(key)}`;
      line.append(tooltip);
    });
    for (let index = 0; index <= 4; index++) add("text", { x: 40 + index * 145, y: 425, "text-anchor": index === 4 ? "end" : "start" }, `${(begin + index * 15).toFixed(1)} s`);
    byId("engine-chart-status").textContent = `${data.length} recorded samples at 0.05 s per calculation. ${data.length ? "History is virtual demonstration data." : "Press Run to record a trend."}`;
  }
  function render() {
    byId("engine-time").textContent = simulation.internal.simulationTime.toFixed(2);
    byId("engine-state-time").textContent = simulation.internal.elapsedInState.toFixed(2);
    byId("engine-state").textContent = simulation.result.outputs.EngineStateLabel;
    byId("engine-mode").textContent = simulation.running ? "Running" : "Paused";
    byId("engine-run").disabled = simulation.running;
    byId("engine-pause").disabled = !simulation.running;
    byId("engine-emergency").setAttribute("aria-pressed", String(Boolean(simulation.result.inputs.EmergencyStop)));
    byId("engine-emergency").disabled = Boolean(simulation.result.inputs.EmergencyStop);
    byId("engine-emergency").textContent = simulation.result.inputs.EmergencyStop ? "Emergency stop · LATCHED" : "Emergency stop";
    byId("engine-start-reason").textContent = startReason();
    for (const item of byId("engine-stepper").children) {
      if (Number(item.dataset.state) === simulation.internal.engineState) item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    }
    for (const [name, control] of Object.entries(inputs)) {
      if (control.control) { control.control.checked = Boolean(simulation.result.inputs[name]); continue; }
      control.range.value = simulation.result.inputs[name];
      const capped = simulation.result.clampedFields[name];
      control.accepted.textContent = capped ? `Input capped / invalid. Accepted: ${valueText(name)}` : `Accepted: ${valueText(name)}`;
      control.number.setAttribute("aria-invalid", String(capped));
    }
    root.querySelectorAll("[data-signal]").forEach(node => { node.textContent = valueText(node.dataset.signal); });
    const sentences = explanations();
    root.querySelectorAll("[data-explanation]").forEach(node => { node.textContent = sentences[node.dataset.explanation]; });
    if (activeView !== "overview") byId("engine-explanation").textContent = sentences[activeView];
    drawChart();
    cutaway?.sync(simulation.result, simulation.running);
  }
  function pause() { clearInterval(interval); interval = null; simulation.running = false; render(); }
  byId("engine-run").addEventListener("click", () => {
    if (interval !== null) return;
    simulation.running = true;
    interval = setInterval(() => {
      for (let i = 0; i < 4; i++) { simulation.step(); cutaway?.advance(simulation.result, STEP); }
      render();
    }, 200);
    render();
  });
  byId("engine-toggle-inputs").addEventListener("click", () => {
    const panel = byId("engine-input-controls");
    panel.hidden = !panel.hidden;
    byId("engine-toggle-inputs").setAttribute("aria-expanded", String(!panel.hidden));
    byId("engine-toggle-inputs").textContent = panel.hidden ? "Show input controls" : "Hide input controls";
  });
  byId("engine-pause").addEventListener("click", pause);
  byId("engine-reset").addEventListener("click", () => {
    pause(); simulation.reset();
    cutaway?.reset();
    for (const [name, control] of Object.entries(inputs)) if (control.number) control.number.value = simulation.rawInputs[name];
    render();
  });
  byId("engine-load-preset").addEventListener("click", () => {
    simulation.loadPreset(Number(byId("engine-preset").value));
    for (const [name, control] of Object.entries(inputs)) if (control.number) control.number.value = simulation.rawInputs[name];
    render();
  });
  byId("engine-start").addEventListener("click", () => { simulation.pulse("StartRequest"); render(); });
  byId("engine-stop").addEventListener("click", () => { simulation.pulse("StopRequest"); render(); });
  byId("engine-emergency").addEventListener("click", () => { simulation.emergencyStop(); render(); });
  byId("engine-export").addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([simulation.csv()], { type: "text/csv;charset=utf-8" }));
    const anchor = make("a"); anchor.href = url; anchor.download = "engine-live-data-virtual.csv";
    document.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  function closeCutaway(message = "3D view closed. Calculations and graphs are unchanged.") {
    cutaway?.dispose(); cutaway = null;
    byId("cutaway-workspace").hidden = true;
    byId("cutaway-stage").hidden = true;
    byId("cutaway-unload").hidden = true;
    byId("cutaway-load").hidden = false;
    byId("cutaway-load").disabled = false;
    byId("cutaway-status").textContent = message;
  }
  async function loadCutaway() {
    if (cutaway || cutawayLoading || pageGone) return;
    cutawayLoading = true; cutawayClosed = false;
    byId("cutaway-load").disabled = true;
    byId("cutaway-status").textContent = "Loading the local 3D renderer…";
    try {
      const { createCutaway } = await import("./cutaway.bundle.mjs");
      if (pageGone) return;
      byId("cutaway-workspace").hidden = false;
      byId("cutaway-stage").hidden = false;
      cutaway = createCutaway(root, simulation.result, () => closeCutaway("3D graphics context was lost. You can retry Load 3D engine; calculations and graphs remain available."));
      cutaway.sync(simulation.result, simulation.running);
      byId("cutaway-load").hidden = true;
      byId("cutaway-unload").hidden = false;
      byId("cutaway-status").textContent = "3D ready · embedded here. Starts paused.";
    } catch {
      closeCutaway("3D is unavailable on this device or could not load. Enable WebGL 2 and retry, or continue using all calculations and graphs below.");
    } finally { cutawayLoading = false; }
  }
  byId("cutaway-load").addEventListener("click", loadCutaway);
  byId("cutaway-unload").addEventListener("click", () => { cutawayClosed = true; closeCutaway(); });
  window.addEventListener("pagehide", () => { pageGone = true; pause(); closeCutaway(); });
  window.addEventListener("pageshow", event => { pageGone = false; if (event.persisted && !cutawayClosed) loadCutaway(); });
  renderStructure(); render();
  loadCutaway();
}
