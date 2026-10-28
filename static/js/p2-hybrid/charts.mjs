export const COLORS=['#245abd','#a34f1d','#087e74','#773b9c'];
export const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
export const svgEl=(tag,attrs={},text)=>{const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;return e;};
export function download(content,name,type){const a=make('a');const url=URL.createObjectURL(new Blob([content],{type}));a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export function exportSvg(svg,name){const clone=svg.cloneNode(true);clone.setAttribute('xmlns','http://www.w3.org/2000/svg');clone.setAttribute('viewBox','0 -80 500 350');
 const figure=svg.closest('figure'),caption=figure?.querySelector('figcaption')?.textContent||svg.getAttribute('aria-label')||name,legend=[...(figure?.querySelectorAll('.p2-chart-legend span')||[])].map(e=>e.textContent).join(' · ');
 function wrap(text,y){const words=text.split(/\s+/);let line='',lines=[];for(const word of words){if((line+' '+word).length>65){lines.push(line);line=word;}else line+=(line?' ':'')+word;}if(line)lines.push(line);for(const [i,t]of lines.slice(0,2).entries())clone.append(svgEl('text',{x:20,y:y+i*17,'font-size':12,fill:'#344c5c'},t));}
 wrap(caption,-60);wrap(legend,-23);clone.querySelectorAll('text').forEach(e=>{e.setAttribute('fill','#344c5c');e.setAttribute('font-family','sans-serif');e.setAttribute('font-size',e.getAttribute('y')<0?'12':'14');});download(new XMLSerializer().serializeToString(clone),name+'.svg','image/svg+xml');}
export function linePlot(svg,rows,series,start,end,cursorTime){
 svg.replaceChildren();const add=(tag,attrs,text)=>{const el=svgEl(tag,attrs,text);svg.append(el);return el;};
 svg.setAttribute('viewBox','0 0 500 270');
 if(!rows?.length){add('text',{x:250,y:120,'text-anchor':'middle'},'Run a simulation to view results');return;}
 const selected=rows.filter(r=>r.time_s>=start&&r.time_s<=end);if(!selected.length)return;
 let min=0,max=0;for(const row of selected)for(const s of series){min=Math.min(min,row[s.key]);max=Math.max(max,row[s.key]);}const pad=(max-min||1)*.07;min-=pad;max+=pad;
 const x=t=>75+(t-start)/(end-start||1)*395,y=v=>205-(v-min)/(max-min)*170;
 for(let i=0;i<=4;i++){const v=min+(max-min)*i/4,t=start+(end-start)*i/4;add('line',{x1:75,x2:470,y1:y(v),y2:y(v),stroke:'#e1e7ee'});add('text',{x:68,y:y(v)+4,'text-anchor':'end'},Math.abs(v)>=10000?v.toExponential(1).replace('e+','e'):v.toFixed(Math.abs(v)<10?2:0));add('text',{x:x(t),y:227,'text-anchor':'middle'},t.toFixed(2));}
 add('text',{x:275,y:255,'text-anchor':'middle'},'Time (s)');add('text',{x:10,y:120,transform:'rotate(-90 10 120)','text-anchor':'middle'},series[0].unit);
 // Keep each bucket's extrema for every series, including abrupt protection events.
 const keep=new Set([0,selected.length-1]),bucket=Math.max(1,Math.ceil(selected.length/150));
 for(let i=0;i<selected.length;i+=bucket){const end=Math.min(selected.length,i+bucket);keep.add(i);keep.add(end-1);for(const s of series){let lo=i,hi=i;for(let j=i+1;j<end;j++){if(selected[j][s.key]<selected[lo][s.key])lo=j;if(selected[j][s.key]>selected[hi][s.key])hi=j;}keep.add(lo);keep.add(hi);}}
 const points=[...keep].sort((a,b)=>a-b).map(i=>selected[i]);series.forEach((s,i)=>add('polyline',{points:points.map(r=>`${x(r.time_s).toFixed(2)},${y(r[s.key]).toFixed(2)}`).join(' '),fill:'none',stroke:COLORS[i%4],'stroke-width':2.2,'stroke-dasharray':i?`${8-i} ${3+i}`:'none'}));
 const cursor=add('line',{x1:x(cursorTime),x2:x(cursorTime),y1:30,y2:205,stroke:'#526476','stroke-dasharray':'3 3','data-cursor':''});cursor.setAttribute('visibility',cursorTime>=start&&cursorTime<=end?'visible':'hidden');
}
export function createCharts(container,info,onTime){
 const lookup=Object.fromEntries(info.signals.map(s=>[s.key,s])),charts=[];let result=null,start=0,end=30,current=0;
 for(const[groupIndex,g]of info.scope_groups.entries()){
  const section=make('section',undefined,'p2-plot-group');section.dataset.scopeGroup=g.name;const title=make('h3',g.name,'h4');title.id=`p2-group-${groupIndex}`;section.setAttribute('aria-labelledby',title.id);const grid=make('div',undefined,'p2-chart-grid');section.append(title,grid);container.append(section);
  for(const keys of g.panels){const series=keys.map(k=>lookup[k]),f=make('figure'),caption=make('figcaption',series.map(s=>s.label).join(' / ')+` (${series[0].unit})`),legend=make('p',undefined,'p2-chart-legend'),svg=svgEl('svg',{role:'img','aria-label':caption.textContent+' versus time (s)'}),readout=make('p','Use recorded time to inspect a sample.','p2-chart-readout'),save=make('button','Export chart SVG','btn btn-sm btn-outline-secondary');save.type='button';save.disabled=true;
   series.forEach((s,i)=>{const span=make('span',`${['Solid','Dashed','Dotted'][i]}: ${s.label}`);span.style.setProperty('--series-color',COLORS[i]);legend.append(span);});
   save.addEventListener('click',()=>exportSvg(svg,`p2-${keys[0]}`));f.append(caption,legend,svg,readout,save);grid.append(f);const chart={svg,series,readout,save};charts.push(chart);
   const inspect=e=>{if(!result)return;const r=svg.getBoundingClientRect(),v=(e.clientX-r.left)/r.width*500;onTime(Math.max(start,Math.min(end,start+(v-75)/395*(end-start))));};svg.addEventListener('pointermove',inspect);svg.addEventListener('click',inspect);
  }
 }
 function draw(){for(const c of charts){linePlot(c.svg,result?.time_series,c.series,start,end,current);c.save.disabled=!result;}}
 function cursor(row){if(!result)return;current=row.time_s;for(const c of charts){const x=75+(current-start)/(end-start||1)*395;const l=c.svg.querySelector('[data-cursor]');if(l){l.setAttribute('x1',x);l.setAttribute('x2',x);l.setAttribute('visibility',current>=start&&current<=end?'visible':'hidden');}c.readout.textContent=`${current.toFixed(3)} s · `+c.series.map(s=>`${s.label}: ${row[s.key].toFixed(4)} ${s.unit}`).join(' · ');let title=c.svg.querySelector('title');if(!title){title=svgEl('title');c.svg.append(title);}title.textContent=c.readout.textContent;}}
 draw();return {setResult(r){result=r;start=0;end=r?.inputs.duration_s||30;draw();},cursor,zoom(reset=false){if(!result)return;const duration=result.inputs.duration_s,span=reset?duration:Math.max(duration/16,(end-start)/2);start=Math.max(0,Math.min(duration-span,current-span/2));end=start+span;draw();cursor(result.time_series[Math.min(result.time_series.length-1,Math.round(current/result.inputs.time_step_s))]);return[start,end];}};
}
