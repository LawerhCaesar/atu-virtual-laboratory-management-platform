import {FIELDS,DEFAULTS,PRESETS,validateConfig} from "./model.mjs";

const root=document.getElementById("wheel-slip");
if(root) initialise();
function initialise(){
  const $=id=>document.getElementById(id), make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
  const controls={}, errorFields={}, preset=$("ws-preset");
  let draft={...DEFAULTS}, result=null, worker=null, playing=false, playbackS=0, lastFrame=0, zoomStart=0, zoomEnd=1;
  const media=matchMedia("(prefers-reduced-motion: reduce)");
  for(const name of Object.keys(PRESETS))preset.append(new Option(name,name));
  let fieldset;
  const groups={0:"Scenario",7:"Road and vehicle",10:"Wheel and tyre",12:"Torque"};
  for(const [index,[key,label,unit,value,min,max,step,purpose]] of FIELDS.entries()){
    if(groups[index]){fieldset=make("fieldset");fieldset.append(make("legend",groups[index]));$("ws-fields").append(fieldset);}
    const box=make("div",undefined,"fuel-input"), title=make("label",`${label} (${unit})`), input=make("input"), range=make("input"), row=make("div",undefined,"fuel-number");
    input.id=`ws-input-${key}`;input.type="number";input.step="any";input.className="form-control";input.value=value;title.htmlFor=input.id;
    const help=make("small",`Allowed: ${min}–${max} ${unit}. Default: ${value}. ${purpose}`);help.id=`ws-help-${key}`;
    const error=make("small","","fuel-field-error");error.id=`ws-error-${key}`;errorFields[key]=error;
    input.setAttribute("aria-describedby",`${help.id} ${error.id}`);
    range.type="range";range.min=min;range.max=max;range.step=step;range.value=value;range.className="form-range";range.setAttribute("aria-label",`${label} slider`);range.setAttribute("aria-describedby",help.id);
    const update=value=>{draft[key]=value;input.value=Number.isFinite(value)?value:"";range.value=Number.isFinite(value)?value:min;changed();};
    const down=make("button","−","btn btn-outline-secondary"),up=make("button","+","btn btn-outline-secondary");
    for(const [button,dir,verb] of [[down,-1,"Decrease"],[up,1,"Increase"]]){button.type="button";button.setAttribute("aria-label",`${verb} ${label}`);button.addEventListener("click",()=>{const next=Number((Number(draft[key]||0)+dir*step).toFixed(6));update(Math.min(max,Math.max(min,next)));});}
    row.append(down,input,up);input.addEventListener("input",()=>{draft[key]=input.value===""?NaN:Number(input.value);range.value=Number.isFinite(draft[key])?draft[key]:min;changed();});range.addEventListener("input",()=>update(Number(range.value)));
    box.append(title,row,range,help,error);fieldset.append(box);controls[key]={input,range};
  }
  fieldset=make("fieldset");fieldset.append(make("legend","Controllers"));$("ws-fields").append(fieldset);
  for(const [key,label] of [["absEnabled","ABS enabled"],["tcsEnabled","TCS enabled"]]){const box=make("div",undefined,"fuel-input"),input=make("input"),labelEl=make("label",label);input.type="checkbox";input.id=`ws-input-${key}`;input.className="form-check-input me-2";input.checked=true;labelEl.htmlFor=input.id;input.addEventListener("change",()=>{draft[key]=input.checked;changed();});box.append(input,labelEl,make("small",key==="absEnabled"?"Controls brake torque when braking above 1 m/s.":"Controls drive torque when accelerating without braking."));fieldset.append(box);controls[key]={input};}
  const kpis=[
    ["finalDistanceM","Distance travelled","m",2],["stoppingTimeS","Stopping time","s",2],["stoppingDistanceM","Stopping distance","m",2],
    ["peakBrakeSlip","Peak brake slip","ratio",3],["peakDriveSlip","Peak drive slip","ratio",3],["peakAbsTyreForceN","Peak absolute tyre force","N",1],
    ["absActiveTimeS","ABS active time","s",2],["tcsActiveTimeS","TCS active time","s",2],["finalVehicleSpeedKph","Final vehicle speed","km/h",2],["finalWheelSpeedKph","Final wheel peripheral speed","km/h",2]
  ];
  const cards={}; for(const [key,label,unit] of kpis){const box=make("div"),value=make("dd","—");value.dataset.wsMetric=key;box.append(make("dt",`${label} (${unit})`),value);$("ws-kpis").append(box);cards[key]=value;}
  const chartDefs=[
    ["Vehicle and wheel speed","km/h",[["vehicleSpeedKph","Vehicle speed"],["wheelPeripheralSpeedKph","Wheel peripheral speed"]]],
    ["Wheel slip","ratio",[["brakeSlip","Brake slip"],["driveSlip","Drive slip"]],[.10,.12,.18,.20]],
    ["Applied torque","N·m",[["brakeTorqueNm","Brake torque"],["driveTorqueNm","Drive torque"]]],
    ["Tyre longitudinal force","N",[["tyreForceN","Tyre force per wheel"]]],
    ["Controller state timeline","code / active",[["controllerMode","Controller mode"],["absActive","ABS active"],["tcsActive","TCS active"]]],
    ["Distance travelled","m",[["distanceM","Distance"]]],
  ];
  const ns="http://www.w3.org/2000/svg", colours=["#2857b5","#a44319","#126445"],charts=[];
  for(const [index,[title,unit,series]] of chartDefs.entries()){
    const figure=make("figure"), caption=make("figcaption",`${title} (${unit})`),legend=make("p",undefined,"ws-legend"),svg=document.createElementNS(ns,"svg"),readout=make("p","Move the pointer over the chart to inspect values.","ws-chart-readout");
    series.forEach(([,label],i)=>{const item=make("span",label);item.style.setProperty("--series-color",colours[i]);legend.append(item);});
    if(index===1)legend.append(make("span","Dashed: TCS 0.10 / 0.18; ABS 0.12 / 0.20"));
    svg.setAttribute("viewBox","0 0 500 240");svg.setAttribute("role","img");svg.setAttribute("aria-label",`${title} (${unit}) versus time (s)`);svg.id=`ws-chart-${index}`;
    svg.addEventListener("pointermove",event=>{if(!result)return;const rect=svg.getBoundingClientRect(),fraction=Math.max(0,Math.min(1,((event.clientX-rect.left)/rect.width*500-65)/415)),row=result.samples[Math.min(result.samples.length-1,Math.round((zoomStart+fraction*(zoomEnd-zoomStart))/.001))];readout.textContent=`${row.timeS.toFixed(3)} s · `+series.map(([key,label])=>`${label}: ${Number(row[key]).toFixed(3)} ${unit}`).join(" · ");});
    const exportChart=make("button","Download chart SVG","btn btn-sm btn-outline-secondary");exportChart.type="button";exportChart.setAttribute("aria-label",`Download ${title} chart SVG`);exportChart.disabled=true;exportChart.addEventListener("click",()=>{if(result){const clone=svg.cloneNode(true);clone.setAttribute("xmlns",ns);download(new XMLSerializer().serializeToString(clone),"image/svg+xml",`wheel-slip-chart-${index+1}.svg`);}});
    figure.append(caption,legend,svg,readout,exportChart);$("ws-charts").append(figure);charts.push({svg,series,unit,thresholds:chartDefs[index][3]||[],exportChart});
  }
  function drawCharts(){
    if(result){const duration=result.config.durationS,window=duration/Number($("ws-zoom").value);zoomStart=Math.max(0,Math.min(duration-window,playbackS-window/2));zoomEnd=zoomStart+window;}
    for(const {svg,series,thresholds,exportChart} of charts){
      exportChart.disabled=!result;
      svg.replaceChildren();const add=(tag,attrs,text)=>{const e=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;svg.append(e);return e;};
      if(!result){add("text",{x:270,y:110,"text-anchor":"middle"},"Run a simulation to see this chart");continue;}
      const all=result.samples.slice(Math.round(zoomStart/.001),Math.round(zoomEnd/.001)+1), chosen=new Set([0,all.length-1]), width=Math.max(1,Math.ceil(all.length/360));
      for(let start=0;start<all.length;start+=width){const end=Math.min(all.length,start+width);chosen.add(start);chosen.add(end-1);for(const [key] of series){let low=start,high=start;for(let j=start+1;j<end;j++){if(Number(all[j][key])<Number(all[low][key]))low=j;if(Number(all[j][key])>Number(all[high][key]))high=j;}chosen.add(low);chosen.add(high);}if(series.some(([key])=>key==="controllerMode")){for(let j=start+1;j<end;j++)if(all[j].controllerMode!==all[j-1].controllerMode){chosen.add(j-1);chosen.add(j);}}}
      const rows=[...chosen].sort((a,b)=>a-b).map(i=>all[i]);let lo=Math.min(0,...thresholds),hi=Math.max(1,...thresholds);
      for(const row of rows)for(const [key] of series){lo=Math.min(lo,Number(row[key]));hi=Math.max(hi,Number(row[key]));}const pad=(hi-lo||1)*.05;lo-=pad;hi+=pad;
      const x=t=>65+(t-zoomStart)/(zoomEnd-zoomStart)*415,y=v=>190-(v-lo)/(hi-lo)*170;
      for(let tick=0;tick<=4;tick++){const value=lo+(hi-lo)*tick/4,yy=y(value),time=zoomStart+(zoomEnd-zoomStart)*tick/4;add("line",{x1:65,x2:480,y1:yy,y2:yy,stroke:"#e0e6ee"});add("text",{x:59,y:yy+4,"text-anchor":"end"},Math.abs(value)>9999?value.toExponential(1):value.toFixed(Math.abs(value)<10?2:0));add("text",{x:x(time),y:211,"text-anchor":"middle"},time.toFixed(1));}
      add("text",{x:270,y:232,"text-anchor":"middle"},"Time (s)");
      for(const threshold of thresholds)add("line",{x1:65,x2:480,y1:y(threshold),y2:y(threshold),stroke:"#8a8a8a","stroke-dasharray":"4 4","stroke-width":1});
      series.forEach(([key],index)=>add("polyline",{points:rows.map(row=>`${x(row.timeS).toFixed(2)},${y(Number(row[key])).toFixed(2)}`).join(" "),fill:"none",stroke:colours[index],"stroke-width":2,"stroke-dasharray":["none","7 3","2 3"][index]}));
    }
  }
  function sync(){for(const [key,control] of Object.entries(controls)){if(control.input.type==="checkbox")control.input.checked=draft[key];else{control.input.value=draft[key];control.range.value=draft[key];}}}
  function cancel(){if(worker){worker.terminate();worker=null;}playing=false;lastFrame=0;}
  function validate(){const errors=validateConfig(draft);for(const [key,node] of Object.entries(errorFields)){node.textContent=errors[key]||"";controls[key].input.setAttribute("aria-invalid",String(Boolean(errors[key])));}$("ws-error").hidden=!Object.keys(errors).length;$("ws-error").textContent=Object.values(errors).join(" ");return !Object.keys(errors).length;}
  function changed(){cancel();result=null;playbackS=0;validate();$("ws-status").textContent="Inputs changed · run a new simulation.";$("ws-result-note").textContent="Run a scenario to calculate results.";$("ws-warnings").replaceChildren();for(const cell of Object.values(cards))cell.textContent="—";drawCharts();renderFrame();buttons();}
  function buttons(){const valid=!Object.keys(validateConfig(draft)).length;$("ws-run").disabled=!valid||!!worker;$("ws-cancel").disabled=!worker;for(const id of ["ws-json","ws-csv","ws-scrub","ws-restart"])$(id).disabled=!result;$("ws-play").disabled=!result||playing||playbackS>=result.config.durationS;$("ws-pause").disabled=!playing;}
  function surface(mu){return mu<.3?"low grip":mu<.6?"reduced grip":"higher grip";}
  const modes={0:"No active intervention",1:"ABS APPLY",2:"ABS HOLD",3:"ABS RELEASE", "-1":"TCS RESTORE", "-2":"TCS HOLD", "-3":"TCS REDUCE"};
  function renderFrame(){
    $("ws-road").textContent=`Road μ ${Number(draft.roadMu).toFixed(2)} · ${surface(draft.roadMu)}`;
    if(!result){$("ws-controller").textContent="Awaiting simulation";$("ws-speed").textContent="Vehicle — km/h · Wheel — km/h";$("ws-visual-cue").textContent="Run a simulation to view the response";$("ws-time").textContent="0.00";$("ws-scrub").value=0;$("ws-car").setAttribute("transform","translate(0 0)");$("ws-wheel-a").removeAttribute("transform");$("ws-wheel-b").removeAttribute("transform");$("ws-slip-marks").setAttribute("opacity","0");return;}
    const row=result.samples[Math.min(result.samples.length-1,Math.round(playbackS/.001))], total=Math.max(result.metrics.finalDistanceM,.001),progress=Math.min(1,row.distanceM/total);
    $("ws-controller").textContent=`${modes[row.controllerMode]} · ABS ${row.absActive?"active":"inactive"} · TCS ${row.tcsActive?"active":"inactive"}`;
    $("ws-speed").textContent=`Vehicle ${row.vehicleSpeedKph.toFixed(1)} km/h · Wheel ${row.wheelPeripheralSpeedKph.toFixed(1)} km/h`;
    const cue=row.brakeSlip>.2?"Wheel-lock tendency":row.driveSlip>.18?"Wheel-spin tendency":"Wheel grip illustration";$("ws-visual-cue").textContent=`${cue} · ${modes[row.controllerMode]}`;$("ws-slip-marks").setAttribute("opacity",row.brakeSlip>.2||row.driveSlip>.18?"1":"0");
    $("ws-car").setAttribute("transform",`translate(${Math.min(245,progress*245)} 0)`);const degrees=(row.wheelAngleRad*180/Math.PI)%360;
    $("ws-wheel-a").setAttribute("transform",`rotate(${degrees} 135 231)`);$("ws-wheel-b").setAttribute("transform",`rotate(${degrees} 407 231)`);
    $("ws-road-marks").setAttribute("stroke-dashoffset",String(-row.distanceM*4%60));$("ws-time").textContent=playbackS.toFixed(2);$("ws-scrub").value=playbackS;
  }
  function showResult(data){result=data;playbackS=0;$("ws-scrub").max=data.config.durationS;$("ws-warnings").replaceChildren(...data.warnings.map(w=>make("li",w)));$("ws-result-note").textContent=`${data.samples.length.toLocaleString()} full-resolution samples. Controller time counts each enabled control mode, including apply/hold.`;
    for(const [key,,,digits] of kpis)cards[key].textContent=data.metrics[key]===null?"Not reached within simulation time":data.metrics[key].toFixed(digits);
    $("ws-status").textContent="Calculation complete · use playback to explore.";drawCharts();renderFrame();buttons();}
  $("ws-load").addEventListener("click",()=>{draft={...PRESETS[preset.value]};sync();changed();$("ws-status").textContent=`${preset.value} loaded · press Run simulation.`;});
  $("ws-reset").addEventListener("click",()=>{draft={...DEFAULTS};sync();changed();$("ws-status").textContent="Defaults restored · press Run simulation.";});
  $("ws-run").addEventListener("click",()=>{if(!validate())return;changed();$("ws-status").textContent="Calculating in the background…";try{worker=new Worker(new URL("./worker.mjs",import.meta.url),{type:"module"});const current=worker;current.onmessage=event=>{if(worker!==current)return;worker.terminate();worker=null;if(event.data.ok)showResult(event.data.result);else{$("ws-error").hidden=false;$("ws-error").textContent=event.data.error;$("ws-status").textContent="Calculation failed.";buttons();}};current.onerror=()=>{if(worker!==current)return;cancel();$("ws-error").hidden=false;$("ws-error").textContent="The simulation worker failed to start. Check the browser and try again.";$("ws-status").textContent="Calculation failed.";buttons();};current.postMessage({...draft});buttons();}catch(error){cancel();$("ws-error").hidden=false;$("ws-error").textContent=error.message;buttons();}});
  $("ws-cancel").addEventListener("click",()=>{cancel();$("ws-status").textContent="Calculation cancelled.";buttons();});
  $("ws-play").addEventListener("click",()=>{playing=true;lastFrame=0;buttons();});$("ws-pause").addEventListener("click",()=>{playing=false;buttons();});
  $("ws-restart").addEventListener("click",()=>{playing=false;playbackS=0;lastFrame=0;renderFrame();drawCharts();buttons();});$("ws-scrub").addEventListener("input",event=>{playing=false;playbackS=Number(event.target.value);renderFrame();drawCharts();buttons();});$("ws-zoom").addEventListener("change",drawCharts);
  function animate(now){if(playing&&result&&!document.hidden){if(lastFrame)playbackS=Math.min(result.config.durationS,playbackS+(now-lastFrame)/1000*Number($("ws-playback-speed").value));if(playbackS>=result.config.durationS)playing=false;renderFrame();buttons();}lastFrame=now;requestAnimationFrame(animate);}
  document.addEventListener("visibilitychange",()=>{if(document.hidden){playing=false;buttons();}lastFrame=0;});media.addEventListener("change",()=>{if(media.matches){playing=false;buttons();}});
  const download=(text,type,name)=>{const url=URL.createObjectURL(new Blob([text],{type})),a=make("a");a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  $("ws-json").addEventListener("click",()=>{if(result)download(JSON.stringify(result,null,2),"application/json","wheel-slip-results.json");});
  $("ws-csv").addEventListener("click",()=>{if(!result)return;const keys=Object.keys(result.samples[0]),meta=[`# modelVersion,${result.modelVersion}`,...Object.entries(result.config).map(([k,v])=>`# config.${k},${v}`)];download([...meta,keys.join(","),...result.samples.map(row=>keys.map(k=>row[k]).join(","))].join("\n"),"text/csv","wheel-slip-results.csv");});
  validate();drawCharts();renderFrame();buttons();requestAnimationFrame(animate);
}
