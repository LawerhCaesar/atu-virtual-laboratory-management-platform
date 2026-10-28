const NS='http://www.w3.org/2000/svg';
export function createScene(host){
 const svg=document.createElementNS(NS,'svg');svg.classList.add('p2-scene');svg.setAttribute('viewBox','0 0 660 490');svg.setAttribute('role','img');svg.setAttribute('aria-label','P2 engine, clutch and motor join before transmission, final drive and wheels');host.append(svg);
 const add=(tag,attrs,text,parent=svg)=>{const el=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))el.setAttribute(k,v);if(text!==undefined)el.textContent=text;parent.append(el);return el;};
 const defs=add('defs',{});for(const[key,col]of Object.entries({engine:'#f2ca78',electric:'#82bbff',shaft:'#78d4c7'})){const marker=add('marker',{id:`p2-arrow-${key}`,viewBox:'0 0 10 10',refX:8,refY:5,markerWidth:4,markerHeight:4,orient:'auto'},undefined,defs);add('path',{d:'M0 0 L10 5 L0 10Z',fill:col},undefined,marker);}
 const path=(id,d,col,key)=>add('path',{id,d,stroke:col,'stroke-width':4,'marker-end':`url(#p2-arrow-${key})`,class:'p2-flow','data-active':'false'});
 const enginePath=path('p2-engine-path','M175 222 H230 M330 222 H390','#f2ca78','engine');
 const electricPath=path('p2-electric-path','M200 92 H270 M390 92 H455 V172','#82bbff','electric');
 const shaftPath=path('p2-shaft-path','M515 222 H600 V330 H175 V390 H220 M340 390 H395 M515 390 H560','#78d4c7','shaft');
 const nodes={};
 function node(key,x,y,w,label){const g=add('g',{'data-component':key});add('rect',{x,y,width:w,height:90,rx:16,class:'p2-node'},undefined,g);add('text',{x:x+w/2,y:y+31,'text-anchor':'middle',class:'p2-node-title'},label,g);const value=add('text',{x:x+w/2,y:y+66,'text-anchor':'middle',class:'p2-node-value'},'—',g);nodes[key]={g,value};return g;}
 node('battery',40,44,160,'Battery');node('inverter',270,44,120,'Inverter');
 node('engine',40,177,135,'Engine');node('clutch',230,177,100,'Clutch');node('motor',390,177,125,'Motor');
 node('transmission',220,345,120,'Gearbox');node('final',395,345,120,'Final drive');
 const wheels=add('g',{'data-component':'wheels'});for(const y of [350,417]){add('rect',{x:561,y,width:70,height:25,rx:7,fill:'#132335',stroke:'#b7cadc','stroke-width':2},undefined,wheels);const g=add('g',{'data-rotor':'wheel','data-active':'false'},undefined,wheels);add('path',{d:`M570 ${y+12} H622 M596 ${y+3} V${y+22}`,stroke:'#b7cadc','stroke-width':2},undefined,g);}add('path',{d:'M595 375 V417',stroke:'#b7cadc','stroke-width':4},undefined,wheels);
 const wheelText=add('text',{x:590,y:475,'text-anchor':'middle',class:'p2-node-value'},'Wheels');
 const batteryFill=add('rect',{x:52,y:118,width:136,height:5,rx:2,fill:'#82bbff'});
 const clutchPlate=add('path',{d:'M268 244 H292',stroke:'#f2ca78','stroke-width':4});
 for(const[key,cx,cy]of [['engine',107,283],['motor',452,283]]){const g=add('g',{'data-rotor':key,'data-active':'false'});add('circle',{cx,cy,r:12,fill:'none',stroke:key==='engine'?'#f2ca78':'#78d4c7','stroke-width':2},undefined,g);add('path',{d:`M${cx-8} ${cy} H${cx+8} M${cx} ${cy-8} V${cy+8}`,stroke:'#dce8f4','stroke-width':2},undefined,g);}
 const detail=add('text',{x:35,y:320,class:'p2-node-value'},'Power paths awaiting a run');
 return {update(row,parameters,playing){svg.dataset.playing=String(playing);if(!row){for(const p of [enginePath,electricPath,shaftPath])p.dataset.active='false';for(const n of Object.values(nodes))n.value.textContent='—';detail.textContent='Power paths awaiting a run';wheelText.textContent='Wheels';batteryFill.setAttribute('width',0);svg.querySelectorAll('[data-rotor]').forEach(e=>e.dataset.active='false');return;}
  const engine=row.engine_torque_nm>0&&row.clutch_state===1,motor=row.motor_torque_nm>0,shaft=row.actual_wheel_torque_nm>0;
  enginePath.dataset.active=String(engine);electricPath.dataset.active=String(motor);shaftPath.dataset.active=String(shaft);
  enginePath.setAttribute('stroke-width',3+Math.min(row.engine_torque_nm/30,5));electricPath.setAttribute('stroke-width',3+Math.min(row.battery_terminal_power_w/8000,5));shaftPath.setAttribute('stroke-width',3+Math.min(row.actual_wheel_torque_nm/200,5));
  svg.style.setProperty('--flow-speed',`${Math.max(.35,1.7-row.battery_terminal_power_w/40000)}s`);
  nodes.engine.g.dataset.nodeActive=String(engine);nodes.motor.g.dataset.nodeActive=String(motor);
  nodes.engine.value.textContent=`${row.engine_torque_nm.toFixed(1)} Nm${engine?'':' · off'}`;
  nodes.motor.value.textContent=`${row.motor_torque_nm.toFixed(1)} Nm`;
  nodes.clutch.value.textContent=row.clutch_state?'CLOSED':'OPEN';clutchPlate.setAttribute('d',row.clutch_state?'M264 246 H296':'M264 246 L277 238 M286 246 H296');
  nodes.battery.value.textContent=`${row.soc_percent.toFixed(2)}% SOC`;batteryFill.setAttribute('width',136*row.soc_percent/100);
  nodes.inverter.value.textContent=`${(parameters.inverter_efficiency*100).toFixed(1)}% η`;
  nodes.transmission.value.textContent=`${parameters.gear_ratio.toFixed(2)} : 1`;nodes.final.value.textContent=`${parameters.final_drive_ratio.toFixed(2)} : 1`;
  wheelText.textContent=`${row.actual_wheel_torque_nm.toFixed(1)} Nm`;
  detail.textContent=`${row.battery_current_a.toFixed(2)} A · ${row.battery_terminal_voltage_v.toFixed(2)} V · auxiliary ${parameters.auxiliary_load_w.toFixed(0)} W`;
  svg.querySelectorAll('[data-rotor]').forEach(el=>el.dataset.active=String(el.dataset.rotor==='engine'?engine:el.dataset.rotor==='motor'?motor:shaft));
 }};
}
