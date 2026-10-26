import {DEFAULTS, FIELDS, PRESETS, clamp, validate} from "./model.mjs";
import {FuelSimulation} from "./controller.mjs";

const root = document.getElementById("fuel-delivery");
if (root) initialise();
function initialise() {
  const byId = id => document.getElementById(id);
  const make = (tag, text, css) => {
    const e = document.createElement(tag); if (text !== undefined) e.textContent = text;
    if (css) e.className = css; return e;
  };
  const sim = new FuelSimulation(), controls = {}, cells = {};
  let draft = {...DEFAULTS}, valid = true, interval = null, stopped = false;
  const media = matchMedia("(prefers-reduced-motion: reduce)");
  const motion = byId("fuel-motion"); motion.checked = !media.matches;
  const updateMotionPreference = () => { if (media.matches) motion.checked = false; };
  media.addEventListener("change", updateMotionPreference);
  const kpis = [
    ["baseFuelMgPerEvent", "Base fuel mass", "mg/event"], ["finalFuelMgPerEvent", "Final fuel mass", "mg/event"],
    ["injectorPulseWidthMs", "Injector pulse width", "ms"], ["injectorDutyCyclePct", "Injector duty cycle", "%"],
    ["predictedLambda", "Predicted lambda", "ratio"], ["stftPct", "Short-term fuel trim", "%"],
    ["ltftPct", "Long-term fuel trim", "%"], ["fuelFlowGps", "Fuel flow", "g/s"], ["fuelFlowLph", "Fuel flow", "L/h"],
    ["cumulativeFuelG", "Cumulative fuel", "g"], ["brakePowerKw", "Brake power", "kW"],
    ["bsfcGPerKWh", "BSFC", "g/kWh"], ["fuelSavingPct", "Fuel saving", "%"], ["recommendedFuelScale", "Recommended fuel scale", "ratio"],
  ];
  const details = [
    ["injectionEventsPerSecond", "Injection-event rate", "events/s"], ["airMassMgPerEvent", "Air mass", "mg/event"],
    ["targetAfr", "Target air–fuel ratio", "ratio"], ["warmupFactor", "Warm-up factor", "×"],
    ["loadFactor", "Load factor", "×"], ["accelerationFactor", "Acceleration factor", "×"],
    ["baselineCorrectedFuelMgPerEvent", "Corrected baseline fuel", "mg/event"], ["fuelTrimFactor", "Fuel-trim factor", "×"],
    ["commandedFuelMgPerEvent", "Commanded fuel", "mg/event"], ["correctedInjectorFlowMgPerMs", "Corrected injector flow", "mg/ms"],
    ["injectorDeadTimeMs", "Injector dead time", "ms"], ["rawDutyCyclePct", "Requested duty before limiting", "%"],
  ];
  for (const [section, fields] of [["fuel-kpis", kpis], ["fuel-details", details]]) {
    for (const [key, label, unit] of fields) {
      const box = make("div"), dd = make("dd", "—"); dd.dataset.fuelOutput = key;
      box.append(make("dt", `${label} (${unit})`), dd); byId(section).append(box); cells[key] = dd;
    }
  }
  let groupName = "", group;
  for (const f of FIELDS) {
    if (f.group !== groupName) {
      groupName = f.group; group = make("fieldset"); group.append(make("legend", f.group));
      byId("fuel-input-fields").append(group);
    }
    const box = make("div", undefined, "fuel-input"), label = make("label", f.unit ? `${f.label} (${f.unit})` : f.label);
    const input = make("input"), error = make("small", "", "fuel-field-error");
    input.id = `fuel-input-${f.key}`; label.htmlFor = input.id; error.id = `fuel-error-${f.key}`;
    input.setAttribute("aria-describedby", `fuel-help-${f.key} ${error.id}`);
    const help = make("small", typeof f.value === "boolean" ? "Enabled: STFT reacts to measured lambda and LTFT learns." : `Suggested: ${f.min}–${f.max} ${f.unit}. Default: ${f.value}.`); help.id = `fuel-help-${f.key}`;
    if (typeof f.value === "boolean") {
      input.type = "checkbox"; input.checked = f.value; input.className = "form-check-input me-2";
      input.addEventListener("change", () => { draft[f.key] = input.checked; edit(); });
      box.append(input, label, help, error); controls[f.key] = {input};
    } else {
      input.type = "number"; input.value = f.value; input.min = f.min; input.max = f.max; input.step = f.step;
      input.className = "form-control"; input.inputMode = f.step < 1 ? "decimal" : "numeric";
      const row = make("div", undefined, "fuel-number");
      const slider = make("input"); slider.type = "range"; slider.min = f.min; slider.max = f.max;
      slider.step = f.step; slider.value = f.value; slider.className = "form-range";
      slider.setAttribute("aria-label", `${f.label} slider`); slider.setAttribute("aria-describedby", help.id);
      const set = value => { draft[f.key] = value; input.value = value; slider.value = value; edit(); };
      for (const [symbol, verb, direction] of [["−", "Decrease", -1], ["+", "Increase", 1]]) {
        const button = make("button", symbol, "btn btn-outline-secondary"); button.type = "button";
        button.setAttribute("aria-label", `${verb} ${f.label}`);
        button.addEventListener("click", () => set(Number(clamp((Number.isFinite(draft[f.key]) ? draft[f.key] : f.value) + direction * f.step, f.min, f.max).toFixed(4))));
        row.append(button);
      }
      row.insertBefore(input, row.lastChild);
      input.addEventListener("input", () => { draft[f.key] = input.value === "" ? NaN : Number(input.value); slider.value = draft[f.key]; edit(); });
      slider.addEventListener("input", () => set(Number(slider.value)));
      box.append(label, row, slider, help, error); controls[f.key] = {input, slider};
    }
    group.append(box);
  }
  PRESETS.forEach(([name], index) => { const option = make("option", name); option.value = index; byId("fuel-preset").append(option); });
  function syncInputs() {
    for (const f of FIELDS) {
      const c = controls[f.key];
      if (typeof f.value === "boolean") c.input.checked = draft[f.key];
      else { c.input.value = draft[f.key]; c.slider.value = draft[f.key]; }
    }
  }
  function pause() { clearInterval(interval); interval = null; sim.running = false; }
  function edit() {
    pause(); const status = validate(draft); valid = status.valid;
    for (const f of FIELDS) {
      byId(`fuel-error-${f.key}`).textContent = status.errors[f.key] || "";
      controls[f.key].input.setAttribute("aria-invalid", String(Boolean(status.errors[f.key])));
    }
    byId("fuel-validation").hidden = valid;
    byId("fuel-validation").textContent = valid ? "" : "Correct the marked inputs. Calculation, comparison and exports are blocked; displayed readings are from the last valid inputs.";
    if (valid) {
      try { sim.edit(draft); }
      catch (error) { valid = false; byId("fuel-validation").hidden = false; byId("fuel-validation").textContent = error.message; }
    }
    byId("fuel-comparison").hidden = true; render();
  }
  function startClock(resume = false) {
    if (!valid) return;
    pause(); if (resume) sim.resume(); else sim.start();
    if (sim.running) {
      let lastRender = 0;
      interval = setInterval(() => {
        // Exactly one selected engineering step per tick. Wall-clock throttling
        // may slow playback; it never changes solver dt or integrates hidden time.
        sim.tick();
        if (!sim.running) pause();
        if (!sim.running || performance.now() - lastRender >= 100) { render(); lastRender = performance.now(); }
      }, sim.inputs.timeStepS * 1000);
    }
    render();
  }
  byId("fuel-run").addEventListener("click", () => startClock());
  byId("fuel-resume").addEventListener("click", () => startClock(true));
  byId("fuel-pause").addEventListener("click", () => { pause(); render(); });
  byId("fuel-reset").addEventListener("click", () => { pause(); draft = {...DEFAULTS}; sim.reset(); syncInputs(); edit(); });
  byId("fuel-load").addEventListener("click", () => {
    pause(); draft = {...DEFAULTS, ...PRESETS[Number(byId("fuel-preset").value)][1]}; sim.reset(draft); syncInputs(); edit();
  });
  byId("fuel-toggle-inputs").addEventListener("click", () => {
    const fields = byId("fuel-input-fields"); fields.hidden = !fields.hidden;
    byId("fuel-toggle-inputs").setAttribute("aria-expanded", String(!fields.hidden));
    byId("fuel-toggle-inputs").textContent = fields.hidden ? "Show inputs" : "Hide inputs";
  });
  byId("fuel-recommend").addEventListener("click", () => {
    if (!valid) return; draft.fuelOptimisationScale = sim.result.outputs.recommendedFuelScale; syncInputs(); edit();
    byId("fuel-status").textContent = `Recommended scale ${draft.fuelOptimisationScale.toFixed(3)} applied. Review lambda and warnings before running.`;
  });
  function download(data, type, extension) {
    const url = URL.createObjectURL(new Blob([data], {type})), a = make("a");
    a.href = url; a.download = `fuel-delivery-optimisation.${extension}`; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  byId("fuel-json").addEventListener("click", () => { if (valid) download(JSON.stringify({...sim.payload(), history: sim.history, comparison: sim.comparison}, null, 2), "application/json", "json"); });
  byId("fuel-csv").addEventListener("click", () => { if (valid) download(sim.csv(), "text/csv;charset=utf-8", "csv"); });
  const format = (key, value, outputs = sim.result.outputs) => key === "bsfcGPerKWh" && outputs.brakePowerKw < 0.1 ? "Not meaningful at near-zero power" : value.toFixed(3);
  function renderComparison() {
    const box = byId("fuel-comparison"), comparison = sim.compare(); box.replaceChildren(); box.hidden = false;
    box.append(make("h3", "Baseline versus adjusted", "h4"), make("p", comparison.basis, "small text-secondary"));
    const bars = make("div", undefined, "fuel-compare-bars");
    for (const [key, label, unit] of [["cumulativeFuelG", "Cumulative fuel", "g"], ["bsfcGPerKWh", "BSFC", "g/kWh"]]) {
      const max = Math.max(comparison.baseline.outputs[key], comparison.adjusted.outputs[key], 1);
      for (const [name, run] of [["Baseline · scale 1.00", comparison.baseline], ["Adjusted", comparison.adjusted]]) {
        const figure = make("figure"), caption = make("figcaption", `${label} · ${name}: ${format(key, run.outputs[key], run.outputs)} ${unit}`);
        figure.append(caption);
        if (key !== "bsfcGPerKWh" || run.outputs.brakePowerKw >= .1) {
          const bar = make("progress"); bar.max = max; bar.value = run.outputs[key];
          bar.setAttribute("aria-label", `${name} ${label} (${unit})`); figure.append(bar);
        }
        bars.append(figure);
      }
    }
    box.append(bars);
    const scroll = make("div", undefined, "fuel-table-scroll"), table = make("table", undefined, "table table-sm");
    table.append(make("caption", "Fresh runs with current inputs; scale is the only difference."));
    const head = make("thead"), header = make("tr");
    for (const label of ["Result", "Baseline · 1.00", `Adjusted · ${sim.inputs.fuelOptimisationScale.toFixed(3)}`]) { const th = make("th", label); th.scope = "col"; header.append(th); }
    head.append(header); table.append(head); const body = make("tbody");
    for (const [key, label, unit] of kpis.filter(([key]) => !["baseFuelMgPerEvent", "recommendedFuelScale"].includes(key))) {
      const row = make("tr"), labelCell = make("th", `${label} (${unit})`); labelCell.scope = "row"; row.append(labelCell);
      for (const run of [comparison.baseline, comparison.adjusted]) row.append(make("td", format(key, run.outputs[key], run.outputs)));
      body.append(row);
    }
    const warningRow = make("tr"), label = make("th", "Warnings / constraints"); label.scope = "row"; warningRow.append(label);
    for (const run of [comparison.baseline, comparison.adjusted]) warningRow.append(make("td", run.status.warnings.join(" ") || (run.status.optimisationAcceptable ? "Within educational checks" : "Caution: lambda differs from target by more than 0.03.")));
    body.append(warningRow); table.append(body); scroll.append(table); box.append(scroll);
  }
  byId("fuel-compare").addEventListener("click", () => { if (valid) { pause(); renderComparison(); render(); } });
  const chartDefs = [
    ["Lambda", "ratio", [["targetLambda", "Target", true], ["measuredLambda", "Measured", true], ["predictedLambda", "Predicted"]]],
    ["Fuel trims", "%", [["stftPct", "STFT"], ["ltftPct", "LTFT"]]],
    ["Fuel flow", "g/s", [["fuelFlowGps", "Flow"]]],
    ["Cumulative fuel", "g", [["cumulativeFuelG", "Consumed"]]],
    ["Injector pulse width", "ms", [["injectorPulseWidthMs", "Pulse width"]]],
    ["Injector duty cycle", "%", [["injectorDutyCyclePct", "Duty"]]],
  ];
  const ns = "http://www.w3.org/2000/svg", colours = ["#2857b5", "#91411c", "#126445"], charts = [];
  for (const [index, [title, unit, series]] of chartDefs.entries()) {
    const fig = make("figure"), caption = make("figcaption", `${title} (${unit})`), legend = make("p", "", "fuel-legend");
    series.forEach(([, label], j) => legend.append(make("span", `${["Solid", "Dashed", "Dotted"][j]}: ${label}`)));
    const svg = document.createElementNS(ns, "svg"); svg.setAttribute("viewBox", "0 0 500 235"); svg.setAttribute("role", "img"); svg.setAttribute("aria-label", `${title} in ${unit} against virtual time in seconds`); svg.id = `fuel-chart-${index}`;
    fig.append(caption, legend, svg); byId("fuel-charts").append(fig); charts.push({svg, series, unit});
  }
  function drawCharts() {
    const history = sim.history;
    // Uniform display decimation only; full-resolution data remain in CSV/JSON.
    const rows = history.filter((_, index) => index % Math.max(1, Math.ceil(history.length / 180)) === 0);
    if (history.length && rows.at(-1) !== history.at(-1)) rows.push(history.at(-1));
    for (const {svg, series, unit} of charts) {
      svg.replaceChildren();
      const add = (tag, attributes, text) => { const e = document.createElementNS(ns, tag); for (const [k, v] of Object.entries(attributes)) e.setAttribute(k, v); if (text !== undefined) e.textContent = text; svg.append(e); return e; };
      const values = rows.flatMap(row => series.map(([key,, input]) => input ? row.inputs[key] : row.outputs[key]));
      let min = Math.min(...values, 0), max = Math.max(...values, 1); const spread = max - min || 1;
      min -= spread * .05; max += spread * .05;
      const endTime = Math.max(sim.inputs.simulationDurationS, history.at(-1)?.simulationTimeS || 0);
      const x = time => 65 + time / endTime * 415, y = value => 190 - (value - min) / (max - min) * 170;
      for (let tick = 0; tick <= 4; tick++) {
        const value = min + (max - min) * tick / 4, yy = y(value);
        add("line", {x1: 65, x2: 480, y1: yy, y2: yy, stroke: "#e0e6ee"});
        add("text", {x: 59, y: yy + 4, "text-anchor": "end"}, Math.abs(value) >= 10000 ? value.toExponential(1) : value.toFixed(Math.abs(value) < 10 ? 2 : 0));
        add("text", {x: x(endTime * tick / 4), y: 211, "text-anchor": "middle"}, (endTime * tick / 4).toFixed(1));
      }
      add("text", {x: 270, y: 232, "text-anchor": "middle"}, "Virtual time (s)");
      if (!rows.length) add("text", {x: 270, y: 100, "text-anchor": "middle"}, "Run to record time samples");
      series.forEach(([key,, input], index) => {
        add("polyline", {points: rows.map(row => `${x(row.simulationTimeS)},${y(input ? row.inputs[key] : row.outputs[key])}`).join(" "), fill: "none", stroke: colours[index], "stroke-width": 2.5, "stroke-dasharray": ["none", "8 4", "2 4"][index]});
      });
    }
  }
  const descriptions = {
    source: "Fuel density is fixed at 0.745 g/cc. The source is illustrative; fuel supply pressure dynamics are not simulated.",
    rail: "Rail pressure changes corrected injector flow using a square-root relationship. Higher pressure reduces the pulse width needed for the same fuel mass.",
    injector: "Pulse width combines the fuel-open duration and voltage-dependent injector dead time. Duty is limited to 100% for display; saturation triggers a warning.",
    cylinder: "Predicted lambda follows measured lambda divided by trims, scale and injector bias. Cylinder colour indicates mixture relative to target; it is not a combustion or temperature simulation.",
  };
  root.querySelectorAll("[data-component]").forEach(button => button.addEventListener("click", () => {
    root.querySelectorAll("[data-component]").forEach(other => other.setAttribute("aria-pressed", String(other === button)));
    byId("fuel-component-explanation").textContent = descriptions[button.dataset.component];
  }));
  function render() {
    const o = sim.result.outputs;
    if (!sim.comparison) byId("fuel-comparison").hidden = true;
    byId("fuel-time").textContent = sim.state.simulationTimeS.toFixed(2);
    byId("fuel-duration").textContent = sim.inputs.simulationDurationS;
    byId("fuel-mode").textContent = !valid ? "Input error · paused" : sim.running ? "Running" : sim.state.simulationTimeS >= sim.inputs.simulationDurationS - 1e-9 ? "Complete" : "Paused";
    byId("fuel-run").disabled = !valid || sim.running;
    byId("fuel-pause").disabled = !sim.running;
    byId("fuel-resume").disabled = !valid || sim.running || !sim.history.length || sim.state.simulationTimeS >= sim.inputs.simulationDurationS - 1e-9;
    for (const id of ["fuel-recommend", "fuel-compare", "fuel-json"]) byId(id).disabled = !valid;
    byId("fuel-csv").disabled = !valid || !sim.history.length;
    for (const [key, cell] of Object.entries(cells)) cell.textContent = format(key, o[key]);
    byId("fuel-status").textContent = !valid ? "Last valid preview shown; correct input errors to continue." : sim.result.status.optimisationAcceptable ? "Within educational checks · not proof of physical optimality." : "Caution · review operating limits and target mixture.";
    byId("fuel-warnings").replaceChildren(...sim.result.status.warnings.map(w => make("li", w)));
    byId("fuel-record-status").textContent = `${sim.history.length} recorded time samples. Editing preserves prior samples with their original inputs. Exports are local; no assessment is submitted.`;
    const mixture = o.predictedLambda < sim.inputs.targetLambda - .03 ? "rich" : o.predictedLambda > sim.inputs.targetLambda + .03 ? "lean" : "near";
    byId("fuel-mixture").dataset.mixture = mixture; byId("fuel-mixture").textContent = mixture === "near" ? "Near target" : `${mixture === "rich" ? "Rich" : "Lean"} relative to target`;
    const colour = {rich: "#e8ad52", lean: "#70b6ff", near: "#51ba9b"}[mixture];
    byId("fuel-cylinder-fill").setAttribute("fill", colour);
    byId("fuel-flow-path").setAttribute("stroke-width", String(clamp(o.fuelFlowGps * 2 + 2, 2, 14)));
    byId("fuel-spray").setAttribute("fill", colour);
    const width = clamp(o.injectorPulseWidthMs * 2, 8, 45);
    byId("fuel-spray").setAttribute("d", `M470 187 L${470-width} 245 Q470 260 ${470+width} 245Z`);
    byId("fuel-visual-flow").textContent = `${o.fuelFlowGps.toFixed(3)} g/s`;
    byId("fuel-visual-pulse").textContent = `${o.injectorPulseWidthMs.toFixed(3)} ms / injection`;
    byId("fuel-duty").value = o.injectorDutyCyclePct; byId("fuel-duty-text").textContent = o.injectorDutyCyclePct.toFixed(1);
    const fuelMax = Math.max(100, Math.ceil(o.cumulativeFuelG / 100) * 100);
    byId("fuel-used").max = fuelMax; byId("fuel-used").value = o.cumulativeFuelG;
    byId("fuel-used-text").textContent = o.cumulativeFuelG.toFixed(3); byId("fuel-used-max").textContent = fuelMax;
    drawCharts();
  }
  let phase = 0, lastFrame = 0, frame;
  function animate(now) {
    const dt = lastFrame ? Math.min((now-lastFrame)/1000, .05) : 0; lastFrame = now;
    if (sim.running && valid && motion.checked && !document.hidden) {
      phase = (phase + dt * clamp(sim.inputs.engineSpeedRpm / 4000, .2, 1.5)) % 1;
      const opening = (1 - Math.cos(phase * 2 * Math.PI)) / 2;
      byId("fuel-needle").setAttribute("transform", `translate(0 ${-5 * opening})`);
      byId("fuel-spray").setAttribute("opacity", String(.25 + opening * .35));
      byId("fuel-flow-markers").setAttribute("stroke-dashoffset", String(-phase * 30));
    }
    byId("fuel-schematic").dataset.phase = phase.toFixed(4);
    frame = requestAnimationFrame(animate);
  }
  byId("fuel-reset").addEventListener("click", () => {
    phase = 0; byId("fuel-needle").removeAttribute("transform"); byId("fuel-flow-markers").setAttribute("stroke-dashoffset", "0"); byId("fuel-spray").setAttribute("opacity", ".5");
  });
  document.addEventListener("visibilitychange", () => { if (document.hidden && sim.running) { pause(); render(); } });
  window.addEventListener("pagehide", () => { stopped = true; pause(); cancelAnimationFrame(frame); });
  window.addEventListener("pageshow", event => { if (event.persisted && stopped) { stopped = false; render(); lastFrame = 0; frame = requestAnimationFrame(animate); } });
  render(); frame = requestAnimationFrame(animate);
}
