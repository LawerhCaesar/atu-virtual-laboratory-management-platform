const NS='http://www.w3.org/2000/svg';
export function createSchematic(host,detail){
 const svg=document.createElementNS(NS,'svg');svg.setAttribute('viewBox','0 0 760 320');svg.setAttribute('role','group');svg.setAttribute('aria-label','Interactive engine-system schematic');svg.classList.add('engine-schematic');host.append(svg);
 const add=(tag,attrs,text,parent=svg)=>{const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;parent.append(e);return e;};
 const pathDefs=['M160 70 H230','M330 70 H395','M495 70 H570','M160 245 H230','M330 245 H395','M495 245 H570','M445 110 V205'];
 const paths=pathDefs.map(d=>add('path',{d,stroke:'#91b5cf','stroke-width':3,fill:'none'}));
 const nodes={};
 function node(key,x,y,label){const g=add('g',{tabindex:'0',role:'button','aria-label':`${label}: show explanation`,class:'engine-schematic-node'});add('rect',{x,y,width:100,height:80,rx:12,fill:'#29435d',stroke:'#8fb8d2'},undefined,g);add('text',{x:x+50,y:y+28,'text-anchor':'middle',fill:'#fff','font-size':label==='VIRTUAL pump'?13:15},label,g);const text=add('text',{x:x+50,y:y+56,'text-anchor':'middle',fill:'#dcecff','font-size':13},'—',g);if(['engine','fan','pump','starter','fuel','injector'].includes(key)){const rotor=add('g',{'data-rotor':key,'data-active':'false'},undefined,g);add('circle',{cx:x+18,cy:y+67,r:6,fill:'none',stroke:'#bce5ee','stroke-width':1.5},undefined,rotor);add('path',{d:`M${x+12} ${y+67} H${x+24} M${x+18} ${y+61} V${y+73}`,stroke:'#bce5ee','stroke-width':1.5},undefined,rotor);}g.addEventListener('click',()=>detail(key));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();detail(key);}});nodes[key]={g,text,x,y};}
 node('battery',60,30,'Battery');node('ecu',230,30,'ECU / auth');node('starter',395,30,'Starter');node('engine',570,30,'Engine / RPM');node('fuel',60,205,'Fuel pump');node('injector',230,205,'Injector');node('fan',395,205,'Fan');node('pump',570,205,'VIRTUAL pump');
 const ect=add('text',{x:380,y:165,'text-anchor':'middle',fill:'#fff','font-size':15},'Virtual ECT1 / ECT2 signals');
 const ignition=add('text',{x:380,y:190,'text-anchor':'middle',fill:'#dcecff','font-size':14},'Ignition —');
 const media=matchMedia('(max-width:600px)');
 function layout(){const mobile=media.matches;svg.setAttribute('viewBox',mobile?'0 0 390 610':'0 0 760 320');
  const positions={battery:[45,25],ecu:[235,25],starter:[45,155],engine:[235,155],fuel:[45,285],injector:[235,285],fan:[45,415],pump:[235,415]};
  for(const [key,n]of Object.entries(nodes)){const pos=mobile?positions[key]:[n.x,n.y];n.g.setAttribute('transform',`translate(${pos[0]-n.x} ${pos[1]-n.y})`);}
  const mobilePaths=['M145 65 H235','M145 195 H235','M145 325 H235','M145 455 H235','M285 105 V130 H95 V155','M285 235 V260 H95 V285','M285 365 V390 H95 V415'];
  paths.forEach((p,i)=>p.setAttribute('d',mobile?mobilePaths[i]:pathDefs[i]));
  ect.setAttribute('x',mobile?195:380);ect.setAttribute('y',mobile?545:165);ignition.setAttribute('x',mobile?195:380);ignition.setAttribute('y',mobile?575:190);
 }
 media.addEventListener('change',layout);layout();
 return {update(result,running){const i=result.inputs,o=result.outputs;
 const values={battery:`${i.BatteryVoltage.toFixed(2)} V`,ecu:i.StartAuthorisation?'Authorised':'Not authorised',starter:o.StarterState?'ON':'OFF',engine:`${i.EngineSpeed.toFixed(0)} rpm`,fuel:o.FuelPumpState?'ON':'OFF',injector:o.InjectionEnable?`${o.InjectorPW.toFixed(3)} ms`:'Disabled',fan:`${o.FanDuty.toFixed(1)}% duty`,pump:`${o.WaterPumpDuty.toFixed(1)}% duty`};
 for(const[k,n]of Object.entries(nodes)){n.text.textContent=values[k];n.g.setAttribute('aria-label',`${k}: ${values[k]}; show explanation`);}
 ect.textContent=`${media.matches?'':'Virtual '}ECT1 ${o.ECT1Temp.toFixed(1)}°C · ECT2 ${o.ECT2Temp.toFixed(1)}°C · Δ ${o.SensorDifference.toFixed(1)}°C`;
 ignition.textContent=o.IgnitionEnable?`Ignition enabled · ${o.IgnitionTiming.toFixed(2)}° BTDC`:'Ignition disabled';
 for(const rotor of svg.querySelectorAll('[data-rotor]')){const key=rotor.dataset.rotor;const active=key==='engine'?[2,3].includes(o.EngineState)&&i.EngineSpeed>0:key==='fan'?o.FanDuty>0:key==='pump'?o.WaterPumpDuty>0:key==='starter'?o.StarterState>0:key==='fuel'?o.FuelPumpState>0:o.InjectionEnable>0;rotor.dataset.active=String(Boolean(active));const duty=key==='fan'?o.FanDuty:key==='pump'?o.WaterPumpDuty:50;rotor.style.setProperty('--rotor-time',`${Math.max(1.2,3-duty/60)}s`);}
 svg.dataset.running=String(running);svg.dataset.fan=String(o.FanDuty>0);svg.dataset.pump=String(o.WaterPumpDuty>0);
 }};
}
