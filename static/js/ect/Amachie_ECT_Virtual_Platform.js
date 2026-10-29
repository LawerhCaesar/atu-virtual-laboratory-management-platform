/*
 * DAVID AMACHIE - ENGINE COOLANT TEMPERATURE VIRTUAL LAB
 * Single-file JavaScript reference implementation and Codex handoff, v1.0.0.
 * Source: validated native Simulink R2024b model, 25 October 2026.
 * Browser: <script src="Amachie_ECT_Virtual_Platform.js"></script>
 *          AmachieECT.mount(document.querySelector('#ect-lab'));
 * Node:    const ECT = require('./Amachie_ECT_Virtual_Platform.js');
 *          const run = ECT.simulate();
 * Commands: --self-test | --verify-csv PATH | --brief | --demo OUTPUT.html
 * No dependencies, network calls, API keys, MATLAB or Simulink runtime required.
 * This is a deliberate port of ONE ECT sensor model, not a generic SLX converter.
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AmachieECT = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const VERSION = '1.0.0';
  const SOURCE = Object.freeze({
    model: 'David_Amachie_ECT_Complete_Interactive_Model.slx',
    folder: 'F:\\Scripts for codex\\Mr. Amachie',
    sha256: '227F2EEB1BCC63FA49AE3F7AC00E0D457C87A1EF7A40510D6EEB81D80CA8A6E6',
    release: 'MATLAB / Simulink R2024b', date: '2026-10-25',
    chat: 'https://chatgpt.com/s/cx_6ade6c06f2308191a15a14ab6b0dfa08',
    threadId: '01a174ab-4743-7293-a73d-88f677355ca9',
    chatNote: 'Public, immutable snapshot of the source conversation; not a live link to later updates. Local files are not supplied by this link.'
  });
  const DEFAULTS = Object.freeze({
    inputMode: 1, fixedCoolantC: 85, stepTimeS: 20, stepBeforeC: 20,
    stepAfterC: 100, initialSensorC: 20, minTempC: -20, maxTempC: 130,
    tauS: 3, r0Ohm: 2500, betaK: 3950, referenceTempC: 25,
    referenceVoltageV: 5, pullupOhm: 2490, adcMaxCount: 4095,
    dtS: 0.01, stopTimeS: 120
  });
  const OUTPUTS = Object.freeze([
    'Coolant_Input_C', 'Sensor_Temperature_C', 'Thermistor_Resistance_Ohm',
    'ECT_Voltage_V', 'ADC_Count', 'Reconstructed_Temperature_C',
    'Conversion_Error_C', 'Input_Valid_Status', 'Conversion_Valid_Status'
  ]);
  const MAX_INTERVALS = 100000;
  const clamp = (x, lo, hi) => Math.min(Math.max(x, lo), hi);
  class ECTError extends Error {
    constructor(code, message) { super(message); this.name = 'ECTError'; this.code = code; }
  }
  function insist(ok, code, message) { if (!ok) throw new ECTError(code, message); }
  function validateConfig(overrides = {}) {
    insist(overrides && typeof overrides === 'object' && !Array.isArray(overrides), 'CONFIG', 'Configuration must be an object.');
    for (const key of Object.keys(overrides)) insist(Object.hasOwn(DEFAULTS, key), 'UNKNOWN_PARAMETER', `Unknown parameter: ${key}`);
    const c = { ...DEFAULTS, ...overrides };
    for (const [key, value] of Object.entries(c)) insist(typeof value === 'number' && Number.isFinite(value), 'FINITE_NUMBER', `${key} must be a finite number.`);
    insist(c.inputMode === 0 || c.inputMode === 1, 'MODE', 'Input mode must be 0 (fixed) or 1 (step).');
    insist(c.stepTimeS >= 0, 'STEP_TIME', 'Step time must be nonnegative.');
    insist(c.minTempC > -273.15 && c.maxTempC > c.minTempC && c.referenceTempC > -273.15, 'TEMPERATURE_RANGE', 'Tmin and T0 must exceed absolute zero; Tmax must exceed Tmin.');
    insist(c.initialSensorC >= c.minTempC && c.initialSensorC <= c.maxTempC, 'INITIAL_TEMPERATURE', 'Initial sensor temperature must be inside Tmin and Tmax.');
    for (const key of ['tauS', 'r0Ohm', 'betaK', 'referenceVoltageV', 'pullupOhm']) insist(c[key] > 0, 'POSITIVE_PARAMETER', `${key} must be positive.`);
    insist(Number.isInteger(c.adcMaxCount) && c.adcMaxCount >= 3 && c.adcMaxCount <= 16777215, 'ADC_MAX', 'ADC maximum count must be an integer from 3 to 16777215.');
    const lowR = c.pullupOhm / (c.adcMaxCount - 1);
    insist(1 / (c.referenceTempC + 273.15) + Math.log(lowR / c.r0Ohm) / c.betaK > 0, 'INVERSE_DOMAIN', 'Calibration makes the inverse temperature equation invalid at the first usable ADC count.');
    for (const t of [c.minTempC, c.maxTempC]) {
      const r = c.r0Ohm * Math.exp(c.betaK * (1 / (t + 273.15) - 1 / (c.referenceTempC + 273.15)));
      insist(Number.isFinite(r) && r > 0, 'RESISTANCE_DOMAIN', 'Calibration overflows or underflows the thermistor resistance.');
      insist(Number.isFinite(r + c.pullupOhm) && Number.isFinite(c.referenceVoltageV * r), 'NUMERICAL_RANGE', 'Electrical parameters exceed the supported numeric range.');
    }
    insist(Number.isFinite(c.pullupOhm * (c.adcMaxCount - 1)), 'NUMERICAL_RANGE', 'Inverse resistance exceeds the supported numeric range.');
    insist(c.dtS > 0 && c.dtS <= c.tauS / 10, 'TIME_STEP', 'Time step must be positive and no larger than tau / 10.');
    const intervals = c.stopTimeS / c.dtS;
    insist(c.stopTimeS > 0 && Number.isFinite(intervals) && intervals >= 1 && Math.abs(intervals - Math.round(intervals)) < 1e-7 && intervals <= MAX_INTERVALS, 'DURATION', `Stop time must be a positive whole number of time steps, with at most ${MAX_INTERVALS} intervals.`);
    return Object.freeze(c);
  }
  function requestedAt(t, c) {
    if (c.inputMode === 0) return c.fixedCoolantC;
    // Resolve representation noise at an exact sample boundary, without a physical time shift.
    const eps = 8 * Number.EPSILON * Math.max(1, Math.abs(t), Math.abs(c.stepTimeS));
    return t + eps >= c.stepTimeS ? c.stepAfterC : c.stepBeforeC;
  }
  function rawSnapshot(t, sensor, c) {
    const requested = requestedAt(t, c);
    const tc = clamp(requested, c.minTempC, c.maxTempC);
    const r = c.r0Ohm * Math.exp(c.betaK * (1 / (sensor + 273.15) - 1 / (c.referenceTempC + 273.15)));
    const voltage = c.referenceVoltageV * r / (c.pullupOhm + r);
    // Counts are nonnegative, so Math.round matches MATLAB round, including positive half-counts.
    const adc = Math.round(clamp(voltage / c.referenceVoltageV * c.adcMaxCount, 0, c.adcMaxCount));
    const safeCount = clamp(adc, 1, c.adcMaxCount - 1);
    const estimatedR = c.pullupOhm * safeCount / (c.adcMaxCount - safeCount);
    const estimatedT = 1 / (1 / (c.referenceTempC + 273.15) + Math.log(estimatedR / c.r0Ohm) / c.betaK) - 273.15;
    const row = {
      timeS: t, Coolant_Input_C: tc, Sensor_Temperature_C: sensor,
      Thermistor_Resistance_Ohm: r, ECT_Voltage_V: voltage, ADC_Count: adc,
      Reconstructed_Temperature_C: estimatedT, Conversion_Error_C: estimatedT - sensor,
      Input_Valid_Status: Number(requested >= c.minTempC && requested <= c.maxTempC),
      Conversion_Valid_Status: Number(adc > 0 && adc < c.adcMaxCount),
      Requested_Coolant_C: requested, Quantised_Voltage_V: adc * c.referenceVoltageV / c.adcMaxCount,
      Reconstructed_Resistance_Ohm: estimatedR
    };
    insist(Object.values(row).every(Number.isFinite), 'NONFINITE_OUTPUT', 'A calculation produced a nonfinite value; review the calibration.');
    return Object.freeze(row);
  }
  function createEngine(overrides = {}) {
    const config = validateConfig(overrides), finalTick = Math.round(config.stopTimeS / config.dtS);
    let tick = 0, sensor = config.initialSensorC;
    const snapshot = () => rawSnapshot(tick * config.dtS, sensor, config);
    function step() {
      if (tick >= finalTick) return snapshot();
      const h = config.dtS, t0 = tick * h, tm = (tick + 0.5) * h, t1 = (tick + 1) * h;
      const derivative = (t, s) => (clamp(requestedAt(t, config), config.minTempC, config.maxTempC) - s) / config.tauS;
      const k1 = derivative(t0, sensor);
      const k2 = derivative(tm, sensor + h * k1 / 2);
      const k3 = derivative(tm, sensor + h * k2 / 2);
      const k4 = derivative(t1, sensor + h * k3);
      const next = sensor + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
      // Validate before committing the next state.
      const result = rawSnapshot(t1, next, config);
      sensor = next; tick += 1; return result;
    }
    return Object.freeze({
      config, snapshot, step,
      get done() { return tick >= finalTick; },
      advance(count = 1) {
        insist(Number.isInteger(count) && count >= 0 && count <= MAX_INTERVALS, 'ADVANCE', 'advance expects an integer step count in the supported range.');
        let result = snapshot(); for (let i = 0; i < count && tick < finalTick; i++) result = step(); return result;
      },
      reset() { tick = 0; sensor = config.initialSensorC; return snapshot(); }
    });
  }
  function simulate(config = {}) {
    const engine = createEngine(config), samples = [engine.snapshot()];
    while (!engine.done) samples.push(engine.step());
    return Object.freeze({ config: engine.config, samples: Object.freeze(samples), final: samples[samples.length - 1] });
  }
  function toCSV(run) {
    const columns = ['timeS', ...OUTPUTS, 'Requested_Coolant_C', 'Quantised_Voltage_V', 'Reconstructed_Resistance_Ohm'];
    return columns.join(',') + '\n' + run.samples.map(r => columns.map(k => r[k]).join(',')).join('\n') + '\n';
  }
  function verifyReferenceCSV(text) {
    const lines = text.trim().split(/\r?\n/).map(line => line.split(','));
    const expectedHeaders = ['Time_s','Coolant_C','Sensor_C','Resistance_ohm','Voltage_V','ADC_Count','Estimated_C','Error_C','Input_Valid','Conversion_Valid'];
    insist(lines[0].join(',') === expectedHeaders.join(','), 'CSV_HEADER', 'Expected the original default_run.csv header.');
    const run = simulate();
    insist(lines.length - 1 === run.samples.length, 'CSV_ROWS', 'Reference must contain all 12001 default-run samples.');
    const maxima = Object.fromEntries(OUTPUTS.map(key => [key, 0]));
    const limits = [1e-8, 1e-8, 1e-6, 1e-9, 0, 1e-8, 1e-8, 0, 0];
    for (let i = 1; i < lines.length; i++) {
      const ref = lines[i].map(v => v.trim() === '' ? NaN : Number(v));
      insist(ref.length === 10 && ref.every(Number.isFinite), 'CSV_VALUE', `Malformed reference row ${i}.`);
      const actual = run.samples[i - 1];
      insist(Math.abs(ref[0] - actual.timeS) < 1e-9, 'CSV_TIME', `Time mismatch at row ${i}.`);
      OUTPUTS.forEach((key, j) => {
        const error = Math.abs(ref[j + 1] - actual[key]); maxima[key] = Math.max(maxima[key], error);
        insist(error <= limits[j], 'REFERENCE_MISMATCH', `${key} disagrees with Simulink at t=${ref[0]} s; error=${error}.`);
      });
    }
    return { status: 'PASS', rows: run.samples.length, signals: 9, maxAbsoluteErrors: maxima, tolerances: Object.fromEntries(OUTPUTS.map((k,i)=>[k,limits[i]])) };
  }
  function selfTest() {
    const results = [];
    const check = (name, fn) => { fn(); results.push({ name, status: 'PASS' }); };
    const close = (a,b,t=1e-8) => insist(Math.abs(a-b)<=t,'TEST',`${a} differs from ${b}.`);
    const reject = (override, code) => { let got; try { validateConfig(override); } catch(e) { got=e.code; } insist(got===code,'TEST',`Expected ${code}; got ${got}.`); };
    check('Default 120-second run', () => { const r=simulate(); insist(r.samples.length===12001,'TEST','Sample count'); close(r.final.Sensor_Temperature_C,100); close(r.final.ADC_Count,268,0);close(r.final.Reconstructed_Temperature_C,100.00169261318308); });
    check('RK4 step boundary matches Simulink', () => close(simulate().samples[2000].Sensor_Temperature_C,20.0444444444444));
    for (const temp of [-20,25,85,100,130,-40,150]) check(`Fixed input ${temp} C`, () => {
      const r=simulate({inputMode:0,fixedCoolantC:temp,stopTimeS:60}), target=clamp(temp,-20,130);
      for(const s of r.samples) close(s.Sensor_Temperature_C,target+(20-target)*Math.exp(-s.timeS/3),1e-7);
      close(r.final.Input_Valid_Status,Number(temp>=-20&&temp<=130),0);
    });
    check('Cooling response', () => { const r=simulate({initialSensorC:100,stepBeforeC:100,stepAfterC:20});close(r.final.Sensor_Temperature_C,20);close(r.final.ADC_Count,2282,0); });
    for(const tau of [1,10]) check(`Time constant ${tau} s`, () => { const r=simulate({tauS:tau}); for(const s of r.samples) { const expected=s.timeS<20?20:100-80*Math.exp(-(s.timeS-20)/tau); close(s.Sensor_Temperature_C,expected,.15); } });
    for(const max of [255,65535]) check(`ADC max ${max}`, () => { const r=simulate({adcMaxCount:max});close(r.final.ADC_Count,max===255?17:4289,0); });
    for(const temp of [-20,130]) check(`ADC rail at ${temp} C`, () => {const s=simulate({adcMaxCount:3,inputMode:0,fixedCoolantC:temp,stopTimeS:60}).final;close(s.Conversion_Valid_Status,0,0);insist(Number.isFinite(s.Reconstructed_Temperature_C),'TEST','Rail fallback not finite');});
    for(const [name,over,code] of [
      ['Zero tau',{tauS:0},'POSITIVE_PARAMETER'],['Negative resistance',{r0Ohm:-1},'POSITIVE_PARAMETER'],
      ['Zero voltage',{referenceVoltageV:0},'POSITIVE_PARAMETER'],['Fractional ADC',{adcMaxCount:4095.5},'ADC_MAX'],
      ['Invalid mode',{inputMode:2},'MODE'],['Reversed limits',{maxTempC:-30},'TEMPERATURE_RANGE'],
      ['Absolute zero',{referenceTempC:-273.15},'TEMPERATURE_RANGE'],['Initial outside range',{initialSensorC:150},'INITIAL_TEMPERATURE'],
      ['Oversized time step',{tauS:.001},'TIME_STEP'],['NaN input',{fixedCoolantC:NaN},'FINITE_NUMBER'],
      ['String value',{fixedCoolantC:'85'},'FINITE_NUMBER'],['Negative step time',{stepTimeS:-1},'STEP_TIME'],
      ['Unknown setting',{tau:3},'UNKNOWN_PARAMETER'],['Unaligned duration',{stopTimeS:.015},'DURATION'],
      ['Workload limit',{stopTimeS:1001},'DURATION'],['Sub-step duration',{stopTimeS:1e-13},'DURATION'],['Invalid inverse calibration',{betaK:1},'INVERSE_DOMAIN']
    ]) check(`Reject: ${name}`,()=>reject(over,code));
    check('Independent instances and deterministic reset',()=>{const a=createEngine(),b=createEngine();a.advance(2100);close(b.snapshot().timeS,0,0);a.reset();close(a.snapshot().Sensor_Temperature_C,20,0);close(a.advance(2000).Sensor_Temperature_C,20.0444444444444);});
    check('Stop boundary is idempotent',()=>{const a=createEngine({stopTimeS:.02});a.advance(10);close(a.step().timeS,.02,0);});
    check('Configuration is immutable',()=>{const c={tauS:3};const a=createEngine(c);c.tauS=8;close(a.config.tauS,3,0);insist(Object.isFrozen(a.config),'TEST','Config not frozen');});
    check('CSV export preserves full-resolution samples',()=>insist(toCSV(simulate({stopTimeS:.02})).trim().split('\n').length===4,'TEST','CSV row count'));
    return { status:'PASS', tests:results.length, results };
  }

  // CODEX_BRIEF and the optional browser interface are below. The numeric engine
  // above does not access the DOM and can be used directly in Node or a worker.
  const CODEX_BRIEF = `Build an ECT sensor laboratory inside the user's existing virtual platform.
Use this file as the working numerical reference; inspect the existing application first.
Do not replace unrelated pages or invent combustion, fan, speed, RPM or fuel-control physics.

SOURCE AND CONTEXT
Model: ${SOURCE.model}
Local source folder: ${SOURCE.folder}
Model SHA-256: ${SOURCE.sha256}
Source chat: ${SOURCE.chat}
${SOURCE.chatNote}
If a local read_thread tool is available and authorized, the source thread ID is ${SOURCE.threadId}.
This handoff is self-contained. Do not stop work merely because the chat or MATLAB is unavailable.

IMPLEMENTATION
1. Keep the pure numerical engine separate from rendering. Use AmachieECT.createEngine,
   simulate and validateConfig, or port them faithfully into the project's chosen architecture.
2. Preserve all nine original named outputs, their units, two validity flags, parameter defaults,
   0.01-second RK4 sampling, and ADC rounding/clamping. Protect both ADC rails and inverse domains.
3. Never use a browser frame interval as the numerical integration step. Playback speed changes
   presentation only. Pause when the page becomes hidden. Apply edited settings atomically and reset.
4. Reuse the platform's design system, routing, authentication and storage conventions. The local
   reference has no accounts, network calls or telemetry. Add persistence only if explicitly needed.
5. Run --self-test and --verify-csv against ECT_Validation_2026-10-25/default_run.csv when available.
   Do not replace calculated values with hard-coded results. Re-test any changed engine.

REQUIRED VISUAL OUTPUT - DO NOT FINISH WITH CODE OR STATIC PICTURES ALONE
Deliver an operational, responsive ECT lab screen with:
- A labelled stationary engine-bay/coolant-sensor/ECU schematic (SVG or equivalent). Show Tc and Ts
  with a consistent temperature colour scale, and show the computed voltage and ADC signal path.
  Animation is instructional signal activity, not an invented coolant flow or vehicle motion model.
- Numeric readouts with units for applied coolant, sensor temperature, ECU estimate, resistance,
  voltage, ADC count and conversion error. Show input validity and conversion validity separately.
  ADC-rail estimates must be clearly marked FALLBACK / INVALID; never display a misleading green OK.
- Four readable, synchronized plots: [Tc, Ts, estimated temperature], [R, reconstructed R],
  [analogue voltage, quantised voltage], and ADC count. Also provide the conversion-error plot.
- Start/Pause, Reset, timeline scrubber, playback speed, scenario presets, editable settings with
  inline validation, and CSV export of every computed sample and both flags. Display changes are
  decimated only for plotting; exported and computed data retain full resolution.
- Keyboard-operable controls, visible focus, accessible names, non-colour status text, reduced-motion
  support, and layouts checked at desktop and narrow mobile width. Avoid overlapping labels.
- On-screen explanation that this is an ideal first-order sensor model, not a full engine model.

ANIMATED CAR RECOMMENDATION
A stationary car cutaway with the ECT sensor highlighted is suitable if the platform already uses
car graphics. Make it optional around the required sensor/ECU schematic. Do not add moving wheels,
RPM, fan switching, boiling coolant, fuel changes or overheating alarms unless independently
specified and modelled. A photo-realistic or 3D car is not required for this model's learning goal.

ACCEPTANCE AND HANDOVER
Demonstrate default heating, cooling, fixed 85 C, out-of-range clamping, both ADC rails, invalid
settings, pause/resume, reset, scrubbing and CSV export. Compare the complete 12001-sample default
trace to the supplied Simulink CSV, with the tolerances implemented by verifyReferenceCSV.
Disclose that other scenarios have JavaScript analytical/guard tests, not full Simulink trace parity.
Capture labelled screenshots at the initial state, warm-up and final state, plus a rail-invalid
state and mobile view. Provide the working route or local launch instructions and test results.
Demand these corresponding visual outputs before calling the platform integration complete.
Do not deploy or publish the platform without the user's authorization.`;

  const PRESETS = Object.freeze({
    heating: Object.freeze({ label: 'Default heating', config: {} }),
    cooling: Object.freeze({ label: 'Cooling', config: {initialSensorC:100,stepBeforeC:100,stepAfterC:20} }),
    fixed: Object.freeze({ label: 'Fixed 85 C', config: {inputMode:0,fixedCoolantC:85} }),
    clamped: Object.freeze({ label: 'Input above limit', config: {inputMode:0,fixedCoolantC:150} }),
    lowRail: Object.freeze({ label: 'ADC lower rail', config: {inputMode:0,fixedCoolantC:130,adcMaxCount:3} }),
    highRail: Object.freeze({ label: 'ADC upper rail', config: {inputMode:0,fixedCoolantC:-20,adcMaxCount:3} })
  });
  const FIELD_LABELS = Object.freeze({
    fixedCoolantC:'Fixed coolant (C)',stepTimeS:'Step time (s)',stepBeforeC:'Before step (C)',stepAfterC:'After step (C)',
    initialSensorC:'Initial sensor (C)',minTempC:'Minimum (C)',maxTempC:'Maximum (C)',tauS:'Time constant (s)',
    r0Ohm:'Reference resistance (ohm)',betaK:'Beta (K)',referenceTempC:'Reference temperature (C)',
    referenceVoltageV:'Reference voltage (V)',pullupOhm:'Pull-up resistance (ohm)',adcMaxCount:'Maximum ADC count',
    dtS:'Calculation step (s)',stopTimeS:'Duration (s)'
  });
  const PLOTS = Object.freeze([
    {title:'Temperature response',unit:'C',series:[['Coolant_Input_C','Coolant','#1769cf'],['Sensor_Temperature_C','Sensor','#be5600'],['Reconstructed_Temperature_C','ECU estimate','#8050a8']]},
    {title:'Thermistor resistance',unit:'ohm',series:[['Thermistor_Resistance_Ohm','NTC','#1769cf'],['Reconstructed_Resistance_Ohm','Reconstructed','#be5600']]},
    {title:'Voltage conversion',unit:'V',series:[['ECT_Voltage_V','Analogue','#1769cf'],['Quantised_Voltage_V','Quantised','#be5600']]},
    {title:'ADC output',unit:'counts',series:[['ADC_Count','Digital count','#1769cf']]},
    {title:'Conversion error',unit:'C',series:[['Conversion_Error_C','Estimate minus sensor','#8050a8']]}
  ]);
  // Preserve each bucket's minimum and maximum for display. No numerical data is discarded.
  function plotPoints(rows, key, maxPoints = 500) {
    if(rows.length <= maxPoints) return rows;
    const size = Math.ceil(rows.length / Math.floor(maxPoints/2)), selected=[0,rows.length-1];
    for(let i=0;i<rows.length;i+=size){let lo=i,hi=i;for(let j=i;j<Math.min(i+size,rows.length);j++){if(rows[j][key]<rows[lo][key])lo=j;if(rows[j][key]>rows[hi][key])hi=j;}selected.push(lo,hi);}
    return [...new Set(selected)].sort((a,b)=>a-b).map(i=>rows[i]);
  }
  function mount(container, overrides = {}) {
    insist(container && container.ownerDocument && typeof container.appendChild==='function','DOM','Pass a browser DOM element to mount().');
    const doc=container.ownerDocument, win=doc.defaultView;
    let run=simulate(overrides), index=0, playing=false, disposed=false, raf=0, lastStamp=null, playTime=0, lastChart=0;
    const host=doc.createElement('div');host.className='amachie-ect-host';container.appendChild(host);
    const ui=host.attachShadow({mode:'open'}), q=selector=>ui.querySelector(selector);
    const reduced=win.matchMedia('(prefers-reduced-motion: reduce)');
    const fieldHTML=Object.entries(FIELD_LABELS).map(([key,label])=>`<label>${label}<input data-setting="${key}" type="number" step="any" required aria-label="${label}"></label>`).join('');
    ui.innerHTML=`<style>
      :host{display:block;color:#18364b;font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;color-scheme:light}
      *{box-sizing:border-box} .lab{background:#f3f7fa;border:1px solid #d5e1e8;border-radius:20px;padding:clamp(16px,3vw,32px);max-width:1440px;margin:auto}
      h1{font-size:clamp(26px,3vw,37px);line-height:1.12;margin:6px 0 12px;letter-spacing:-1px}h2{font-size:19px;margin:0 0 12px}h3{font-size:16px;margin:0}
      p{margin:6px 0 12px}.eyebrow{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#427187;font-weight:750}.muted{color:#526977;font-size:13px}
      .top{display:flex;align-items:start;justify-content:space-between;gap:20px}.tag{font-size:12px;background:#dceef4;border-radius:30px;padding:6px 12px;white-space:nowrap}
      .controls{display:flex;align-items:end;gap:12px;flex-wrap:wrap;margin:24px 0 18px}.controls label{font-size:12px;font-weight:650;display:grid;gap:5px}
      button,select,input{font:inherit;color:inherit;border:1px solid #b8cbd6;border-radius:8px;background:white;padding:9px 12px;min-height:42px}
      button{cursor:pointer;font-weight:650}button.primary{background:#145d7a;color:white;border-color:#145d7a}button:disabled{opacity:.5;cursor:default}
      :focus-visible{outline:3px solid #e88013;outline-offset:3px}a{color:#145d7a}.grid{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(260px,1fr);gap:18px}
      .panel{background:#fff;border:1px solid #d5e1e8;border-radius:14px;padding:20px;min-width:0}.diagram-scroll{overflow-x:auto}.schematic{width:100%;height:auto;display:block;min-width:600px}.swipe-note{display:none}.temperature-gradient{width:180px;height:6px;border-radius:4px;background:linear-gradient(90deg,hsl(220 62% 49%),hsl(115 62% 49%),hsl(10 62% 49%));margin:8px 0 4px}.status{padding:10px 12px;border-radius:8px;font-size:13px;margin:8px 0;background:#e5f3ed;color:#1b6049}.status.warn{background:#fff0d4;color:#80500a}.status.bad{background:#fce4e0;color:#922b22}
      .metrics{display:grid;grid-template-columns:1fr 1fr;gap:14px}.metric{border-bottom:1px solid #e4ecf1;padding:7px 0 12px}.metric span{display:block;color:#526977;font-size:12px}.metric strong{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums}.metric em{font-style:normal;font-size:11px;margin-left:6px;color:#526977}
      .timeline{display:grid;grid-template-columns:auto 1fr auto;gap:14px;align-items:center;margin:20px 0}.timeline input{padding:0;width:100%;accent-color:#145d7a;min-width:0}.timeline output{font-variant-numeric:tabular-nums;min-width:85px;text-align:right}
      .plots{display:grid;grid-template-columns:1fr 1fr;gap:18px}.plot:last-child{grid-column:1/-1}.plot svg{width:100%;display:block;overflow:visible}.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:11px;margin:6px 0}.legend i{width:15px;height:3px;display:inline-block;vertical-align:middle;margin-right:4px}
      .chart-note{font-size:11px;color:#526977;margin-top:4px}details{margin:20px 0}summary{cursor:pointer;font-weight:700;padding:10px 0}.settings{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.settings label{font-size:12px;font-weight:600;display:grid;gap:4px}.settings input{width:100%;min-width:0}.settings-actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:16px}.error{color:#922b22;font-weight:600;font-size:13px}.foot{font-size:12px;color:#526977;margin:20px 0 0}.signal{stroke-dasharray:7 6}.running .signal{animation:ect-signal 1.5s linear infinite}@keyframes ect-signal{to{stroke-dashoffset:-26}}
      .reduced .signal{animation:none!important}@media(prefers-reduced-motion:reduce){.signal{animation:none!important}}@media(max-width:820px){.grid{grid-template-columns:1fr}.settings{grid-template-columns:repeat(2,minmax(0,1fr))}.top{display:block}.tag{display:inline-block;margin-top:4px}}
      @media(max-width:560px){.plots{grid-template-columns:1fr}.plot:last-child{grid-column:auto}.panel{padding:14px}.timeline{gap:8px;grid-template-columns:auto 1fr}.timeline output{grid-column:2;text-align:left}.controls{gap:8px}.controls>label{flex:1 1 140px}.settings{grid-template-columns:1fr 1fr}.metrics strong{font-size:20px}.lab{border-radius:0}.swipe-note{display:block;font-size:12px;color:#526977}}
    </style><section class="lab" aria-label="Engine coolant temperature virtual laboratory">
      <header class="top"><div><div class="eyebrow">David Amachie / Virtual vehicle laboratory</div><h1>Read the temperature.<br>Follow the signal.</h1><p class="muted">Explore how a coolant sensor becomes a digital temperature reading.</p></div><span class="tag">ECT sensor / validated reference logic</span></header>
      <div class="controls"><label>Experiment<select id="preset" aria-label="Experiment">${Object.entries(PRESETS).map(([k,v])=>`<option value="${k}">${v.label}</option>`).join('')}<option value="custom">Custom settings</option></select></label>
      <button id="play" class="primary">Start</button><button id="reset">Reset</button><label>Playback speed<select id="speed" aria-label="Playback speed"><option value="0.25">0.25x</option><option value="1" selected>1x</option><option value="5">5x</option><option value="20">20x</option></select></label><button id="export">Export CSV</button></div>
      <div id="run-status" class="muted" role="status" aria-live="polite">Ready. Press Start or move the timeline.</div>
      <div class="grid"><section class="panel"><h2>Inside the engine bay</h2><p class="muted">Stationary schematic. Colours show calculated temperatures.</p>
      <p class="swipe-note">Swipe the diagram to follow the sensor-to-ECU path.</p><div class="diagram-scroll" tabindex="0" aria-label="Scrollable engine schematic"><svg class="schematic" viewBox="0 0 740 330" role="img" aria-labelledby="diagram-title diagram-desc"><title id="diagram-title">Coolant sensor and ECU signal chain</title><desc id="diagram-desc">Applied coolant heats the sensor. Its resistance changes the divider voltage, which the ECU converts to an ADC count and temperature estimate.</desc>
        <path d="M24 270V78Q24 49 55 49H430Q457 49 457 78V270" fill="#f4f7fa" stroke="#c6d3db" stroke-width="2"/>
        <text x="43" y="78" fill="#526977" font-size="13">ENGINE BAY / simplified cutaway</text>
        <rect x="67" y="120" width="225" height="125" rx="18" fill="#e5ebef" stroke="#8095a2" stroke-width="2"/>
        <path d="M94 135h163M94 154h163M94 173h163" stroke="#c0cdd5" stroke-width="6"/>
        <text x="92" y="211" fill="#18364b" font-size="16" font-weight="600">Engine coolant</text><text id="tc-label" x="92" y="232" fill="#18364b" font-size="14">20.00 C</text>
        <path id="coolant-path" d="M40 292H327V223H292" fill="none" stroke="#3c98d4" stroke-width="16" stroke-linejoin="round"/>
        <text x="47" y="318" fill="#526977" font-size="12">Colour = applied coolant temperature</text>
        <rect x="300" y="173" width="55" height="46" rx="6" fill="#354e5e"/><circle id="sensor" cx="327" cy="222" r="17" fill="#3c98d4" stroke="#18364b" stroke-width="3"/>
        <path d="M329 172V139" stroke="#526977" stroke-width="2"/><text x="294" y="115" fill="#18364b" font-size="14" font-weight="650">ECT sensor</text><text id="ts-label" x="293" y="134" fill="#526977" font-size="13">Ts = 20.00 C</text>
        <path class="signal" d="M357 195H509" stroke="#c36c13" stroke-width="4" fill="none"/><path d="M503 189l11 6-11 6" fill="#c36c13"/>
        <text x="390" y="174" fill="#80500a" font-size="12">Voltage signal</text><text id="voltage-label" x="401" y="219" fill="#18364b" font-size="14">2.786 V</text>
        <rect x="518" y="112" width="195" height="148" rx="16" fill="#e7f1f5" stroke="#50839a" stroke-width="2"/><text x="541" y="145" fill="#145d7a" font-size="18" font-weight="700">ECU</text>
        <text id="adc-label" x="541" y="177" fill="#18364b" font-size="14">ADC 2282</text><text id="estimate-label" x="541" y="205" fill="#18364b" font-size="15" font-weight="650">20.00 C</text><text id="estimate-state" x="541" y="233" fill="#1b6049" font-size="12">Valid conversion</text>
      </svg></div><div class="temperature-gradient"></div><p id="colour-scale" class="chart-note"></p><p class="chart-note">Dashed motion illustrates signal activity. No coolant-flow rate or moving-car physics is implied.</p><div id="input-status" class="status"></div><div id="conversion-status" class="status"></div>
      </section><section class="panel"><h2>Sensor and ECU readings</h2><div class="metrics">${[
        ['Coolant_Input_C','Applied coolant','C'],['Sensor_Temperature_C','Sensor temperature','C'],['Reconstructed_Temperature_C','ECU estimate','C'],
        ['Thermistor_Resistance_Ohm','Thermistor resistance','ohm'],['ECT_Voltage_V','Analogue voltage','V'],['ADC_Count','ADC count','counts'],['Conversion_Error_C','Conversion error','C']
      ].map(([key,label,unit])=>`<div class="metric"><span>${label}</span><strong data-value="${key}">--</strong><em>${unit}</em></div>`).join('')}</div><p id="fallback-note" class="error"></p><p class="muted">Error = ECU estimate minus sensor temperature. Sensor lag is separate from ADC quantization error.</p></section></div>
      <label class="timeline">Simulation time<input id="timeline" aria-label="Simulation time" type="range" min="0" max="12000" step="1" value="0"><output id="time-value">0.00 / 120 s</output></label>
      <div class="plots">${PLOTS.map((p,i)=>`<section class="panel plot"><h3>${p.title}</h3><div class="legend">${p.series.map(([,name,color])=>`<span><i style="background:${color}"></i>${name}</span>`).join('')}</div><svg data-plot="${i}" viewBox="0 0 600 210" role="img" aria-label="${p.title} over simulation time"></svg><p class="chart-note">${p.unit} / time (s). Computed samples through the selected time.</p></section>`).join('')}</div>
      <details><summary>Experiment settings and calibration</summary><p class="muted">Edits take effect together when you select Apply. This resets the experiment. Yellow blocks in Simulink correspond to these settings.</p><form id="settings"><div class="settings"><label>Input mode<select data-setting="inputMode" aria-label="Input mode"><option value="0">Fixed coolant</option><option value="1">Step profile</option></select></label>${fieldHTML}</div><div class="settings-actions"><button class="primary" type="submit">Apply and reset</button><button id="defaults" type="button">Restore defaults</button><span id="settings-error" class="error" role="alert"></span></div></form></details>
      <footer class="foot"><b>Model boundary:</b> ideal first-order sensor, NTC resistor, voltage divider and ADC reconstruction. No combustion, vehicle speed, fan control, noise or fault injection. <a href="${SOURCE.chat}" target="_blank" rel="noopener noreferrer">Source chat snapshot</a>. <span>Logic v${VERSION}.</span></footer>
    </section>`;
    function fillSettings(){for(const [key,value] of Object.entries(run.config)){const el=q(`[data-setting="${key}"]`);if(el)el.value=String(value);}q('#timeline').max=String(run.samples.length-1);}
    function colour(t){const f=clamp((t-run.config.minTempC)/(run.config.maxTempC-run.config.minTempC),0,1);return `hsl(${220-210*f} 62% 49%)`;}
    const format=(n,places=2)=>Number.isFinite(n)?n.toFixed(places):'Invalid';
    function drawPlots(){
      const rows=run.samples.slice(0,index+1), selected=run.samples[index];
      for(let i=0;i<PLOTS.length;i++){
        const p=PLOTS[i], all=p.series.flatMap(([key])=>rows.map(r=>r[key]));
        let lo=Infinity,hi=-Infinity;for(const v of all){lo=Math.min(lo,v);hi=Math.max(hi,v);}
        const pad=Math.max((hi-lo)*.12,Math.abs(hi)*.02,.01);lo-=pad;hi+=pad;
        const small=q(`[data-plot="${i}"]`).clientWidth<420,left=small?110:65,font=small?20:12;
        const x=t=>left+t/run.config.stopTimeS*(580-left),y=v=>170-(v-lo)/(hi-lo)*140;
        const num=v=>Math.abs(v)<1e-12?'0':Math.abs(v)>=10000?v.toExponential(1):Math.abs(v)<.1?v.toFixed(3):v.toFixed(1);
        let svg='';for(let j=0;j<4;j++){const yy=30+j*140/3;svg+=`<line x1="${left}" x2="580" y1="${yy}" y2="${yy}" stroke="#e1e9ee"/><text x="${left-8}" y="${yy+font/3}" text-anchor="end" font-size="${font}" fill="#526977">${num(hi-j*(hi-lo)/3)}</text>`;}
        for(let j=0;j<=4;j++){const tt=j*run.config.stopTimeS/4;svg+=`<text x="${x(tt)}" y="198" text-anchor="middle" font-size="${font}" fill="#526977">${num(tt)}</text>`;}
        svg+=`<line x1="${left}" x2="580" y1="170" y2="170" stroke="#94aab7"/>`;
        p.series.forEach(([key,,color],seriesIndex)=>{const rowsToDraw=plotPoints(rows,key);const points=rowsToDraw.map(r=>`${x(r.timeS).toFixed(2)},${y(r[key]).toFixed(2)}`).join(' ');svg+=`<polyline points="${points}" fill="none" stroke="${color}" stroke-width="${seriesIndex?1.6:2}"${seriesIndex===2?' stroke-dasharray="5 3"':''}/><circle cx="${x(selected.timeS)}" cy="${y(selected[key])}" r="2.3" fill="${color}"/>`;});
        q(`[data-plot="${i}"]`).innerHTML=svg;
      }
    }
    function render(charts=true){
      const s=run.samples[index];q('#timeline').value=String(index);q('#time-value').textContent=`${s.timeS.toFixed(2)} / ${run.config.stopTimeS} s`;
      q('#timeline').setAttribute('aria-valuetext',`${s.timeS.toFixed(2)} seconds`);
      for(const el of ui.querySelectorAll('[data-value]')){const key=el.dataset.value;el.textContent=format(s[key],key==='ADC_Count'?0:key==='ECT_Voltage_V'||key==='Conversion_Error_C'?4:2);}
      q('#tc-label').textContent=`Tc = ${format(s.Coolant_Input_C)} C`;q('#ts-label').textContent=`Ts = ${format(s.Sensor_Temperature_C)} C`;
      q('#voltage-label').textContent=`${format(s.ECT_Voltage_V,3)} V`;q('#adc-label').textContent=`ADC ${s.ADC_Count} / ${run.config.adcMaxCount}`;
      q('#estimate-label').textContent=`${format(s.Reconstructed_Temperature_C)} C`;
      q('#coolant-path').setAttribute('stroke',colour(s.Coolant_Input_C));q('#sensor').setAttribute('fill',colour(s.Sensor_Temperature_C));
      q('#colour-scale').textContent=`Temperature scale: ${run.config.minTempC} C (blue) to ${run.config.maxTempC} C (red).`;
      q('#input-status').textContent=s.Input_Valid_Status?'Input VALID - requested coolant is within limits.':`Input CLAMPED - requested ${format(s.Requested_Coolant_C)} C; applied ${format(s.Coolant_Input_C)} C.`;
      q('#input-status').className=s.Input_Valid_Status?'status':'status warn';
      q('#conversion-status').textContent=s.Conversion_Valid_Status?'Conversion VALID - ADC is between its rails.':'Conversion INVALID - ADC at a rail; temperature shown is a guarded fallback.';
      q('#conversion-status').className=s.Conversion_Valid_Status?'status':'status bad';
      q('#estimate-state').textContent=s.Conversion_Valid_Status?'Valid conversion':'FALLBACK / INVALID';q('#estimate-state').setAttribute('fill',s.Conversion_Valid_Status?'#1b6049':'#922b22');
      q('#fallback-note').textContent=s.Conversion_Valid_Status?'':'ECU estimate is a fallback, not a valid measurement.';
      if(charts)drawPlots();
      host.dispatchEvent(new win.CustomEvent('ect:sample',{detail:s,bubbles:true,composed:true}));
    }
    function pause(message='Paused.'){playing=false;win.cancelAnimationFrame(raf);lastStamp=null;q('#play').textContent='Start';q('.lab').classList.remove('running');q('#run-status').textContent=message;}
    function frame(stamp){
      if(!playing||disposed)return;
      if(lastStamp!==null){const elapsed=Math.max(0,Math.min((stamp-lastStamp)/1000,.25));playTime=Math.min(run.config.stopTimeS,playTime+elapsed*Number(q('#speed').value));}
      lastStamp=stamp;index=Math.min(run.samples.length-1,Math.floor((playTime+1e-10)/run.config.dtS));
      const charts=stamp-lastChart>=100||index===run.samples.length-1;render(charts);if(charts)lastChart=stamp;
      if(index===run.samples.length-1){pause('Complete. Reset or select another experiment.');return;}raf=win.requestAnimationFrame(frame);
    }
    function start(){if(disposed)return;if(index===run.samples.length-1){index=0;playTime=0;render();}if(playing)return;playing=true;lastStamp=null;q('#play').textContent='Pause';q('.lab').classList.add('running');q('#run-status').textContent='Running - playback speed does not change the computed results.';raf=win.requestAnimationFrame(frame);}
    function setConfig(c){insist(!disposed,'DISPOSED','This interface has been destroyed.');const next=simulate(c);pause('Ready - settings applied and experiment reset.');run=next;index=0;playTime=0;fillSettings();q('#settings-error').textContent='';render();return run.config;}
    function seek(t){insist(Number.isFinite(t),'TIME','Seek time must be finite.');pause('Paused at selected time.');index=Math.round(clamp(t,0,run.config.stopTimeS)/run.config.dtS);playTime=run.samples[index].timeS;render();return run.samples[index];}
    q('#play').onclick=()=>playing?pause():start();q('#reset').onclick=()=>seek(0);
    q('#timeline').oninput=()=>seek(Number(q('#timeline').value)*run.config.dtS);
    q('#preset').onchange=()=>{const key=q('#preset').value;if(PRESETS[key])setConfig(PRESETS[key].config);};
    q('#settings').onsubmit=event=>{event.preventDefault();try{const c={};for(const el of ui.querySelectorAll('[data-setting]'))c[el.dataset.setting]=el.value.trim()===''?NaN:Number(el.value);setConfig(c);q('#preset').value='custom';}catch(e){pause('Settings were not applied. Correct the highlighted message.');q('#settings-error').textContent=e.message;}};
    q('#defaults').onclick=()=>{setConfig({});q('#preset').value='heating';};
    q('#export').onclick=()=>{const url=win.URL.createObjectURL(new win.Blob([toCSV(run)],{type:'text/csv;charset=utf-8'}));const a=doc.createElement('a');a.href=url;a.download='Amachie_ECT_run.csv';doc.body.appendChild(a);a.click();a.remove();win.setTimeout(()=>win.URL.revokeObjectURL(url),1000);q('#run-status').textContent=`Exported ${run.samples.length} computed samples with status flags.`;};
    const visibility=()=>{if(doc.hidden&&playing)pause('Paused because this page was hidden. Press Start to resume.');};doc.addEventListener('visibilitychange',visibility);
    const motion=()=>q('.lab').classList.toggle('reduced',reduced.matches);reduced.addEventListener('change',motion);motion();
    fillSettings();if(Object.keys(overrides).length)q('#preset').value='custom';render();
    return Object.freeze({host,start,pause,seek,setConfig,
      get snapshot(){return run.samples[index];},get config(){return run.config;},get playing(){return playing;},
      exportCSV:()=>toCSV(run),
      destroy(){if(disposed)return;pause();disposed=true;doc.removeEventListener('visibilitychange',visibility);reduced.removeEventListener('change',motion);host.remove();}
    });
  }
  const api = { VERSION, SOURCE, DEFAULTS, OUTPUTS, MAX_INTERVALS, ECTError,
    validateConfig, createEngine, simulate, toCSV, verifyReferenceCSV, selfTest, CODEX_BRIEF, PRESETS, mount };
  return Object.freeze(api);
});

if(typeof module==='object' && module.exports && typeof require==='function' && require.main===module){
  const E=module.exports, fs=require('node:fs');
  try{
    const args=process.argv.slice(2);
    if(args[0]==='--self-test'&&args.length===1)console.log(JSON.stringify(E.selfTest(),null,2));
    else if(args[0]==='--verify-csv'&&args.length===2)console.log(JSON.stringify(E.verifyReferenceCSV(fs.readFileSync(args[1],'utf8')),null,2));
    else if(args[0]==='--brief'&&args.length===1)console.log(E.CODEX_BRIEF);
    else if(args[0]==='--demo'&&args.length===2){
      const source=fs.readFileSync(__filename,'utf8').replace(/<\/script/gi,'<\\/script');
      const html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amachie ECT Virtual Lab</title><style>body{margin:0;padding:24px;background:#e9f0f4}@media(max-width:560px){body{padding:0}}</style></head><body><main id="ect-lab"></main><script>'+source+'</script><script>globalThis.ectLab=AmachieECT.mount(document.getElementById("ect-lab"));</script></body></html>';
      fs.writeFileSync(args[1],html,{flag:'wx'});console.log('Created offline demonstration: '+args[1]);
    }else if(args.length===0)console.log('Amachie ECT v'+E.VERSION+'\nCommands: --self-test | --verify-csv PATH | --brief | --demo NEW_OUTPUT.html');
    else throw new Error('Unknown command or missing argument. Use --self-test, --verify-csv PATH, --brief, or --demo NEW_OUTPUT.html.');
  }catch(error){console.error((error.code?error.code+': ':'')+error.message);process.exitCode=1;}
}
