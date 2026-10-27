import {FIELDS,DEFAULTS,calculateMicroHybridStopStart} from './model.mjs';
const $=id=>document.getElementById(id), root=$('micro-hybrid');
if(root) {
  const inputs={}, saved=[]; let values={...DEFAULTS}, result=null, timer=null, step=0, stopIndex=0;
  const el=(tag,text,cls)=>{const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n;};
  const kpis=[['fuelReductionPct','Fuel reduction','%'],['fuelSavedG','Fuel saved','g'],['totalEngineOffTimeS','Engine-off time','s'],['finalBatterySocPct','Final battery SOC','%'],['restartCount','Restarts',''],['breakEvenStopTimeS','Break-even stop','s']];
  const purpose={stopDurationS:'Stationary time per traffic stop.',numberOfStops:'Number of stops in the same route.',initialSocPct:'Battery charge before the scenario.',accessoryLoadW:'Electrical demand supported during an accepted stop.',minimumStopTimeS:'Controller minimum duration for considering engine shutdown.',movingFuelG:'Fuel used while moving; identical in both cases.',idleFuelRateGps:'Conventional fuel consumed per second of idling.',restartFuelPerStartG:'Additional fuel for each restart.',batteryNominalVoltageV:'Nominal voltage used to convert energy to SOC change.',batteryCapacityAh:'Battery capacity used for the SOC estimate.',batteryInternalResistanceOhm:'Resistance used in crank and accessory voltage estimates.',crankingCurrentA:'Current used to estimate the restart voltage drop.',minimumCrankVoltageV:'Lowest predicted cranking voltage for an accepted stop.',minimumSocPct:'Minimum initial battery charge for an accepted stop.',maximumAccessoryLoadW:'Maximum accessory load permitted during engine-off operation.',startEnergyJPerRestart:'Electrical starting energy per accepted restart.',batteryEfficiency:'Efficiency factor for recovering battery energy.',alternatorEfficiency:'Efficiency factor for conversion from engine to electricity.',engineEfficiency:'Efficiency factor for converting fuel energy to mechanical energy.',fuelLhvJPerKg:'Fuel energy per kilogram used for the recharge fuel equivalent.'};
  const fmt=v=>v===null?'No finite point':Number(v).toFixed(2);
  for(const [index,[key,label,unit,def,min,max]] of FIELDS.entries()) {
    const wrap=el('div',undefined,'fuel-input'), l=el('label',`${label} (${unit})`), row=el('div',undefined,'fuel-number');
    const n=el('input'); n.id=`micro-input-${key}`; n.type='number'; n.step='any'; n.className='form-control'; n.value=def; l.htmlFor=n.id;
    const help=el('small',`${purpose[key]} Suggested: ${min}–${max} ${unit}. Default: ${def}.${index<6?' The slider is unavailable outside that range; you can still type research values.':''}`); help.id=`micro-help-${key}`; n.setAttribute('aria-describedby',help.id);
    const delta=key==='numberOfStops'?1:(max-min || 1)/20;
    const left=el('button','−','btn btn-outline-secondary'),right=el('button','+','btn btn-outline-secondary');
    for(const [button,dir,name] of [[left,-1,'Decrease'],[right,1,'Increase']]) {button.type='button';button.setAttribute('aria-label',`${name} ${label}`);button.addEventListener('click',()=>{const v=Number(n.value); n.value=Number((v+delta*dir).toPrecision(10)); update();});}
    n.addEventListener('input',update); row.append(left,n,right); wrap.append(l,row);
    if(index<6) {const slider=el('input'); slider.type='range'; slider.className='form-range';slider.min=min;slider.max=max;slider.step='any';slider.value=def;slider.setAttribute('aria-label',`${label} slider`);slider.setAttribute('aria-describedby',help.id);slider.addEventListener('input',()=>{n.value=key==='numberOfStops'?Math.round(Number(slider.value)):Number(slider.value).toFixed(2);update();});n._slider=slider;wrap.append(slider);}
    wrap.append(help); $(index<6?'micro-basic':'micro-advanced').append(wrap); inputs[key]=n;
  }
  function pause(){clearInterval(timer);timer=null;$('micro-play').disabled=false;$('micro-pause').disabled=true;}
  function bar(container,label,value,max,unit) { const wrap=el('div',undefined,'micro-bar'), caption=el('span',`${label}: ${fmt(value)} ${unit}`), p=el('progress');p.max=Math.max(1,max,value);p.value=Math.max(0,value);p.setAttribute('aria-label',`${label}: ${fmt(value)} ${unit}`);wrap.append(caption,p);container.append(wrap); }
  function update() {
    pause(); for(const [key,input] of Object.entries(inputs)) {values[key]=input.value.trim()===''?NaN:Number(input.value);if(input._slider){input._slider.disabled=!Number.isFinite(values[key])||values[key]<Number(input._slider.min)||values[key]>Number(input._slider.max);if(!input._slider.disabled) input._slider.value=values[key];}}
    try {result=calculateMicroHybridStopStart(values); $('micro-error').hidden=true;} catch(error) {result=null;$('micro-error').hidden=false;$('micro-error').textContent=`${error.message} Correct the input to update the results.`;}
    for(const id of ['micro-save','micro-export','micro-play','micro-replay']) $(id).disabled=!result;
    if(!result) { $('micro-status').textContent='Input needs attention'; $('micro-status').removeAttribute('data-permitted'); $('micro-reason').textContent='Results unavailable until inputs are corrected.'; $('micro-failed').replaceChildren(); $('micro-warnings').replaceChildren(); $('micro-stage').textContent='Input needs attention'; $('micro-engine').textContent='Engine state unavailable'; $('micro-battery').textContent='Battery state unavailable'; $('micro-play-progress').textContent='Correct the input to restore the illustration.'; $('micro-kpis').replaceChildren(); $('micro-charts').replaceChildren(); $('micro-formulas').replaceChildren(); return; }
    const o=result; $('micro-status').textContent=o.stopPermission?'Automatic stop permitted':'Automatic stop inhibited'; $('micro-status').dataset.permitted=String(o.stopPermission);
    $('micro-reason').textContent=`Code ${o.inhibitCode} · ${o.inhibitMessage}`;
    $('micro-failed').replaceChildren(...o.failedConditions.map(x=>el('li',x))); $('micro-warnings').replaceChildren(...o.warnings.map(x=>el('li',x)));
    const grid=$('micro-kpis'); grid.replaceChildren(); for(const [key,label,unit] of kpis) {const box=el('div'),dt=el('dt',`${label}${unit?` (${unit})`:''}`),dd=el('dd',fmt(o[key]));dd.dataset.microOutput=key;box.append(dt,dd);grid.append(box);}
    const chart=$('micro-charts'); chart.replaceChildren();
    chart.append(el('h3','Fuel comparison','h5 mt-4')); const fuelMax=Math.max(o.conventionalFuelG,o.microHybridFuelG,1);
    bar(chart,'Conventional fuel',o.conventionalFuelG,fuelMax,'g');bar(chart,'Micro-hybrid fuel',o.microHybridFuelG,fuelMax,'g');
    chart.append(el('h3','Fuel accounting','h5 mt-4'));
    const waterfall=el('div',undefined,'micro-waterfall'), scale=Math.max(o.idleFuelAvoidedG,1);
    waterfall.setAttribute('role','img'); waterfall.setAttribute('aria-label',`Fuel accounting: ${fmt(o.idleFuelAvoidedG)} g idle fuel avoided, less ${fmt(o.restartFuelPenaltyG)} g restart fuel and ${fmt(o.rechargeFuelPenaltyG)} g recharge fuel, leaves ${fmt(o.fuelSavedG)} g saved.`);
    for(const [label,low,high,kind] of [['Avoided',0,o.idleFuelAvoidedG,'gain'],['Restart',o.idleFuelAvoidedG-o.restartFuelPenaltyG,o.idleFuelAvoidedG,'penalty'],['Recharge',o.fuelSavedG,o.idleFuelAvoidedG-o.restartFuelPenaltyG,'penalty'],['Net',0,o.fuelSavedG,'gain']]) {const col=el('div',undefined,'micro-waterfall-column'),track=el('div',undefined,'micro-waterfall-track'),band=el('span',undefined,`micro-waterfall-band ${kind}`);band.style.bottom=`${Math.max(0,low)/scale*100}%`;band.style.height=`${Math.max(0,high-low)/scale*100}%`;track.append(band);col.append(track,el('span',label));waterfall.append(col);}chart.append(waterfall);
    for(const [label,key] of [['Idle fuel avoided','idleFuelAvoidedG'],['Restart fuel penalty','restartFuelPenaltyG'],['Recharge fuel penalty','rechargeFuelPenaltyG'],['Net fuel saved','fuelSavedG']]) bar(chart,label,o[key],Math.max(o.idleFuelAvoidedG,1),'g');
    chart.append(el('h3','Battery and duration','h5 mt-4'));
    bar(chart,'Initial SOC',values.initialSocPct,100,'%');bar(chart,'Final SOC',o.finalBatterySocPct,100,'%');
    bar(chart,'Predicted crank voltage',o.predictedCrankVoltageV,Math.max(15,o.predictedCrankVoltageV,values.minimumCrankVoltageV),'V');
    bar(chart,'Engine-off terminal voltage',o.engineOffTerminalVoltageV,Math.max(15,o.engineOffTerminalVoltageV),'V');
    bar(chart,'Minimum crank voltage',values.minimumCrankVoltageV,Math.max(15,values.minimumCrankVoltageV),'V');
    const durationMax=Math.max(1,values.stopDurationS,values.minimumStopTimeS,o.breakEvenStopTimeS??0);
    bar(chart,'Actual stop',values.stopDurationS,durationMax,'s');bar(chart,'Minimum stop',values.minimumStopTimeS,durationMax,'s');if(o.breakEvenStopTimeS!==null)bar(chart,'Break-even stop',o.breakEvenStopTimeS,durationMax,'s');else chart.append(el('p','No finite break-even point for these inputs.','small'));
    $('micro-formulas').replaceChildren(...[
      `Crank voltage = 11.8 + 0.012 × ${values.initialSocPct} − ${values.crankingCurrentA} × ${values.batteryInternalResistanceOhm} = ${fmt(o.predictedCrankVoltageV)} V.`,
      `Break-even = (restart fuel + starting energy fuel equivalent) / (idle rate − accessory fuel-equivalent rate) = ${fmt(o.breakEvenStopTimeS)}${o.breakEvenStopTimeS===null?'':' s'}.`,
      `Electrical energy = ${fmt(o.accessoryEnergyJ)} J accessories + ${fmt(o.startEnergyTotalJ)} J starts = ${fmt(o.totalElectricalEnergyJ)} J.`,
      `Conventional fuel = ${fmt(o.conventionalFuelG)} g; micro-hybrid fuel = ${fmt(o.microHybridFuelG)} g; difference = ${fmt(o.fuelSavedG)} g (${fmt(o.fuelReductionPct)}%).`
    ].map(x=>el('p',x)));
    step=0; stopIndex=0; showStage();
  }
  function showStage() {
    if(!result)return; const count=Math.min(values.numberOfStops,3), off=result.stopPermission;
    const states=['Approaching the traffic light','Stopped · controller evaluates',off?'Engine OFF · accessories on battery':`Engine ON · ${result.inhibitMessage}`,off?'Restarting · engine ON':'Continuing with engine ON','Moving away'];
    const stage=states[step]; document.querySelector('.micro-scene').dataset.stage=step===0?'moving':step===4?'leaving':'stopped';
    $('micro-stage').textContent=count?stage:'No stops selected'; $('micro-engine').textContent=step===2&&off?'Engine OFF':'Engine ON';$('micro-battery').textContent=step===2&&off?'Battery supplies accessories':'Battery standby';
    const fraction=count?(stopIndex+(step>=3?1:0))/count:0;
    $('micro-play-progress').textContent=`Illustrative stop ${count?stopIndex+1:0} of ${count}; scenario totals: ${values.numberOfStops} stops · fuel saved ${fmt(result.fuelSavedG*fraction)} g · battery SOC ${fmt(values.initialSocPct+(result.finalBatterySocPct-values.initialSocPct)*fraction)}%.`;
  }
  function tick() { if(!result)return; if(!values.numberOfStops){pause();return;} step++; if(step>4){step=0;stopIndex++;if(stopIndex>=Math.min(values.numberOfStops,3)){step=4;stopIndex=Math.min(values.numberOfStops,3)-1;showStage();pause();return;}} showStage(); }
  function play(){if(!result)return;pause();$('micro-play').disabled=true;$('micro-pause').disabled=false;timer=setInterval(tick,1500/Number($('micro-speed').value));}
  $('micro-play').addEventListener('click',play);$('micro-pause').addEventListener('click',pause);$('micro-replay').addEventListener('click',()=>{pause();step=0;stopIndex=0;showStage();play();});
  $('micro-speed').addEventListener('change',()=>{if(timer)play();});
  $('micro-reset').addEventListener('click',()=>{for(const [key,input] of Object.entries(inputs))input.value=DEFAULTS[key];update();});
  $('micro-export').addEventListener('click',()=>{if(!result)return;const url=URL.createObjectURL(new Blob([JSON.stringify({moduleId:'hev-12v-microhybrid-stopstart',inputs:values,outputs:result},null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='12v-microhybrid-stop-start.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  $('micro-save').addEventListener('click',()=>{if(!result)return;if(saved.length===4)saved.shift();saved.push({inputs:{...values},outputs:{...result}});const table=el('table',undefined,'table table-sm'),caption=el('caption','Most recent four scenarios, stored in this page only.');table.append(caption);const rows=[['Scenario',...saved.map((_,i)=>String(i+1))],...FIELDS.map(([key,label,unit])=>[`${label} (${unit})`,...saved.map(x=>String(x.inputs[key]))]),['Decision code',...saved.map(x=>String(x.outputs.inhibitCode))],['Fuel saved (g)',...saved.map(x=>fmt(x.outputs.fuelSavedG))],['Final SOC (%)',...saved.map(x=>fmt(x.outputs.finalBatterySocPct))]];for(const [idx,row] of rows.entries()){const tr=el('tr');row.forEach((x,j)=>{const cell=el(idx===0||j===0?'th':'td',x);if(cell.tagName==='TH')cell.scope=idx===0?'col':'row';tr.append(cell);});table.append(tr);}$('micro-comparison').replaceChildren(table);});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});window.addEventListener('pagehide',pause);
  update();
}
