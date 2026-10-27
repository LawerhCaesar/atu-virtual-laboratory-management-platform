import {FIELDS,OUTPUTS,DEFAULT_BRAKE_INPUTS,DEFAULT_BRAKE_CALIBRATION,validateInputs} from "./model.mjs";
import {BrakeSimulation} from "./controller.mjs";
import {nudgeValue,sliderBounds} from "../fuel-delivery/controls.mjs";

const root=document.getElementById("brakelab");
if (root) initialise();
function initialise() {
  const byId=id=>document.getElementById(id);
  const make=(tag,text,css)=>{ const e=document.createElement(tag); if(text!==undefined)e.textContent=text; if(css)e.className=css; return e; };
  const sim=new BrakeSimulation(), controls={}, cells={};
  let draft={...DEFAULT_BRAKE_INPUTS}, valid=true, dirty=false, frameId, lastNow=0, stopped=false;
  const media=matchMedia("(prefers-reduced-motion: reduce)"), motion=byId("brake-motion"), live=byId("brake-live");
  motion.checked=!media.matches;
  let groupName="", group;
  for(const f of FIELDS) {
    if(f.group!==groupName) { groupName=f.group; group=make("fieldset"); group.append(make("legend",f.group)); byId("brake-input-fields").append(group); }
    const box=make("div",undefined,"fuel-input"), label=make("label",`${f.label}${f.unit ? ` (${f.unit})` : ""}`), input=make("input");
    input.id=`brake-input-${f.key}`; label.htmlFor=input.id;
    const error=make("small","","fuel-field-error"); error.id=`brake-error-${f.key}`;
    const help=make("small",typeof f.value==="boolean" ? f.purpose : `Suggested: ${f.min}–${f.max} ${f.unit}. Baseline: ${f.value}.`); help.id=`brake-help-${f.key}`;
    input.setAttribute("aria-describedby",`${help.id} ${typeof f.value==="boolean" ? "" : `brake-purpose-${f.key} `}${error.id}`);
    if(typeof f.value==="boolean") {
      input.type="checkbox"; input.checked=f.value; input.className="form-check-input me-2";
      input.addEventListener("change",()=>{draft[f.key]=input.checked; changed();});
      box.append(input,label,help,error); controls[f.key]={input};
    } else {
      input.type="number"; input.step="any"; input.inputMode=f.step<1 ? "decimal" : "numeric"; input.value=f.value; input.className="form-control";
      const row=make("div",undefined,"fuel-number"), slider=make("input");
      slider.type="range"; slider.step="any"; slider.className="form-range";
      slider.setAttribute("aria-label",`${f.label} slider`);
      const purpose=make("small",f.purpose); purpose.id=`brake-purpose-${f.key}`;
      const guide=make("details",undefined,"fuel-field-guide"); guide.append(make("summary",`About ${f.label.toLowerCase()}`),purpose);
      slider.setAttribute("aria-describedby",`${help.id} ${purpose.id}`);
      const syncSlider=value=>{
        const bounds=sliderBounds(f,value); slider.min=bounds.min; slider.max=bounds.max;
        slider.value=Number.isFinite(value) ? value : f.value; slider.disabled=!Number.isFinite(value)||Math.abs(value)>1e6;
        slider.setAttribute("aria-valuetext",slider.disabled ? "Outside slider scale; use numeric entry." : `${value} ${f.unit}`);
      };
      const set=value=>{draft[f.key]=value; input.value=value; syncSlider(value); changed();};
      for(const [text,verb,direction] of [["−","Decrease",-1],["+","Increase",1]]) {
        const button=make("button",text,"btn btn-outline-secondary"); button.type="button";
        button.setAttribute("aria-label",`${verb} ${f.label}`); button.addEventListener("click",()=>set(nudgeValue(f,draft[f.key],direction))); row.append(button);
      }
      row.insertBefore(input,row.lastChild);
      input.addEventListener("input",()=>{draft[f.key]=input.value==="" ? NaN : Number(input.value); syncSlider(draft[f.key]); changed();});
      slider.addEventListener("input",()=>set(Number(slider.value)));
      box.append(label,row,slider,help,guide,error); controls[f.key]={input,syncSlider}; syncSlider(f.value);
    }
    group.append(box);
  }
  const primary=new Set(["requestedDecelerationMps2","requestedForceN","regenerativeForceN","frictionForceN","regenerativePercent","frictionPercent","batteryChargePowerKw","regenerativeCurrentA","motorSpeedRpm"]);
  for(const [key,label,unit] of OUTPUTS) {
    if(key==="forceBalanceResidualN")continue;
    const box=make("div"), dd=make("dd","—"); dd.dataset.brakeOutput=key;
    box.append(make("dt",`${label} (${unit})`),dd); byId(primary.has(key) ? "brake-kpis" : "brake-details").append(box); cells[key]=dd;
  }
  const calibrationLabels={maxServiceDecelMps2:"Maximum service deceleration (m/s²)",wheelRadiusM:"Wheel radius (m)",gearRatio:"Gear ratio",
    drivetrainEfficiency:"Drivetrain efficiency",regenEfficiency:"Regenerative efficiency",speedCutoffMps:"Speed cut-off (m/s)",fullRegenSpeedMps:"Full regeneration speed (m/s)",
    socDeratePct:"SOC derating (%)",socStopPct:"SOC stop (%)",coldCutoffC:"Cold cut-off (°C)",coldFullC:"Cold full acceptance (°C)",
    hotFullC:"Hot full acceptance (°C)",hotCutoffC:"Hot cut-off (°C)",minimumSpeedMps:"Minimum calculation speed (m/s)",forceEpsilonN:"Force epsilon (N)"};
  for(const [key,value] of Object.entries(DEFAULT_BRAKE_CALIBRATION)) byId("brake-calibration").append(make("dt",calibrationLabels[key]),make("dd",String(value)));
  function syncInputs() { for(const f of FIELDS) { const c=controls[f.key]; if(typeof f.value==="boolean")c.input.checked=draft[f.key]; else {c.input.value=draft[f.key];c.syncSlider(draft[f.key]);} } }
  function fail(error) { sim.fail(error); valid=false; byId("brake-validation").hidden=false; byId("brake-validation").textContent=`${error.message} Last-valid readings are shown; correct inputs or Reset. Exports are blocked.`; render(); }
  function guarded(action) { try { action(); } catch(error) { fail(error); } }
  function changed() {
    sim.pause(); dirty=true; const status=validateInputs(draft); valid=status.valid;
    for(const f of FIELDS) { byId(`brake-error-${f.key}`).textContent=status.errors[f.key]||""; controls[f.key].input.setAttribute("aria-invalid",String(Boolean(status.errors[f.key]))); }
    byId("brake-validation").hidden=valid;
    byId("brake-validation").textContent=valid ? "" : "Correct the marked inputs. Last-valid readings are shown; Run and export are blocked.";
    if(valid && live.checked) {
      try { sim.calculate(draft); dirty=false; } catch(error) { fail(error); }
    }
    render();
  }
  byId("brake-run").addEventListener("click",()=>{ if(valid)guarded(()=>{sim.run(draft,motion.checked);dirty=false;lastNow=0;render();}); });
  byId("brake-reset").addEventListener("click",()=>{draft={...DEFAULT_BRAKE_INPUTS};sim.reset();syncInputs();changed();dirty=false;render();});
  byId("brake-pause").addEventListener("click",()=>{sim.pause();render();});
  byId("brake-resume").addEventListener("click",()=>{if(valid&&!dirty&&motion.checked){sim.resume();lastNow=0;render();}});
  live.addEventListener("change",changed);
  motion.addEventListener("change",()=>{if(!motion.checked)sim.pause();render();});
  const preferenceChanged=()=>{if(media.matches){motion.checked=false;sim.pause();render();}};
  media.addEventListener("change",preferenceChanged);
  byId("brake-export").addEventListener("click",()=>{
    if(!valid||dirty)return;
    guarded(()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(sim.payload(),null,2)],{type:"application/json"})), link=make("a");
      link.href=url; link.download="brakelab.json"; document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  });
  function chart(container,values,unit,maximum,minimum=-1) {
    const box=byId(container); box.replaceChildren();
    values.forEach(([key,label,value],index)=>{
      const row=make("div",undefined,"brake-chart-row"); row.dataset.minimum=String(index===minimum); row.dataset.brakeChart=key;
      const caption=`${label}: ${value.toFixed(unit==="ratio" ? 3 : unit==="N" ? 1 : 2)} ${unit}${index===minimum ? " · smallest candidate" : ""}`;
      row.append(make("p",caption)); const bar=make("progress");
      // Normalize bar geometry only, retaining full physical values in text and JSON.
      bar.max=1; bar.value=value/Math.max(maximum,Number.MIN_VALUE); bar.setAttribute("aria-label",label);bar.setAttribute("aria-valuetext",caption);
      row.append(bar); box.append(row);
    });
  }
  function render() {
    const r=sim.result;
    byId("brake-mode").textContent=!valid ? `${sim.error ? "Calculation" : "Input"} error · paused` : dirty ? "Draft changed · Run Model required" : sim.mode;
    byId("brake-run").disabled=!valid;
    byId("brake-export").disabled=!valid||dirty||Boolean(sim.error);
    byId("brake-pause").disabled=!sim.running;
    byId("brake-resume").disabled=!valid||dirty||sim.running||!motion.checked||!sim.hasRun||sim.elapsedS>=r.visual.animationDurationS;
    byId("brake-result-note").textContent=!valid||dirty ? "Last calculated operating point; it does not represent the changed draft." : "Values describe the selected operating point and stay fixed during the illustrative playback.";
    for(const [key,, ,precision] of OUTPUTS) if(cells[key])cells[key].textContent=r[key].toFixed(precision);
    byId("brake-limit").textContent=`Active limit: ${r.activeLimitLabel}${r.requestedForceN>0 && r.requestedForceN<=DEFAULT_BRAKE_CALIBRATION.forceEpsilonN ? " · demand at or below the 1 N diagnostic threshold" : ""}`;
    byId("brake-limit").dataset.code=r.activeLimitCode;
    const balanced=Math.abs(r.forceBalanceResidualN)<.001;
    byId("brake-balance").textContent=`Force-balance residual: ${r.forceBalanceResidualN.toExponential(3)} N · ${balanced ? "Verified (<0.001 N)" : "Outside tolerance"}`;
    byId("brake-balance").dataset.valid=String(balanced);
    byId("brake-warnings").replaceChildren(...r.warnings.map(w=>make("li",w)));
    const tiny=r.requestedForceN>0&&r.requestedForceN<DEFAULT_BRAKE_CALIBRATION.forceEpsilonN;
    byId("brake-share-note").textContent=tiny ? "Below 1 N: protected percentages use a 1 N denominator, so they need not total 100%. No renormalisation is applied." : r.requestedForceN===0 ? "No braking demand; both allocation shares are zero." : "Solid green = regeneration; striped amber = friction.";
    byId("brake-share-label").textContent=`Regenerative ${r.regenerativePercent.toFixed(1)}% · Friction ${r.frictionPercent.toFixed(1)}%`;
    byId("brake-allocation").setAttribute("aria-label",byId("brake-share-label").textContent);
    byId("brake-regen-share").style.width=`${r.regenerativePercent}%`; byId("brake-friction-share").style.width=`${r.frictionPercent}%`;
    const forces=[["requestedForceN","Requested force",r.requestedForceN],["torqueForceLimitN","Motor torque limit",r.torqueForceLimitN],
      ["powerForceLimitN","Motor power limit",r.powerForceLimitN],["batteryForceLimitN","Battery limit",r.batteryForceLimitN]];
    const lowest=Math.min(...forces.map(v=>v[2]));
    chart("brake-force-chart",forces,"N",Math.max(...forces.map(v=>v[2])),forces.findIndex(v=>v[2]===lowest));
    chart("brake-factor-chart",[["speedFactor","Speed",r.speedFactor],["socFactor","SOC",r.socFactor],["temperatureFactor","Temperature",r.temperatureFactor]],"ratio",1);
    const powers=[["mechanicalRegenPowerKw","Mechanical regenerative",r.mechanicalRegenPowerKw],["allowedBatteryPowerKw","Allowed battery",r.allowedBatteryPowerKw],["batteryChargePowerKw","Actual battery charging",r.batteryChargePowerKw]];
    chart("brake-power-chart",powers,"kW",Math.max(...powers.map(v=>v[2])));
    byId("brake-explanation").textContent=`${r.activeLimitLabel}. Requested ${r.requestedForceN.toFixed(1)} N; candidates are torque ${r.torqueForceLimitN.toFixed(1)} N, motor power ${r.powerForceLimitN.toFixed(1)} N and battery ${r.batteryForceLimitN.toFixed(1)} N. Speed factor ${r.speedFactor.toFixed(3)}, SOC factor ${r.socFactor.toFixed(3)} and temperature factor ${r.temperatureFactor.toFixed(3)} act separately. Regeneration receives the permitted minimum when enabled; friction supplies ${r.frictionForceN.toFixed(1)} N of remainder. A changed limit need not change allocation when another limit still controls.`;
    byId("brake-stop-estimate").textContent=r.requestedDecelerationMps2===0 && r.vehicleSpeedMps>0 ? "No braking: no finite stopping estimate. Zero values in the reference payload are sentinels, not an instantaneous stop. Playback is off." : `Constant-deceleration estimates: stop time ${r.visual.stopTimeEstimateS.toFixed(2)} s; stop distance ${r.visual.stopDistanceEstimateM.toFixed(2)} m. Screen playback ${r.visual.animationDurationS.toFixed(2)} s. These are visual estimates, not validated vehicle stopping performance.`;
    drawFrame();
  }
  function drawFrame() {
    const f=sim.frame();
    byId("brake-speed").textContent=f.speedKph.toFixed(1); byId("brake-playback-time").textContent=sim.elapsedS.toFixed(2); byId("brake-playback-duration").textContent=sim.result.visual.animationDurationS.toFixed(2);
    byId("brake-scene").dataset.progress=f.progress.toFixed(5);
    byId("brake-car").setAttribute("transform",`translate(${30+110*f.progress*(2-f.progress)} 0)`);
    byId("brake-wheel-left").setAttribute("transform",`rotate(${f.wheelAngleDeg} 170 245)`);
    byId("brake-wheel-right").setAttribute("transform",`rotate(${f.wheelAngleDeg} 455 245)`);
    byId("brake-friction-glow").setAttribute("opacity",String(f.frictionIntensity*.7));
    byId("brake-wheel-flow").setAttribute("opacity",String(f.regenIntensity)); byId("brake-wheel-flow").setAttribute("stroke-dashoffset",String(-sim.elapsedS*15));
    byId("brake-charge-flow").setAttribute("opacity",String(f.chargeIntensity)); byId("brake-charge-flow").setAttribute("stroke-dashoffset",String(-sim.elapsedS*12));
  }
  function animate(now) {
    const dt=lastNow ? Math.min((now-lastNow)/1000,.05) : 0; lastNow=now;
    if(sim.running && motion.checked && valid && !dirty && !document.hidden) {
      try { const wasRunning=sim.running;sim.tick(dt);drawFrame();if(wasRunning&&!sim.running)render(); } catch(error) {fail(error);}
    }
    frameId=requestAnimationFrame(animate);
  }
  document.addEventListener("visibilitychange",()=>{if(document.hidden){sim.pause();render();}});
  window.addEventListener("pagehide",()=>{stopped=true;sim.pause();cancelAnimationFrame(frameId);});
  window.addEventListener("pageshow",event=>{if(event.persisted&&stopped){stopped=false;lastNow=0;render();frameId=requestAnimationFrame(animate);}});
  render();frameId=requestAnimationFrame(animate);
}
