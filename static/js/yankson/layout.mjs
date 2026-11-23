/* Only presentation preferences survive a reload. No identity, input or permission state. */
export function mountInputLayout(bench, inputs, toolbar) {
  const key = `atu:yankson:layout:v1:${document.querySelector('#yp-workbench').dataset.user}`;
  let preferred = 360, collapsed = false;
  try {
    const saved = JSON.parse(localStorage.getItem(key) || 'null');
    if (Number.isFinite(saved?.width)) preferred = Math.min(600, Math.max(280, Math.round(saved.width/10)*10));
    collapsed = saved?.collapsed === true;
  } catch {}
  const toggle = document.createElement('button');
  toggle.id = 'ys-input-toggle'; toggle.className = 'btn btn-outline-primary'; toggle.type = 'button';
  toggle.setAttribute('aria-controls', inputs.id);
  const widthLabel = document.createElement('label');
  widthLabel.className = 'ys-width-control'; widthLabel.htmlFor = 'ys-input-width';
  widthLabel.textContent = 'Input panel width';
  const slider = document.createElement('input');
  slider.id = 'ys-input-width'; slider.type = 'range'; slider.min = '280'; slider.max = '600'; slider.step = '10';
  const widthText = document.createElement('span'); widthText.id = 'ys-width-value';
  slider.setAttribute('aria-describedby', widthText.id);
  widthLabel.append(slider, widthText); toolbar.append(toggle, widthLabel);
  const divider = document.createElement('div');
  divider.id = 'ys-input-divider'; divider.tabIndex = 0;
  divider.setAttribute('role','separator'); divider.setAttribute('aria-orientation','vertical');
  divider.setAttribute('aria-label','Resize input panel. Use left and right arrow keys.');
  divider.setAttribute('aria-controls', inputs.id);
  inputs.after(divider);
  const maximum = () => Math.floor(Math.max(280, Math.min(600, bench.clientWidth - 340))/10)*10;
  function save() {
    try { localStorage.setItem(key, JSON.stringify({width:preferred,collapsed})); } catch {}
  }
  function paint() {
    const width = Math.round(Math.min(maximum(), Math.max(280, preferred)));
    bench.style.setProperty('--ys-input-width',width+'px');
    bench.dataset.inputsCollapsed = String(collapsed);
    inputs.hidden = collapsed; divider.hidden = collapsed;
    toggle.textContent = collapsed ? 'Show inputs' : 'Collapse inputs';
    toggle.setAttribute('aria-expanded',String(!collapsed));
    slider.max = String(maximum()); slider.value = String(width); slider.disabled = collapsed;
    widthText.textContent = width+' px';
    divider.setAttribute('aria-valuemin','280'); divider.setAttribute('aria-valuemax',String(maximum()));
    divider.setAttribute('aria-valuenow',String(width)); divider.setAttribute('aria-valuetext',width+' pixels');
  }
  function resize(width) { preferred=Math.max(280,Math.min(maximum(),Math.round(width/10)*10));paint();save(); }
  toggle.onclick = () => { collapsed=!collapsed; paint(); save(); };
  slider.oninput = () => resize(Number(slider.value));
  divider.onkeydown = event => {
    const amount=event.shiftKey?40:10;
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
    event.preventDefault();
    resize(event.key==='Home'?280:event.key==='End'?maximum():Number(slider.value)+(event.key==='ArrowLeft'?-amount:amount));
  };
  let drag = null;
  divider.onpointerdown = event => {
    if(event.button!==0 || !event.isPrimary)return;
    event.preventDefault();divider.focus();divider.setPointerCapture(event.pointerId);
    drag={id:event.pointerId,x:event.clientX,width:Number(slider.value)};
  };
  divider.onpointermove = event => { if(drag?.id===event.pointerId)resize(drag.width+event.clientX-drag.x); };
  for(const event of ['pointerup','pointercancel','lostpointercapture']) divider.addEventListener(event,()=>{drag=null;});
  const observer=new ResizeObserver(paint);observer.observe(bench);paint();
  window.addEventListener('pagehide',()=>observer.disconnect(),{once:true});
}
