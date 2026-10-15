(() => {
  "use strict";

  const ENGINE_STATES = Object.freeze({ OFF: 0, PRIME: 1, CRANK: 2, RUN: 3, SHUTDOWN: 4 });
  const STATE_LABELS = ["OFF", "PRIME", "CRANK", "RUN", "SHUTDOWN"];

  const numericDefinitions = [
    { name: "BatteryVoltage", label: "Battery voltage", unit: "V", min: 8.0, max: 14.9, default: 13.8, step: 0.1, group: "Power and engine signals", help: "Used for start permission and injector battery compensation." },
    { name: "EngineSpeed", label: "Engine speed", unit: "rpm", min: 0, max: 6500, default: 800, step: 10, group: "Power and engine signals", help: "Used for start confirmation, fuel quantity, idle error and ignition timing." },
    { name: "ThrottlePosition", label: "Throttle position", unit: "%", min: 0, max: 100, default: 2, step: 1, group: "Power and engine signals", help: "Contributes to engine load and determines whether idle control is active." },
    { name: "ManifoldPressure", label: "Manifold pressure", unit: "kPa", min: 20, max: 105, default: 35, step: 1, group: "Power and engine signals", help: "Contributes to engine load, injector pulse width and ignition timing." },
    { name: "AccessoryLoad", label: "Accessory/electrical load", unit: "%", min: 0, max: 100, default: 10, step: 1, group: "Power and engine signals", help: "Increases the idle-control demand." },
    { name: "O2SensorVoltage", label: "Oxygen-sensor voltage", unit: "V", min: 0.05, max: 0.95, default: 0.45, step: 0.01, group: "Fuel feedback", help: "Produces the simplified lambda estimate and STFT direction." },
    { name: "ECT1Voltage", label: "ECT1 sensor voltage", unit: "V", min: 0.2, max: 4.8, default: 1.0, step: 0.01, group: "Cooling sensors", help: "Converted to ECT1 temperature for fuel, idle and cooling logic." },
    { name: "ECT2Voltage", label: "ECT2 sensor voltage", unit: "V", min: 0.2, max: 4.8, default: 1.1, step: 0.01, group: "Cooling sensors", help: "Converted to ECT2 temperature for cooling control and plausibility." },
  ];

  const defaultInputs = Object.freeze({
    BatteryVoltage: 13.8,
    EngineSpeed: 800,
    ThrottlePosition: 2,
    ManifoldPressure: 35,
    O2SensorVoltage: 0.45,
    ECT1Voltage: 1.0,
    ECT2Voltage: 1.1,
    AccessoryLoad: 10,
    IgnitionSwitch: 0,
    StartAuthorisation: 0,
    StartRequest: 0,
    StopRequest: 0,
    EmergencyStop: 0,
    ACRequest: 0,
  });

  const presets = {
    warmIdle: {
      BatteryVoltage: 13.8, EngineSpeed: 800, ThrottlePosition: 2,
      ManifoldPressure: 35, O2SensorVoltage: 0.45, ECT1Voltage: 1.0,
      ECT2Voltage: 1.1, AccessoryLoad: 10, ACRequest: 0,
    },
    leanO2: {
      BatteryVoltage: 13.8, EngineSpeed: 800, ThrottlePosition: 2,
      ManifoldPressure: 35, O2SensorVoltage: 0.10, ECT1Voltage: 1.0,
      ECT2Voltage: 1.1, AccessoryLoad: 10, ACRequest: 0,
    },
    highCooling: {
      BatteryVoltage: 13.8, EngineSpeed: 900, ThrottlePosition: 3,
      ManifoldPressure: 38, O2SensorVoltage: 0.45, ECT1Voltage: 0.55,
      ECT2Voltage: 0.62, AccessoryLoad: 20, ACRequest: 1,
    },
    idleLoad: {
      BatteryVoltage: 13.0, EngineSpeed: 620, ThrottlePosition: 2,
      ManifoldPressure: 45, O2SensorVoltage: 0.45, ECT1Voltage: 1.0,
      ECT2Voltage: 1.1, AccessoryLoad: 80, ACRequest: 1,
    },
    ectDisagreement: {
      BatteryVoltage: 13.8, EngineSpeed: 800, ThrottlePosition: 2,
      ManifoldPressure: 35, O2SensorVoltage: 0.45, ECT1Voltage: 1.0,
      ECT2Voltage: 2.0, AccessoryLoad: 10, ACRequest: 0,
    },
  };

  let inputs = { ...defaultInputs };
  let internal = { engineState: ENGINE_STATES.OFF, elapsedInState: 0, simulationTime: 0 };
  let running = false;
  let currentResult = null;
  let history = [];
  let historyAccumulator = 0;
  let loopHandle = null;

  const clamp = (value, min, max) => {
    const numeric = Number(value);
    const safe = Number.isFinite(numeric) ? numeric : min;
    return Math.min(Math.max(safe, min), max);
  };

  function sanitizeInputs(raw) {
    const accepted = { ...raw };
    for (const definition of numericDefinitions) {
      accepted[definition.name] = clamp(raw[definition.name], definition.min, definition.max);
    }
    for (const key of ["IgnitionSwitch", "StartAuthorisation", "StartRequest", "StopRequest", "EmergencyStop", "ACRequest"]) {
      accepted[key] = clamp(raw[key], 0, 1);
    }
    return accepted;
  }

  function ectVoltageToTemperature(voltage) {
    const v = clamp(voltage, 0.2, 4.8);
    let temperature;
    if (v >= 4.3) temperature = -20 + (4.8 - v) * 40;
    else if (v >= 3.5) temperature = (4.3 - v) * 31.25;
    else if (v >= 2.5) temperature = 25 + (3.5 - v) * 25;
    else if (v >= 1.5) temperature = 50 + (2.5 - v) * 25;
    else if (v >= 1.0) temperature = 75 + (1.5 - v) * 30;
    else if (v >= 0.6) temperature = 90 + (1.0 - v) * 37.5;
    else if (v >= 0.3) temperature = 105 + (0.6 - v) * (20 / 0.3);
    else temperature = 125 + (0.3 - v) * 100;
    return clamp(temperature, -20, 135);
  }

  function startRunOutputsForState(accepted, state) {
    const engineState = state.engineState;
    const safeStart =
      accepted.IgnitionSwitch > 0.5 &&
      accepted.StartAuthorisation > 0.5 &&
      accepted.StartRequest > 0.5 &&
      accepted.EmergencyStop < 0.5 &&
      accepted.BatteryVoltage >= 9.5;

    return {
      EngineState: engineState,
      EngineStateLabel: STATE_LABELS[engineState],
      StateElapsedTime: state.elapsedInState,
      SafeStartCondition: Number(safeStart),
      FuelPumpState: Number([ENGINE_STATES.PRIME, ENGINE_STATES.CRANK, ENGINE_STATES.RUN].includes(engineState)),
      StarterState: Number(engineState === ENGINE_STATES.CRANK),
      InjectionEnable: Number([ENGINE_STATES.CRANK, ENGINE_STATES.RUN].includes(engineState)),
      IgnitionEnable: Number([ENGINE_STATES.CRANK, ENGINE_STATES.RUN].includes(engineState)),
      StartPermitted: Number([ENGINE_STATES.PRIME, ENGINE_STATES.CRANK, ENGINE_STATES.RUN].includes(engineState)),
    };
  }

  function advanceStartRunState(accepted, previous, dt) {
    let engineState = previous.engineState;
    let elapsedInState = previous.elapsedInState + dt;
    const simulationTime = previous.simulationTime + dt;
    const ignitionOn = accepted.IgnitionSwitch > 0.5;
    const authorised = accepted.StartAuthorisation > 0.5;
    const startRequested = accepted.StartRequest > 0.5;
    const stopRequested = accepted.StopRequest > 0.5;
    const emergency = accepted.EmergencyStop > 0.5;
    const safeStart = ignitionOn && authorised && startRequested && !emergency && accepted.BatteryVoltage >= 9.5;

    const transition = (next) => {
      engineState = next;
      elapsedInState = 0;
    };

    switch (engineState) {
      case ENGINE_STATES.OFF:
        if (safeStart) transition(ENGINE_STATES.PRIME);
        break;
      case ENGINE_STATES.PRIME:
        if (emergency || stopRequested || !ignitionOn) transition(ENGINE_STATES.SHUTDOWN);
        else if (elapsedInState >= 2.0) transition(ENGINE_STATES.CRANK);
        break;
      case ENGINE_STATES.CRANK:
        if (emergency || stopRequested || !ignitionOn || accepted.BatteryVoltage < 8.5) transition(ENGINE_STATES.SHUTDOWN);
        else if (accepted.EngineSpeed >= 500) transition(ENGINE_STATES.RUN);
        else if (elapsedInState >= 5.0) transition(ENGINE_STATES.SHUTDOWN);
        break;
      case ENGINE_STATES.RUN:
        if (emergency || stopRequested || !ignitionOn) transition(ENGINE_STATES.SHUTDOWN);
        break;
      case ENGINE_STATES.SHUTDOWN:
      default:
        if (elapsedInState >= 0.5) transition(ENGINE_STATES.OFF);
        break;
    }

    return { engineState, elapsedInState, simulationTime };
  }

  function calculateFuel(accepted, ect1Temp, start) {
    const rpm = clamp(accepted.EngineSpeed, 0, 6500);
    const map = clamp(accepted.ManifoldPressure, 20, 105);
    const tps = clamp(accepted.ThrottlePosition, 0, 100);
    const o2 = clamp(accepted.O2SensorVoltage, 0.05, 0.95);
    const battery = clamp(accepted.BatteryVoltage, 8.0, 14.9);
    const EngineLoad = clamp(0.55 * ((map - 20) / 85) * 100 + 0.45 * tps, 0, 100);
    const LambdaEstimate = clamp(1.0 + (0.45 - o2) * 0.35, 0.75, 1.25);
    const ClosedLoopActive = Number(start.InjectionEnable > 0.5 && ect1Temp >= 70 && rpm >= 600);
    const STFT = ClosedLoopActive ? clamp((LambdaEstimate - 1.0) * 120, -25, 25) : 0;
    const WarmupEnrichment = clamp((70 - ect1Temp) * 0.5, 0, 40);
    const BatteryCompensation = clamp((13.8 - battery) * 0.18, 0, 1.2);
    const BaseInjectorPW = clamp(1.0 + 0.00035 * rpm + 0.025 * (map - 20) + 0.012 * tps, 1.0, 15.0);
    const InjectorPW = start.InjectionEnable
      ? clamp((BaseInjectorPW + BatteryCompensation) * (1 + (STFT + WarmupEnrichment) / 100), 0, 20)
      : 0;
    return { EngineLoad, LambdaEstimate, STFT, WarmupEnrichment, BatteryCompensation, BaseInjectorPW, InjectorPW, ClosedLoopActive };
  }

  function calculateIdleIgnition(accepted, ect1Temp, start) {
    const rpm = clamp(accepted.EngineSpeed, 0, 6500);
    const tps = clamp(accepted.ThrottlePosition, 0, 100);
    const map = clamp(accepted.ManifoldPressure, 20, 105);
    const load = clamp(accepted.AccessoryLoad, 0, 100);
    const TargetIdleRPM = 750 + clamp((80 - ect1Temp) * 5.625, 0, 450);
    const IdleActive = Number(start.EngineState === ENGINE_STATES.RUN && tps <= 5 && rpm < 2000);
    const RPMError = IdleActive ? TargetIdleRPM - rpm : 0;
    const IdleControlDuty = IdleActive ? clamp(25 + 0.06 * RPMError + 0.25 * load, 0, 100) : 0;
    let IgnitionTiming;
    if (start.IgnitionEnable <= 0.5) IgnitionTiming = 0;
    else if (start.EngineState === ENGINE_STATES.CRANK) IgnitionTiming = 5;
    else IgnitionTiming = clamp(10 + 0.004 * (rpm - 800) - 0.08 * (map - 35) + 0.015 * RPMError, -5, 45);
    return { TargetIdleRPM, RPMError, IdleControlDuty, IgnitionTiming, IdleActive };
  }

  function calculateCooling(accepted, start) {
    const ECT1Temp = ectVoltageToTemperature(accepted.ECT1Voltage);
    const ECT2Temp = ectVoltageToTemperature(accepted.ECT2Voltage);
    const SensorDifference = Math.abs(ECT1Temp - ECT2Temp);
    const SensorDisagreement = Number(SensorDifference > 15);
    const ControlTemperature = Math.max(ECT1Temp, ECT2Temp);
    let FanDuty = 0;
    let WaterPumpDuty = 0;

    if (accepted.EmergencyStop > 0.5 || accepted.BatteryVoltage < 8.0) {
      FanDuty = 0;
      WaterPumpDuty = 0;
    } else if (SensorDisagreement > 0.5) {
      FanDuty = 100;
      WaterPumpDuty = 100;
    } else {
      if (ControlTemperature < 88) FanDuty = 0;
      else if (ControlTemperature < 95) FanDuty = 20 + (ControlTemperature - 88) * (30 / 7);
      else if (ControlTemperature < 105) FanDuty = 50 + (ControlTemperature - 95) * 5;
      else FanDuty = 100;

      if (accepted.ACRequest > 0.5 && start.EngineState >= ENGINE_STATES.CRANK) FanDuty = Math.max(FanDuty, 35);

      if (start.EngineState === ENGINE_STATES.RUN) {
        if (ControlTemperature < 50) WaterPumpDuty = 35;
        else if (ControlTemperature < 90) WaterPumpDuty = 35 + (ControlTemperature - 50) * (35 / 40);
        else if (ControlTemperature < 110) WaterPumpDuty = 70 + (ControlTemperature - 90) * 1.5;
        else WaterPumpDuty = 100;
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

  function calculateSnapshot(advance, dt = 0.05) {
    const accepted = sanitizeInputs(inputs);
    if (advance) internal = advanceStartRunState(accepted, internal, dt);
    const start = startRunOutputsForState(accepted, internal);
    const cooling = calculateCooling(accepted, start);
    const fuel = calculateFuel(accepted, cooling.ECT1Temp, start);
    const idle = calculateIdleIgnition(accepted, cooling.ECT1Temp, start);
    currentResult = { inputs: accepted, outputs: { ...start, ...fuel, ...idle, ...cooling }, internal: { ...internal } };
    return currentResult;
  }

  function buildNumericControls() {
    const host = document.getElementById("numericInputs");
    host.innerHTML = "";
    let activeGroup = "";

    for (const definition of numericDefinitions) {
      if (definition.group !== activeGroup) {
        activeGroup = definition.group;
        const section = document.createElement("section");
        section.className = "control-group";
        section.dataset.group = activeGroup;
        const heading = document.createElement("h3");
        heading.textContent = activeGroup;
        section.appendChild(heading);
        host.appendChild(section);
      }

      const section = host.lastElementChild;
      const wrapper = document.createElement("div");
      wrapper.className = "input-control";
      wrapper.title = definition.help;
      wrapper.innerHTML = `
        <div class="input-control-header">
          <label for="${definition.name}Number">${definition.label}</label>
          <span class="input-range-text">${definition.min}–${definition.max} ${definition.unit}</span>
        </div>
        <div class="slider-number-row">
          <input id="${definition.name}Range" type="range" min="${definition.min}" max="${definition.max}" step="${definition.step}" value="${definition.default}" />
          <input id="${definition.name}Number" type="number" min="${definition.min}" max="${definition.max}" step="${definition.step}" value="${definition.default}" aria-label="${definition.label} in ${definition.unit}" />
        </div>
        <p id="${definition.name}Note" class="input-note">Accepted: ${definition.default} ${definition.unit}</p>
      `;
      section.appendChild(wrapper);

      const range = wrapper.querySelector(`#${definition.name}Range`);
      const number = wrapper.querySelector(`#${definition.name}Number`);
      range.addEventListener("input", () => {
        setNumericInput(definition, Number(range.value), false);
      });
      number.addEventListener("change", () => {
        setNumericInput(definition, Number(number.value), true);
      });
    }
  }

  function setNumericInput(definition, rawValue, showCapMessage) {
    const accepted = clamp(rawValue, definition.min, definition.max);
    inputs[definition.name] = accepted;
    const range = document.getElementById(`${definition.name}Range`);
    const number = document.getElementById(`${definition.name}Number`);
    const note = document.getElementById(`${definition.name}Note`);
    range.value = accepted;
    number.value = accepted;
    const wasCapped = Number(rawValue) !== accepted;
    note.textContent = wasCapped && showCapMessage
      ? `Input capped to ${formatNumber(accepted, definition.step)} ${definition.unit}`
      : `Accepted: ${formatNumber(accepted, definition.step)} ${definition.unit}`;
    note.classList.toggle("capped", wasCapped && showCapMessage);
    calculateSnapshot(false);
    render();
  }

  function syncAllInputControls() {
    for (const definition of numericDefinitions) {
      const range = document.getElementById(`${definition.name}Range`);
      const number = document.getElementById(`${definition.name}Number`);
      const note = document.getElementById(`${definition.name}Note`);
      if (!range || !number || !note) continue;
      range.value = inputs[definition.name];
      number.value = inputs[definition.name];
      note.textContent = `Accepted: ${formatNumber(inputs[definition.name], definition.step)} ${definition.unit}`;
      note.classList.remove("capped");
    }
    for (const key of ["IgnitionSwitch", "StartAuthorisation", "ACRequest"]) {
      const element = document.getElementById(key);
      if (element) element.checked = inputs[key] > 0.5;
    }
  }

  function formatNumber(value, step = 0.01) {
    const decimals = step >= 1 ? 0 : step >= 0.1 ? 1 : 2;
    return Number(value).toFixed(decimals);
  }

  function formatValue(value, unit = "", decimals = 2) {
    if (typeof value === "string") return value;
    return `${Number(value).toFixed(decimals)}${unit ? ` ${unit}` : ""}`;
  }

  function pulseInput(name, durationMs = 500) {
    inputs[name] = 1;
    calculateSnapshot(false);
    render();
    window.setTimeout(() => {
      inputs[name] = 0;
      calculateSnapshot(false);
      render();
    }, durationMs);
  }

  function tick() {
    if (!running) return;
    calculateSnapshot(true, 0.05);
    historyAccumulator += 0.05;
    if (historyAccumulator >= 0.2 - 1e-9) {
      historyAccumulator = 0;
      appendHistory();
    }
    render();
  }

  function appendHistory() {
    if (!currentResult) return;
    const row = {
      time: currentResult.internal.simulationTime,
      ...currentResult.inputs,
      ...currentResult.outputs,
    };
    history.push(row);
    const maximumRows = Math.ceil(60 / 0.2);
    if (history.length > maximumRows) history.splice(0, history.length - maximumRows);
  }

  function setRunning(next) {
    running = next;
    if (running && !loopHandle) loopHandle = window.setInterval(tick, 50);
    render();
  }

  function resetSimulation() {
    running = false;
    inputs = { ...defaultInputs };
    internal = { engineState: ENGINE_STATES.OFF, elapsedInState: 0, simulationTime: 0 };
    history = [];
    historyAccumulator = 0;
    syncAllInputControls();
    calculateSnapshot(false);
    render();
  }

  function forceStateEvaluation() {
    const accepted = sanitizeInputs(inputs);
    internal = advanceStartRunState(accepted, internal, 0);
    calculateSnapshot(false);
    render();
  }

  function render() {
    if (!currentResult) calculateSnapshot(false);
    const { inputs: accepted, outputs, internal: state } = currentResult;

    document.getElementById("runStatus").textContent = running ? "RUNNING" : "PAUSED";
    document.getElementById("simulationTime").textContent = `${state.simulationTime.toFixed(2)} s`;
    document.getElementById("engineStateHeader").textContent = outputs.EngineStateLabel;
    document.getElementById("stateTimeHeader").textContent = `${state.elapsedInState.toFixed(2)} s`;

    document.getElementById("IgnitionSwitchState").textContent = accepted.IgnitionSwitch ? "ON" : "OFF";
    document.getElementById("StartAuthorisationState").textContent = accepted.StartAuthorisation ? "YES" : "NO";
    document.getElementById("ACRequestState").textContent = accepted.ACRequest ? "ON" : "OFF";

    const emergencyButton = document.getElementById("emergencyButton");
    emergencyButton.classList.toggle("active-danger", accepted.EmergencyStop > 0.5);
    emergencyButton.textContent = accepted.EmergencyStop ? "E-stop ACTIVE" : "Emergency stop";

    document.getElementById("startBlockReason").textContent = startConditionMessage(accepted, outputs);

    renderOverview(accepted, outputs);
    renderFuel(accepted, outputs);
    renderIdle(accepted, outputs);
    renderCooling(accepted, outputs);
    renderStartRun(accepted, outputs);
    drawChart();
  }

  function startConditionMessage(accepted, outputs) {
    if (accepted.EmergencyStop) return "Start blocked: reset the emergency stop.";
    if (!accepted.IgnitionSwitch) return "Start blocked: turn the ignition switch ON.";
    if (!accepted.StartAuthorisation) return "Start blocked: fingerprint authorisation is required.";
    if (accepted.BatteryVoltage < 9.5) return "Start blocked: battery voltage must be at least 9.5 V.";
    if (outputs.EngineState === ENGINE_STATES.RUN) return "Engine state is RUN. Use Normal stop or switch ignition OFF to shut down.";
    if (outputs.StartPermitted) return `Start sequence active: ${outputs.EngineStateLabel}.`;
    return "Ready: press Voice/manual start while the simulation is running.";
  }

  function renderOverview(accepted, outputs) {
    document.getElementById("overviewLambda").textContent = formatValue(outputs.LambdaEstimate, "", 3);
    document.getElementById("overviewSTFT").textContent = formatValue(outputs.STFT, "%", 1);
    document.getElementById("overviewInjectorPW").textContent = formatValue(outputs.InjectorPW, "ms", 3);
    document.getElementById("overviewTargetRPM").textContent = formatValue(outputs.TargetIdleRPM, "rpm", 0);
    document.getElementById("overviewRPMError").textContent = formatValue(outputs.RPMError, "rpm", 0);
    document.getElementById("overviewIdleDuty").textContent = formatValue(outputs.IdleControlDuty, "%", 1);
    document.getElementById("overviewControlTemp").textContent = formatValue(outputs.ControlTemperature, "°C", 1);
    document.getElementById("overviewFanDuty").textContent = formatValue(outputs.FanDuty, "%", 1);
    document.getElementById("overviewPumpDuty").textContent = formatValue(outputs.WaterPumpDuty, "%", 1);
    document.getElementById("overviewEngineState").textContent = outputs.EngineStateLabel;
    document.getElementById("overviewFuelPump").textContent = outputs.FuelPumpState ? "ON" : "OFF";
    document.getElementById("overviewInjection").textContent = outputs.InjectionEnable ? "ENABLED" : "DISABLED";

    document.getElementById("overviewExplanation").textContent =
      `${fuelExplanation(accepted, outputs)} ${idleExplanation(accepted, outputs)} ${coolingExplanation(accepted, outputs)}`;
  }

  const fuelCards = [
    ["O2SensorVoltage", "O₂ sensor voltage", "measured", "V", 2, "input"],
    ["ECT1Temp", "ECT1 temperature", "calculated", "°C", 1],
    ["EngineLoad", "Engine load", "calculated", "%", 1],
    ["LambdaEstimate", "Lambda estimate", "calculated", "", 3],
    ["STFT", "STFT / fuel correction", "calculated", "%", 1],
    ["WarmupEnrichment", "Warm-up enrichment", "calculated", "%", 1],
    ["BatteryCompensation", "Battery compensation", "calculated", "ms", 3],
    ["BaseInjectorPW", "Base injector PW", "calculated", "ms", 3],
    ["InjectorPW", "Final injector PW", "commanded", "ms", 3],
    ["ClosedLoopActive", "Closed loop", "status", "", 0, "binary"],
  ];

  const idleCards = [
    ["EngineSpeed", "Actual engine speed", "measured", "rpm", 0, "input"],
    ["TargetIdleRPM", "Target idle speed", "calculated", "rpm", 0],
    ["RPMError", "RPM error", "calculated", "rpm", 0],
    ["AccessoryLoad", "Accessory load", "measured", "%", 0, "input"],
    ["IdleControlDuty", "Idle-control duty", "commanded", "%", 1],
    ["IgnitionTiming", "Ignition timing", "commanded", "° BTDC", 2],
    ["IdleActive", "Idle control", "status", "", 0, "binary"],
  ];

  const coolingCards = [
    ["ECT1Voltage", "ECT1 voltage", "measured", "V", 2, "input"],
    ["ECT2Voltage", "ECT2 voltage", "measured", "V", 2, "input"],
    ["ECT1Temp", "ECT1 temperature", "calculated", "°C", 1],
    ["ECT2Temp", "ECT2 temperature", "calculated", "°C", 1],
    ["SensorDifference", "Sensor difference", "calculated", "°C", 1],
    ["ControlTemperature", "Control temperature", "calculated", "°C", 1],
    ["FanDuty", "PWM fan duty", "commanded", "%", 1],
    ["WaterPumpDuty", "Virtual pump duty", "commanded", "%", 1],
    ["SensorDisagreement", "ECT disagreement", "status", "", 0, "binary"],
    ["CoolingLoopActive", "Cooling loop", "status", "", 0, "binary"],
  ];

  const startRunCards = [
    ["BatteryVoltage", "Battery voltage", "measured", "V", 1, "input"],
    ["EngineSpeed", "Engine speed", "measured", "rpm", 0, "input"],
    ["EngineStateLabel", "Engine state", "status", "", 0, "state"],
    ["StateElapsedTime", "Time in state", "status", "s", 2],
    ["StartPermitted", "Start permitted", "status", "", 0, "binary"],
    ["FuelPumpState", "Fuel-pump relay", "commanded", "", 0, "binary"],
    ["StarterState", "Starter relay", "commanded", "", 0, "binary"],
    ["InjectionEnable", "Injection enable", "commanded", "", 0, "binary"],
    ["IgnitionEnable", "Ignition enable", "commanded", "", 0, "binary"],
  ];

  function renderCards(containerId, cards, accepted, outputs) {
    const container = document.getElementById(containerId);
    container.innerHTML = cards.map(([key, label, category, unit, decimals, mode]) => {
      const value = mode === "input" ? accepted[key] : outputs[key];
      let displayed;
      if (mode === "binary") displayed = value ? "ACTIVE / ON" : "INACTIVE / OFF";
      else if (mode === "state") displayed = String(value);
      else displayed = formatValue(value, unit, decimals);
      return `
        <article class="value-card">
          <span class="value-label">${label}</span>
          <strong class="value-number">${displayed}</strong>
          <span class="value-category category-badge ${category}">${category}</span>
        </article>
      `;
    }).join("");
  }

  function renderFuel(accepted, outputs) {
    renderCards("fuelValues", fuelCards, accepted, outputs);
    const badge = document.getElementById("closedLoopBadge");
    badge.textContent = outputs.ClosedLoopActive ? "Closed loop active" : "Closed loop inactive";
    badge.className = `state-badge ${outputs.ClosedLoopActive ? "active" : "warning"}`;
    document.getElementById("fuelExplanation").textContent = fuelExplanation(accepted, outputs);
  }

  function fuelExplanation(accepted, outputs) {
    if (!outputs.InjectionEnable) return "Injection is disabled because the engine is not in CRANK or RUN, so final injector pulse width is zero.";
    if (!outputs.ClosedLoopActive) {
      if (outputs.ECT1Temp < 70) return "Injection is enabled, but coolant temperature is below 70 °C; closed-loop correction is inactive and warm-up enrichment may be added.";
      if (accepted.EngineSpeed < 600) return "Injection is enabled, but engine speed is below 600 rpm; closed-loop correction remains inactive.";
      return "Closed-loop correction is inactive under the current operating condition.";
    }
    if (outputs.STFT > 0.5) return `O₂ voltage ${accepted.O2SensorVoltage.toFixed(2)} V gives a lean indication. Positive correction of ${outputs.STFT.toFixed(1)}% increases injector pulse width.`;
    if (outputs.STFT < -0.5) return `O₂ voltage ${accepted.O2SensorVoltage.toFixed(2)} V gives a rich indication. Negative correction of ${Math.abs(outputs.STFT).toFixed(1)}% reduces injector pulse width.`;
    return "O₂ voltage is near the simplified switching point, so lambda is near 1.00 and fuel correction is close to zero.";
  }

  function renderIdle(accepted, outputs) {
    renderCards("idleValues", idleCards, accepted, outputs);
    const badge = document.getElementById("idleActiveBadge");
    badge.textContent = outputs.IdleActive ? "Idle control active" : "Idle control inactive";
    badge.className = `state-badge ${outputs.IdleActive ? "active" : "warning"}`;
    document.getElementById("idleExplanation").textContent = idleExplanation(accepted, outputs);
  }

  function idleExplanation(accepted, outputs) {
    if (outputs.EngineState !== ENGINE_STATES.RUN) return "Idle control is inactive until the start/run state machine reaches RUN.";
    if (accepted.ThrottlePosition > 5) return "Throttle position is above 5%, so the model treats the engine as off-idle and disables idle control.";
    if (accepted.EngineSpeed >= 2000) return "Engine speed is above the idle-control range, so idle duty is disabled.";
    const direction = outputs.RPMError > 0 ? "below" : outputs.RPMError < 0 ? "above" : "at";
    return `Actual RPM is ${direction} the coolant-dependent target by ${Math.abs(outputs.RPMError).toFixed(0)} rpm. Idle duty is ${outputs.IdleControlDuty.toFixed(1)}% and ignition timing is ${outputs.IgnitionTiming.toFixed(2)}° BTDC.`;
  }

  function renderCooling(accepted, outputs) {
    renderCards("coolingValues", coolingCards, accepted, outputs);
    const badge = document.getElementById("sensorAgreementBadge");
    if (outputs.SensorDisagreement) {
      badge.textContent = "ECT disagreement";
      badge.className = "state-badge danger";
    } else {
      badge.textContent = "ECT sensors agree";
      badge.className = "state-badge active";
    }
    document.getElementById("coolingExplanation").textContent = coolingExplanation(accepted, outputs);
  }

  function coolingExplanation(accepted, outputs) {
    if (accepted.EmergencyStop) return "Emergency stop is active. The virtual cooling outputs are forced to zero by the emergency branch.";
    if (outputs.SensorDisagreement) return `ECT1 and ECT2 differ by ${outputs.SensorDifference.toFixed(1)} °C, which exceeds 15 °C. The virtual fail-safe commands 100% fan and pump duty.`;
    const acText = accepted.ACRequest && outputs.EngineState >= ENGINE_STATES.CRANK ? " The A/C request also enforces at least 35% fan duty." : "";
    return `The higher coolant value (${outputs.ControlTemperature.toFixed(1)} °C) controls the loop. Fan duty is ${outputs.FanDuty.toFixed(1)}% and virtual pump duty is ${outputs.WaterPumpDuty.toFixed(1)}%.${acText}`;
  }

  function renderStartRun(accepted, outputs) {
    renderCards("startRunValues", startRunCards, accepted, outputs);
    const badge = document.getElementById("startPermittedBadge");
    badge.textContent = outputs.StartPermitted ? "Start sequence permitted" : "Start not permitted";
    badge.className = `state-badge ${outputs.StartPermitted ? "active" : "warning"}`;

    const stepper = document.getElementById("stateStepper");
    stepper.innerHTML = STATE_LABELS.map((label, code) =>
      `<div class="state-step ${outputs.EngineState === code ? "active" : ""}">${label}</div>`
    ).join("");
    document.getElementById("startRunExplanation").textContent = startRunExplanation(accepted, outputs);
  }

  function startRunExplanation(accepted, outputs) {
    switch (outputs.EngineState) {
      case ENGINE_STATES.PRIME:
        return `Fuel pump is priming. CRANK will begin after 2.0 seconds unless stop, E-stop or ignition OFF is detected.`;
      case ENGINE_STATES.CRANK:
        return accepted.EngineSpeed >= 500
          ? "Cranking speed is at least 500 rpm, so the next model step will enter RUN."
          : `Starter, injection and ignition are enabled. The model is waiting for at least 500 rpm; CRANK times out after 5.0 seconds.`;
      case ENGINE_STATES.RUN:
        return "The engine state is RUN. Fuel pump, injection and ignition remain enabled while the starter is OFF.";
      case ENGINE_STATES.SHUTDOWN:
        return "Shutdown is active. Relay and enable outputs are OFF; the model returns to OFF after 0.5 seconds.";
      case ENGINE_STATES.OFF:
      default:
        return startConditionMessage(accepted, outputs);
    }
  }

  const chartConfigs = {
    fuel: {
      title: "Fuel-control relative trends",
      series: [
        ["O2SensorVoltage", "O₂ voltage", 0.05, 0.95, "#1267a5"],
        ["LambdaEstimate", "Lambda", 0.75, 1.25, "#7a3db8"],
        ["STFT", "STFT", -25, 25, "#b86b00"],
        ["InjectorPW", "Injector PW", 0, 20, "#18794e"],
      ],
    },
    idle: {
      title: "Idle-control relative trends",
      series: [
        ["EngineSpeed", "Actual RPM", 0, 1500, "#1267a5"],
        ["TargetIdleRPM", "Target RPM", 750, 1200, "#7a3db8"],
        ["IdleControlDuty", "Idle duty", 0, 100, "#b86b00"],
        ["IgnitionTiming", "Ignition timing", -5, 45, "#18794e"],
      ],
    },
    cooling: {
      title: "Cooling relative trends",
      series: [
        ["ECT1Temp", "ECT1", -20, 135, "#1267a5"],
        ["ECT2Temp", "ECT2", -20, 135, "#7a3db8"],
        ["FanDuty", "Fan duty", 0, 100, "#b86b00"],
        ["WaterPumpDuty", "Virtual pump", 0, 100, "#18794e"],
      ],
    },
    startRun: {
      title: "Start/run state trends",
      series: [
        ["EngineState", "Engine state", 0, 4, "#1267a5"],
        ["FuelPumpState", "Fuel pump", 0, 1, "#7a3db8"],
        ["StarterState", "Starter", 0, 1, "#b86b00"],
        ["InjectionEnable", "Injection", 0, 1, "#18794e"],
        ["IgnitionEnable", "Ignition", 0, 1, "#b42318"],
      ],
    },
  };

  function drawChart() {
    const canvas = document.getElementById("trendCanvas");
    const context = canvas.getContext("2d");
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(300, canvas.clientWidth);
    const height = Math.max(220, canvas.clientHeight);
    const pixelWidth = Math.floor(width * ratio);
    const pixelHeight = Math.floor(height * ratio);
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);

    const type = document.getElementById("chartSelect").value;
    const config = chartConfigs[type];
    const padding = { left: 48, right: 18, top: 30, bottom: 35 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;

    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, width, height);
    context.fillStyle = "#17212b";
    context.font = "700 13px system-ui";
    context.fillText(config.title, padding.left, 19);

    context.strokeStyle = "#d9e0e7";
    context.lineWidth = 1;
    context.font = "11px system-ui";
    context.fillStyle = "#5e6b78";
    for (let grid = 0; grid <= 4; grid += 1) {
      const y = padding.top + (plotHeight * grid) / 4;
      context.beginPath();
      context.moveTo(padding.left, y);
      context.lineTo(width - padding.right, y);
      context.stroke();
      context.fillText(`${100 - grid * 25}%`, 8, y + 4);
    }

    if (history.length < 2) {
      context.fillStyle = "#5e6b78";
      context.font = "14px system-ui";
      context.fillText("Run the simulation to collect trend data.", padding.left + 15, padding.top + plotHeight / 2);
      renderChartLegend(config, null);
      return;
    }

    const firstTime = history[0].time;
    const lastTime = history[history.length - 1].time;
    const span = Math.max(0.2, lastTime - firstTime);

    for (const [key, label, min, max, color] of config.series) {
      context.strokeStyle = color;
      context.lineWidth = 2;
      context.beginPath();
      history.forEach((point, index) => {
        const normalizedX = (point.time - firstTime) / span;
        const normalizedY = clamp((Number(point[key]) - min) / (max - min), 0, 1);
        const x = padding.left + normalizedX * plotWidth;
        const y = padding.top + (1 - normalizedY) * plotHeight;
        if (index === 0) context.moveTo(x, y);
        else context.lineTo(x, y);
      });
      context.stroke();
    }

    context.fillStyle = "#5e6b78";
    context.font = "11px system-ui";
    context.fillText(`${firstTime.toFixed(1)} s`, padding.left, height - 10);
    const endLabel = `${lastTime.toFixed(1)} s`;
    const endWidth = context.measureText(endLabel).width;
    context.fillText(endLabel, width - padding.right - endWidth, height - 10);
    context.save();
    context.translate(13, padding.top + plotHeight / 2);
    context.rotate(-Math.PI / 2);
    context.fillText("Relative position within each signal range", 0, 0);
    context.restore();

    renderChartLegend(config, history[history.length - 1]);
  }

  function renderChartLegend(config, latest) {
    const legend = document.getElementById("chartLegend");
    legend.innerHTML = config.series.map(([key, label, min, max, color]) => {
      const value = latest ? Number(latest[key]).toFixed(2) : "—";
      return `<span class="legend-item"><span class="legend-swatch" style="background:${color}"></span>${label}: ${value}</span>`;
    }).join("");
  }

  function exportCsv() {
    if (!history.length) {
      window.alert("Run the simulation first so there is history to export.");
      return;
    }
    const columns = Array.from(new Set(history.flatMap((row) => Object.keys(row))));
    const escape = (value) => {
      const text = String(value ?? "");
      return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
    };
    const lines = [columns.join(","), ...history.map((row) => columns.map((key) => escape(row[key])).join(","))];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "engine_live_data_virtual_lab_history.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  function activateTab(tabId) {
    document.querySelectorAll(".tab").forEach((button) => button.classList.toggle("active", button.dataset.tab === tabId));
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === tabId));
  }

  function attachEvents() {
    document.getElementById("runButton").addEventListener("click", () => setRunning(true));
    document.getElementById("pauseButton").addEventListener("click", () => setRunning(false));
    document.getElementById("resetButton").addEventListener("click", resetSimulation);
    document.getElementById("exportButton").addEventListener("click", exportCsv);
    document.getElementById("chartSelect").addEventListener("change", drawChart);

    document.querySelectorAll(".tab").forEach((button) => button.addEventListener("click", () => activateTab(button.dataset.tab)));
    document.querySelectorAll("[data-open-tab]").forEach((card) => card.addEventListener("click", () => activateTab(card.dataset.openTab)));

    for (const key of ["IgnitionSwitch", "StartAuthorisation", "ACRequest"]) {
      document.getElementById(key).addEventListener("change", (event) => {
        inputs[key] = event.target.checked ? 1 : 0;
        forceStateEvaluation();
      });
    }

    document.getElementById("startRequestButton").addEventListener("click", () => {
      if (!running) setRunning(true);
      pulseInput("StartRequest", 500);
    });
    document.getElementById("stopRequestButton").addEventListener("click", () => pulseInput("StopRequest", 500));
    document.getElementById("emergencyButton").addEventListener("click", () => {
      inputs.EmergencyStop = 1;
      forceStateEvaluation();
    });
    document.getElementById("resetEmergencyButton").addEventListener("click", () => {
      inputs.EmergencyStop = 0;
      calculateSnapshot(false);
      render();
    });

    document.getElementById("loadPresetButton").addEventListener("click", () => {
      const key = document.getElementById("presetSelect").value;
      if (!key || !presets[key]) return;
      Object.assign(inputs, presets[key]);
      syncAllInputControls();
      calculateSnapshot(false);
      render();
    });

    window.addEventListener("resize", drawChart);
  }

  function initialise() {
    buildNumericControls();
    syncAllInputControls();
    attachEvents();
    calculateSnapshot(false);
    render();
  }

  initialise();
})();
