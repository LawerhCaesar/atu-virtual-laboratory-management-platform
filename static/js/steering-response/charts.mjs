const NS='http://www.w3.org/2000/svg';
const GROUPS=[
 ['Handling Response',[[['yawRateDegPerS','Yaw rate'],'deg/s'],[['sideslipDeg','Sideslip angle'],'deg'],[['lateralAccelerationMps2','Lateral acceleration'],'m/s²']]],
 ['Steering, Radius and Lateral Acceleration',[[['steeringWheelAngleDeg','Steering-wheel angle'],'deg'],[['turningRadiusM','Turning radius'],'m'],[['lateralAccelerationG','Lateral acceleration'],'g']]],
 ['Trajectory and Heading',[[['xM','X position'],'m'],[['yM','Y position'],'m'],[['headingDeg','Heading angle'],'deg']]],
 ['Tyre Lateral Forces',[[['frontLateralForceN','Front lateral force'],'N',['rearLateralForceN','Rear lateral force']]]],
];
const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
export function createCharts(container) {
 let result=null;const charts=[];
 for(const [groupIndex,[name,definitions]] of GROUPS.entries()) {
  const section=make('section',undefined,'steering-plot-group'),title=make('h3',name,'h4'),grid=make('div',undefined,'steering-chart-grid');title.id=`steering-plot-group-${groupIndex}`;section.setAttribute('aria-labelledby',title.id);section.append(title,grid);container.append(section);
  for(const [primary,unit,secondary] of definitions) {
   const series=secondary?[primary,secondary]:[primary],figure=make('figure'),legend=make('p',undefined,'steering-chart-legend'),svg=document.createElementNS(NS,'svg'),readout=make('p','Use playback position to inspect a recorded sample.','steering-chart-readout');
   const name=secondary?'Front and rear lateral forces':primary[1];figure.append(make('figcaption',`${name} (${unit})`));
   series.forEach(([,label],i)=>legend.append(make('span',`${i?'Dashed':'Solid'}: ${label}`)));
   svg.setAttribute('viewBox','0 0 500 245');svg.setAttribute('role','img');svg.setAttribute('aria-label',`${name} (${unit}) versus time (s)`);svg.dataset.steeringChart=primary[0];figure.append(legend,svg,readout);grid.append(figure);charts.push({svg,series,unit,readout,cursor:null});
  }
 }
 const add=(svg,tag,attrs,text)=>{const e=document.createElementNS(NS,tag);for(const [key,value] of Object.entries(attrs))e.setAttribute(key,value);if(text!==undefined)e.textContent=text;svg.append(e);return e;};
 function draw() {
  for(const chart of charts) {
   const {svg,series,unit}=chart;svg.replaceChildren();chart.cursor=null;
   if(!result){add(svg,'text',{x:270,y:110,'text-anchor':'middle'},'Run a simulation to view results');chart.readout.textContent='Use playback position to inspect a recorded sample.';continue;}
   const all=result.samples,selected=new Set([0,all.length-1]),bucket=Math.max(1,Math.ceil(all.length/220));
   for(let start=0;start<all.length;start+=bucket){const end=Math.min(all.length,start+bucket);selected.add(start);selected.add(end-1);for(const [key] of series){let low=start,high=start;for(let i=start+1;i<end;i++){if(all[i][key]<all[low][key])low=i;if(all[i][key]>all[high][key])high=i;}selected.add(low);selected.add(high);}}
   const rows=[...selected].sort((a,b)=>a-b).map(i=>all[i]);let min=0,max=0;for(const row of all)for(const [key] of series){min=Math.min(min,row[key]);max=Math.max(max,row[key]);}const padding=(max-min||1)*.07;min-=padding;max+=padding;
   const x=t=>70+t/result.scenario.durationS*410,y=v=>195-(v-min)/(max-min)*170;
   for(let n=0;n<=4;n++){const value=min+(max-min)*n/4,time=result.scenario.durationS*n/4;add(svg,'line',{x1:70,x2:480,y1:y(value),y2:y(value),stroke:'#e0e6ee'});add(svg,'text',{x:65,y:y(value)+4,'text-anchor':'end'},Math.abs(value)>=10000?value.toExponential(1):value.toFixed(Math.abs(value)<10?2:0));add(svg,'text',{x:x(time),y:215,'text-anchor':'middle'},time.toFixed(1));}
   add(svg,'text',{x:275,y:239,'text-anchor':'middle'},'Time (s)');add(svg,'text',{x:14,y:110,transform:'rotate(-90 14 110)','text-anchor':'middle'},unit);
   series.forEach(([key],i)=>add(svg,'polyline',{points:rows.map(row=>`${x(row.timeS).toFixed(3)},${y(row[key]).toFixed(3)}`).join(' '),fill:'none',stroke:i?'#a34b22':'#2857b5','stroke-width':2.3,'stroke-dasharray':i?'7 4':'none'}));
   chart.cursor=add(svg,'line',{x1:70,x2:70,y1:20,y2:195,stroke:'#67788f','stroke-width':1,'stroke-dasharray':'2 3'});
  }
 }
 function cursor(row){if(!result)return;for(const c of charts){const x=70+row.timeS/result.scenario.durationS*410;c.cursor?.setAttribute('x1',x);c.cursor?.setAttribute('x2',x);c.readout.textContent=`${row.timeS.toFixed(3)} s · `+c.series.map(([key,label])=>`${label}: ${row[key].toFixed(4)} ${c.unit}`).join(' · ');}}
 draw();return {setResult(value){result=value;draw();},setCursor:cursor};
}
