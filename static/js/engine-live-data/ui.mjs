import { EngineSimulation, STEP, PRESETS } from "./controller.mjs";
import { SPEC } from "./spec.mjs";
import { ENGINE_STATE_LABELS, describeCurrentRelationship } from "./model.mjs";
import { createSchematic } from "./schematic.mjs";
import { ectTemperature } from "./reference.mjs";

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
    IgnitionEnable: "Ignition enabled", StartPermitted: "Sequence active", SafeStartCondition: "Safe start condition", ActualRPM: "Imposed actual RPM",
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
    StartAuthorisation: "Simulated permission; no biometric recognition is performed.",
    ACRequest: "Requests at least 35% fan duty when state code is CRANK or higher.",
    StartRequest: "A ten-sample virtual request; it cannot bypass safe-start checks.",
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
    IgnitionTiming: "Commanded degrees BTDC; a negative value represents ATDC.",
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
    SafeStartCondition: "Includes the momentary start request; it normally returns false after the pulse, even during RUN.",
    ActualRPM: "Imposed engine speed input; commands do not automatically change it.",
  };
  const metadata = Object.fromEntries([...SPEC.inputs, ...SPEC.outputs].map(signal => [signal.name, signal]));
  metadata.ActualRPM={name:'ActualRPM',unit:'rpm',min:0,max:6500};
  metadata.SafeStartCondition={name:'SafeStartCondition',unit:'state',min:0,max:1};
  const schematic=createSchematic(byId('engine-schematic'),key=>{
    const {inputs:i,outputs:o}=simulation.result;
    const notes={battery:`Battery ${i.BatteryVoltage.toFixed(2)} V; a start requires at least 9.5 V.`,ecu:`Simulated authorisation ${i.StartAuthorisation?'active':'inactive'}; no biometric capture.`,starter:`Starter ${o.StarterState?'ON':'OFF'} only in CRANK; RPM is imposed independently.`,engine:`Imposed ${i.EngineSpeed.toFixed(0)} rpm; illustrative rotation requires CRANK or RUN and positive RPM.`,fuel:`Fuel pump ${o.FuelPumpState?'ON':'OFF'} in PRIME, CRANK and RUN.`,injector:`Injection ${o.InjectionEnable?'enabled':'disabled'}; pulse ${o.InjectorPW.toFixed(3)} ms.`,fan:`Fan command ${o.FanDuty.toFixed(1)}%; temperature and A/C determine duty, with emergency override.`,pump:`Virtual electric pump command ${o.WaterPumpDuty.toFixed(1)}%; the separate physical 1NZ rig has no electric pump.`};
    byId('engine-component-detail').textContent=notes[key];
  });
  const categories = { measured: "Imposed virtual input", calculated: "ECU-calculated value",
    commanded: "Commanded output", status: "Operating status" };
  const systems = {
    fuel: { title: "Fuel and injection", flow: SPEC.ui.dependencyFlows[0],
      measured: ["O2SensorVoltage", "EngineSpeed", "ManifoldPressure", "ThrottlePosition", "BatteryVoltage"],
      calculated: ["ECT1Temp", "EngineLoad", "LambdaEstimate", "STFT", "WarmupEnrichment", "BatteryCompensation", "BaseInjectorPW"],
      commanded: ["InjectorPW", "InjectionEnable"], status: ["ClosedLoopActive"] },
    idle: { title: "Idle and ignition", flow: SPEC.ui.dependencyFlows[1],
      measured: ["EngineSpeed", "ThrottlePosition", "ManifoldPressure", "AccessoryLoad"],
      calculated: ["ECT1Temp", "ActualRPM", "TargetIdleRPM", "RPMError"],
      commanded: ["IdleControlDuty", "IgnitionTiming"], status: ["IdleActive"] },
    cooling: { title: "Cooling", flow: SPEC.ui.dependencyFlows[2],
      measured: ["ECT1Voltage", "ECT2Voltage", "ACRequest", "BatteryVoltage"],
      calculated: ["ECT1Temp", "ECT2Temp", "SensorDifference", "ControlTemperature"],
      commanded: ["FanDuty", "WaterPumpDuty"], status: ["SensorDisagreement", "CoolingLoopActive"] },
    startRun: { title: "Start and run", flow: SPEC.ui.dependencyFlows[3],
      measured: ["IgnitionSwitch", "StartAuthorisation", "StartRequest", "StopRequest", "EmergencyStop", "BatteryVoltage", "EngineSpeed"],
      calculated: [], commanded: ["FuelPumpState", "StarterState", "InjectionEnable", "IgnitionEnable"],
      status: ["EngineState", "StateElapsedTime", "StartPermitted", "SafeStartCondition"] },
  };
  const label = key => labels[key] || metadata[key]?.label || key;
  const unit = key => ({ degC: "°C", "deg BTDC": "° BTDC", code: "code" }[metadata[key]?.unit] || metadata[key]?.unit || "");
  function valueText(key, result = simulation.result) {
    const value = key in result.inputs ? result.inputs[key] : result.outputs[key];
    if (key === "EngineState") return `${result.outputs.EngineStateLabel} (${value})`;
    if (metadata[key]?.unit === "state") return value ? "ON / ACTIVE" : "OFF / INACTIVE";
    const places = ["EngineSpeed", "ActualRPM", "TargetIdleRPM", "RPMError"].includes(key) ? (Number.isInteger(Number(value)) ? 0 : 1)
      : ["InjectorPW", "BaseInjectorPW", "BatteryCompensation", "LambdaEstimate"].includes(key) ? 3
      : ["ECT1Temp", "ECT2Temp", "SensorDifference", "ControlTemperature", "FanDuty", "WaterPumpDuty", "STFT", "WarmupEnrichment", "EngineLoad", "IdleControlDuty"].includes(key) ? 1 : 2;
    return `${Number(value).toFixed(places)} ${unit(key)}`;
  }
  let activeView = Object.hasOwn(systems, root.dataset.initialView) ? root.dataset.initialView : "overview";
  let viewAnimation = null;
  let interval = null, wallAnchor = 0, accumulator = 0;
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
        const text = make("label", name === "StartAuthorisation" ? "Simulated authorisation" : definition.label, "form-check-label");
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
          const value=number.value.trim()==='' ? NaN : Number(number.value);
          if(!Number.isFinite(value)){inputs[name].error='Enter a finite number; the last accepted value is retained.';render();return;}
          inputs[name].error=''; simulation.setInput(name,value); render();
        };
        number.addEventListener("input", editNumber);
        number.addEventListener("change", editNumber);
        range.addEventListener("input", () => {
          inputs[name].error='';simulation.setInput(name, Number(range.value)); number.value = range.value; render();
        });
        const adjustment = make("div", undefined, "engine-number-adjustment");
        const step = name === "EngineSpeed" ? 50 : Number(number.step);
        for (const [symbol, direction, verb] of [["−", -1, "Decrease"], ["+", 1, "Increase"]]) {
          const button = make("button", symbol, "btn btn-outline-secondary engine-nudge");
          button.type = "button";
          button.setAttribute("aria-label", `${verb} ${label(name)}`);
          button.title = `${verb} by ${step} ${definition.unit}`;
          button.addEventListener("click", () => {
            const value = simulation.rawInputs[name] + direction * step;
            const bounded = Math.min(definition.max, Math.max(definition.min, value));
            number.value = Number(bounded.toFixed(2));
            inputs[name].error='';simulation.setInput(name, Number(number.value)); render();
          });
          adjustment.append(button);
        }
        adjustment.insertBefore(number, adjustment.lastChild);
        const restore = make("button", `Default: ${definition.default} ${definition.unit}`, "btn btn-sm btn-outline-secondary engine-input-default");
        restore.type = "button";
        restore.setAttribute("aria-label", `Restore ${label(name)} default`);
        restore.addEventListener("click", () => {
          number.value = definition.default;
          inputs[name].error='';simulation.setInput(name, definition.default); render();
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
  PRESETS.forEach((preset, index) => {
    const option = make("option", preset.name); option.value = index; byId("engine-preset").append(option);
  });

  function startReason() {
    const { inputs: i, outputs: o } = simulation.result;
    if (i.EmergencyStop) return "Emergency stop is latched. All engine and cooling commands are off. Use Clear emergency or Reset all to release.";
    if (o.EngineState !== 0) return `Sequence active: ${o.EngineStateLabel}. Prime 2.0 s; maximum cranking 5.0 s.`;
    const reasons = [];
    if (!i.IgnitionSwitch) reasons.push("ignition is off");
    if (!i.StartAuthorisation) reasons.push("simulated authorisation is not active");
    if (i.BatteryVoltage < 9.5) reasons.push("battery is below 9.5 V");
    if (reasons.length) return `Start blocked because ${reasons.join("; ")}.`;
    return simulation.running ? "Ready for a simulated start request." : "Ready. Run or resume the simulation before pressing Start engine.";
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
      overview.append(make("p", "Data categories: Imposed virtual input → ECU-calculated value → Commanded output → Operating status.", "small text-secondary"));
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

  const chartGroups={
    fuel:[['O2SensorVoltage'],['LambdaEstimate'],['STFT'],['InjectorPW']],
    idle:[['EngineSpeed','TargetIdleRPM'],['RPMError'],['IdleControlDuty'],['IgnitionTiming']],
    cooling:[['ECT1Temp','ECT2Temp','ControlTemperature'],['FanDuty','WaterPumpDuty'],['SensorDifference']],
    startRun:[['EngineState'],['FuelPumpState','StarterState','InjectionEnable','IgnitionEnable'],['StartPermitted','SafeStartCondition']],
  };
  const selectable=[...new Set([...SPEC.inputs.map(s=>s.name),...SPEC.outputs.map(s=>s.name),'ActualRPM','SafeStartCondition'])];
  for(const key of selectable){const option=make('option',`${label(key)} (${unit(key)})`);option.value=key;byId('engine-chart-extra').append(option);}
  let inspectIndex=null;
  byId('engine-chart-extra').addEventListener('change',drawChart);
  byId('engine-chart-inspect').addEventListener('input',e=>{inspectIndex=Number(e.target.value);drawChart();});
  function drawChart() {
    if (activeView === "overview") return;
    const svg=byId('engine-chart'),ns='http://www.w3.org/2000/svg',data=simulation.history;
    const panels=chartGroups[activeView].map(p=>[...p]),extra=byId('engine-chart-extra').value;
    if(extra)panels.push([extra]);
    const mobile=matchMedia('(max-width:600px)').matches,width=mobile?420:640,left=75,right=width-20;
    const heights=panels.map(keys=>145+keys.length*15),total=heights.reduce((a,b)=>a+b,0);
    svg.replaceChildren();svg.setAttribute('viewBox',`0 0 ${width} ${total+35}`);
    const add=(tag,attrs,text)=>{const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;svg.append(e);return e;};
    add('title',{id:'engine-chart-title'},`${systems[activeView].title}: model history, simulation time in seconds`);
    const last=data.at(-1)?.SimulationTime??0,begin=Math.max(0,last-60),end=Math.max(begin+STEP,last),colors=['#145ca8','#a34b22','#087e74','#7b3696'];
    const chosen=Math.max(0,Math.min(data.length-1,inspectIndex??data.length-1));
    const row=data[chosen],slider=byId('engine-chart-inspect');slider.disabled=!data.length;slider.max=Math.max(0,data.length-1);slider.value=chosen;
    const readings=[];
    let top=15;panels.forEach((keys,index)=>{
      const plotTop=top+35+keys.length*15,bottom=plotTop+65;
      const vals=data.flatMap(r=>keys.map(k=>Number(r[k]))).filter(Number.isFinite);
      let minimum=Math.min(0,...vals),maximum=Math.max(1,...vals);
      if(keys.includes('SensorDifference'))maximum=Math.max(maximum,15);
      const padding=(maximum-minimum)*.08;minimum-=padding;maximum+=padding;
      const x=t=>left+(t-begin)/(end-begin)*(right-left),y=v=>bottom-(v-minimum)/(maximum-minimum)*(bottom-plotTop);
      add('text',{x:5,y:top+13,'font-weight':'bold'},`${label(keys[0])}${keys.length>1?` + ${keys.length-1} signal${keys.length>2?'s':''}`:''} (${unit(keys[0])})`);
      keys.forEach((key,i)=>{const legend=add('text',{x:8,y:top+30+i*15},`${i===0?'Solid':i===1?'Dashed':i===2?'Dotted':'Dash-dot'}: ${label(key)}`);legend.style.fill=colors[i%colors.length];});
      for(let n=0;n<=2;n++){const v=minimum+(maximum-minimum)*n/2;add('line',{x1:left,x2:right,y1:y(v),y2:y(v),stroke:'#dce4ed'});add('text',{x:left-5,y:y(v)+4,'text-anchor':'end'},v.toFixed(Math.abs(v)<10?1:0));}
      if(keys.includes('SensorDifference')){add('line',{x1:left,x2:right,y1:y(15),y2:y(15),stroke:'#a43838','stroke-dasharray':'4 4'});add('text',{x:right-10,y:y(15)-4,'text-anchor':'end'},'15 °C threshold');}
      keys.forEach((key,i)=>{
        const discrete=['EngineState','FuelPumpState','StarterState','InjectionEnable','IgnitionEnable','StartPermitted','SafeStartCondition','ClosedLoopActive','IdleActive','CoolingLoopActive','SensorDisagreement'].includes(key);
        let d='';data.forEach((r,j)=>{const xx=x(r.SimulationTime),yy=y(Number(r[key]));d+=j===0?`M${xx} ${yy}`:discrete?` H${xx} V${yy}`:` L${xx} ${yy}`;});
        const path=add('path',{d,fill:'none',stroke:colors[i%colors.length],'stroke-width':2,'stroke-dasharray':i===1?'7 4':i===2?'2 4':i===3?'7 3 2 3':'none'});
        if(data.length===1)add('circle',{cx:x(data[0].SimulationTime),cy:y(Number(data[0][key])),r:3,fill:colors[i%colors.length]});
        const title=document.createElementNS(ns,'title');title.textContent=row?`${row.SimulationTime.toFixed(2)} s · ${label(key)} ${Number(row[key]).toFixed(3)} ${unit(key)}`:`${label(key)} — no samples`;path.append(title);
        if(row)readings.push(`${label(key)} ${Number(row[key]).toFixed(3)} ${unit(key)}`);
      });
      if(row)add('line',{x1:x(row.SimulationTime),x2:x(row.SimulationTime),y1:plotTop,y2:bottom,stroke:'#667789','stroke-dasharray':'3 3'});
      add('text',{x:left,y:bottom+17},`${begin.toFixed(1)} s`);add('text',{x:right,y:bottom+17,'text-anchor':'end'},`${end.toFixed(1)} s`);top+=heights[index];
    });
    add('text',{x:width/2,y:total+25,'text-anchor':'middle'},'Simulation time (s)');
    byId('engine-chart-readout').textContent=row?`${row.SimulationTime.toFixed(2)} s · ${readings.join(' · ')}`:'No samples recorded.';
    byId('engine-chart-status').textContent=`${data.length} recorded samples at 0.05 s. ${data.length?'Use the sample slider for keyboard access; CSV includes the retained history.':'Run or Step to record a trend.'} State codes: 0 OFF, 1 PRIME, 2 CRANK, 3 RUN, 4 SHUTDOWN; binary signals: 0 OFF, 1 ON.`;
  }
  window.addEventListener('resize',drawChart);
  byId('engine-chart').addEventListener('pointermove',event=>{if(!simulation.history.length)return;const bounds=event.currentTarget.getBoundingClientRect(),viewWidth=matchMedia('(max-width:600px)').matches?420:640,fraction=Math.max(0,Math.min(1,((event.clientX-bounds.left)/bounds.width*viewWidth-75)/(viewWidth-95)));inspectIndex=Math.round(fraction*(simulation.history.length-1));drawChart();});
  function render() {
    byId("engine-time").textContent = simulation.internal.simulationTime.toFixed(2);
    byId("engine-state-time").textContent = simulation.internal.elapsedInState.toFixed(2);
    byId("engine-state").textContent = simulation.result.outputs.EngineStateLabel;
    byId("engine-mode").textContent = simulation.running ? "Running" : simulation.history.length ? "Paused" : "Ready — simulation paused";
    byId("engine-run").textContent=simulation.history.length?"Resume":"Run simulation";
    byId("engine-step").disabled=simulation.running;
    byId("engine-start").disabled=!simulation.running || simulation.internal.engineState!==0;
    byId("engine-stop").disabled=!simulation.running;
    byId("engine-export").disabled=!simulation.history.length;
    const pending=Object.keys(simulation.rawInputs).some(k=>simulation.rawInputs[k]!==simulation.result.inputs[k]);
    byId("engine-pending").textContent=pending?"Inputs changed: pending until Step or the next running sample. Readouts show the last sampled values.":simulation.history.length?"Readings, graphics and history show the same recorded sample.":"No samples yet. CSV becomes available after the first step.";
    byId("engine-clear-emergency").disabled=!simulation.rawInputs.EmergencyStop;
    byId("engine-events").replaceChildren(...(simulation.events.length?simulation.events.slice(-20).map(e=>make("li",`${e.time.toFixed(2)} s · ${e.message}`)):[make("li","No state changes recorded yet.")]));
    schematic.update(simulation.result,simulation.running);
    byId("engine-run").disabled = simulation.running;
    byId("engine-pause").disabled = !simulation.running;
    byId("engine-emergency").setAttribute("aria-pressed", String(Boolean(simulation.rawInputs.EmergencyStop)));
    byId("engine-emergency").disabled = Boolean(simulation.rawInputs.EmergencyStop);
    byId("engine-emergency").textContent = simulation.rawInputs.EmergencyStop ? "Emergency stop · LATCHED" : "Emergency stop";
    byId("engine-start-reason").textContent = startReason();
    for (const item of byId("engine-stepper").children) {
      if (Number(item.dataset.state) === simulation.internal.engineState) item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    }
    for (const [name, control] of Object.entries(inputs)) {
      if (control.control) { control.control.checked = Boolean(simulation.rawInputs[name]); continue; }
      control.range.value = simulation.rawInputs[name];
      const capped = simulation.clampedFields[name];
      const raw=simulation.rawInputs[name];
      const ect=['ECT1Voltage','ECT2Voltage'].includes(name)?` · input preview ${ectTemperature(raw).toFixed(1)} °C`:'';
      const accepted=`${Number(raw).toFixed(unit(name)==='V'?2:1)} ${unit(name)}${ect}`;
      control.accepted.textContent=control.error || (capped?`Input capped. Accepted: ${accepted}`:`Accepted: ${accepted}`) + (simulation.rawInputs[name]!==simulation.result.inputs[name]?' · pending next sample':'');
      control.number.setAttribute("aria-invalid", String(Boolean(control.error)));
    }
    root.querySelectorAll("[data-signal]").forEach(node => { node.textContent = valueText(node.dataset.signal); });
    const sentences = explanations();
    root.querySelectorAll("[data-explanation]").forEach(node => { node.textContent = sentences[node.dataset.explanation]; });
    if (activeView !== "overview") byId("engine-explanation").textContent = sentences[activeView];
    drawChart();
    cutaway?.sync(simulation.result, simulation.running);
  }
  function pause(reason) { clearInterval(interval); interval=null; simulation.running=false; wallAnchor=0;accumulator=0;render();if(reason)byId('engine-pending').textContent=reason; }
  function advanceOne(){simulation.step();cutaway?.advance(simulation.result,STEP);}
  byId("engine-run").addEventListener("click", () => {
    if(interval!==null)return;
    simulation.running=true; wallAnchor=performance.now(); accumulator=0;
    interval=setInterval(()=>{
      const now=performance.now(),delta=(now-wallAnchor)/1000;wallAnchor=now;
      if(document.hidden){pause('Paused because this tab is hidden. Resume deliberately.');return;}
      if(delta>.5){pause('Paused after a long browser delay. Resume deliberately to continue without skipping history.');return;}
      accumulator+=delta;let steps=0;
      while(accumulator>=STEP && steps<10){advanceOne();accumulator-=STEP;steps++;}
      if(steps){inspectIndex=null;render();}
    },50);render();
  });
  byId('engine-step').addEventListener('click',()=>{if(!simulation.running){advanceOne();render();}});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&simulation.running)pause('Paused because this tab is hidden. Resume deliberately.');});
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
    for (const [name, control] of Object.entries(inputs)) if (control.number) {control.number.value = simulation.rawInputs[name];control.error='';}
    render();
  });
  byId("engine-load-preset").addEventListener("click", () => {
    pause();simulation.loadPreset(Number(byId("engine-preset").value));cutaway?.reset();
    for (const [name, control] of Object.entries(inputs)) if (control.number) {control.number.value = simulation.rawInputs[name];control.error='';}
    render();
  });
  byId("engine-start").addEventListener("click", () => { simulation.pulse("StartRequest"); render(); });
  byId("engine-stop").addEventListener("click", () => { simulation.pulse("StopRequest"); render(); });
  byId("engine-emergency").addEventListener("click", () => { simulation.emergencyStop(); render(); });
  byId("engine-clear-emergency").addEventListener("click",()=>{simulation.clearEmergency();render();});
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
