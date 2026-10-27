const NS='http://www.w3.org/2000/svg';
export function createTrajectory(root,baseline) {
 const $=id=>root.querySelector(`#${id}`),car=$('steering-car'),grid=$('steering-scene-grid');let result=null,fit=null,currentRow=null;
 const body=$('steering-car-body').querySelector('rect');body.setAttribute('x',-baseline.length_m/2);body.setAttribute('y',-baseline.width_m/2);body.setAttribute('width',baseline.length_m);body.setAttribute('height',baseline.width_m);
 const tyreWidth=Number.parseInt(baseline.tyre_size,10)/1000;
 for(const wheel of car.querySelectorAll('g[id^="steering-wheel-"] rect')) {wheel.setAttribute('x',-baseline.wheel_radius_m);wheel.setAttribute('y',-tyreWidth/2);wheel.setAttribute('width',baseline.wheel_radius_m*2);wheel.setAttribute('height',tyreWidth);}
 const add=(tag,attrs,text)=>{const e=document.createElementNS(NS,tag);for(const [key,value] of Object.entries(attrs))e.setAttribute(key,value);if(text!==undefined)e.textContent=text;grid.append(e);};
 function setResult(value) {
  result=value;currentRow=null;grid.replaceChildren();$('steering-full-path').setAttribute('points','');$('steering-trail').setAttribute('points','');car.toggleAttribute('hidden',!result);$('steering-empty').toggleAttribute('hidden',!!result);
  if(!result){$('steering-scene-note').textContent='The full trajectory will fit automatically after a calculation.';return;}
  let minX=0,maxX=0,minY=0,maxY=0;for(const row of result.samples){minX=Math.min(minX,row.xM);maxX=Math.max(maxX,row.xM);minY=Math.min(minY,row.yM);maxY=Math.max(maxY,row.yM);}
  const rangeX=Math.max(10,maxX-minX),rangeY=Math.max(10,maxY-minY),scale=Math.min(640/rangeX,290/rangeY),cx=(minX+maxX)/2,cy=(minY+maxY)/2;
  fit={x:x=>410+(x-cx)*scale,y:y=>205-(y-cy)*scale,scale};
  for(let n=0;n<=4;n++){const xx=cx+rangeX*(n/4-.5),yy=cy+rangeY*(n/4-.5);add('line',{x1:fit.x(xx),x2:fit.x(xx),y1:45,y2:365,stroke:'#6786a0','stroke-opacity':.3});add('text',{x:fit.x(xx),y:390,'text-anchor':'middle'},xx.toFixed(1));add('line',{x1:95,x2:750,y1:fit.y(yy),y2:fit.y(yy),stroke:'#6786a0','stroke-opacity':.3});add('text',{x:88,y:fit.y(yy)+4,'text-anchor':'end'},yy.toFixed(1));}
  add('text',{x:410,y:425,'text-anchor':'middle'},'Global X (m)');add('text',{x:17,y:205,transform:'rotate(-90 17 205)','text-anchor':'middle'},'Global Y (m)');
  const step=Math.max(1,Math.ceil(result.samples.length/1500));fit.rows=result.samples.filter((_,i)=>i%step===0);if(fit.rows.at(-1)!==result.final)fit.rows.push(result.final);
  $('steering-full-path').setAttribute('points',fit.rows.map(row=>`${fit.x(row.xM)},${fit.y(row.yM)}`).join(' '));
  $('steering-scene-note').textContent=`Auto-fit axes in metres. The car is a fixed-size marker for visibility; body proportions use the shared GV70 reference, and wheelbase follows the model's ${(result.parameters.cgToFrontM+result.parameters.cgToRearM).toFixed(3)} m geometry.`;
 }
 function render(row) {
  if(!result)return;
  currentRow=row;
  const scale=40*800/(Math.max(260,$('steering-scene').clientWidth)*baseline.length_m);
  car.setAttribute('transform',`translate(${fit.x(row.xM).toFixed(3)} ${fit.y(row.yM).toFixed(3)}) rotate(${-row.headingDeg}) scale(${scale})`);
  for(const [name,x,side,front] of [['fl',result.parameters.cgToFrontM,-1,true],['fr',result.parameters.cgToFrontM,1,true],['rl',-result.parameters.cgToRearM,-1,false],['rr',-result.parameters.cgToRearM,1,false]]) $('steering-wheel-'+name).setAttribute('transform',`translate(${x} ${side*(front?baseline.front_track_m:baseline.rear_track_m)/2}) rotate(${front?-row.roadWheelAngleDeg:0})`);
  const trail=fit.rows.filter(sample=>sample.timeS<=row.timeS);if(trail.at(-1)!==row)trail.push(row);$('steering-trail').setAttribute('points',trail.map(sample=>`${fit.x(sample.xM)},${fit.y(sample.yM)}`).join(' '));
  $('steering-scene').dataset.sampleTime=row.timeS;
 }
 window.addEventListener('resize',()=>{if(currentRow)render(currentRow);});
 setResult(null);return {setResult,render};
}
