import {guideFor} from "./steps.mjs";

const root=document.getElementById("simulation-walkthrough");
if(root) initialise(root);

function initialise(root) {
  const byId=id=>document.getElementById(id), panel=byId("tour-panel"), launcher=byId("tour-launch");
  // Keep the page's own heading first, while retaining a shared base-template integration.
  const heading=document.querySelector("main .page-heading");
  if(heading)heading.after(root);
  const steps=guideFor(root.dataset.module,root.dataset.name), key=`atu:module-guide:v1:${root.dataset.user}:${root.dataset.module}`;
  let index=0, seen=false, activeTarget=null, addedTabindex=false, canStore=true;
  try {
    const saved=JSON.parse(localStorage.getItem(key) || "null");
    if(saved && typeof saved==="object") {seen=saved.seen===true;index=Number.isInteger(saved.step)?Math.max(0,Math.min(steps.length-1,saved.step)):0;}
  } catch {canStore=false;}
  function save(){try{localStorage.setItem(key,JSON.stringify({seen,step:index}));}catch{canStore=false;byId("tour-panel").querySelector(".tour-note").textContent="Browser storage is unavailable; this guide may appear again on your next visit.";}}
  if(!canStore)panel.querySelector(".tour-note").textContent="Browser storage is unavailable; this guide may appear again on your next visit.";
  function clearTarget(){if(!activeTarget)return;activeTarget.classList.remove("tour-target-highlight");if(addedTabindex)activeTarget.removeAttribute("tabindex");activeTarget=null;addedTabindex=false;}
  function render(){
    clearTarget();const step=steps[index];
    byId("tour-count").textContent=`Step ${index+1} of ${steps.length}`;
    byId("tour-progress-bar").value=(index+1)/steps.length;
    byId("tour-stage").textContent=step.stage;byId("tour-step-title").textContent=step.title;byId("tour-description").textContent=step.description;
    byId("tour-tip").textContent=step.tip?`Tip: ${step.tip}`:"";byId("tour-check").textContent=step.check?`Try / check: ${step.check}`:"";
    byId("tour-back").disabled=index===0;byId("tour-next").textContent=index===steps.length-1?"Finish guide":"Next";
    const target=step.target ? document.querySelector(step.target) : null;
    byId("tour-show").disabled=!target;byId("tour-target-status").textContent=target?"":"This step has no specific page location.";
    save();
  }
  function goToPanel(){panel.scrollIntoView({block:"start",behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"});panel.focus({preventScroll:true});}
  function open(scroll){panel.hidden=false;launcher.setAttribute("aria-expanded","true");seen=true;render();if(scroll)goToPanel();}
  function dismiss(){clearTarget();panel.hidden=true;launcher.dataset.panelVisible="false";launcher.setAttribute("aria-expanded","false");seen=true;save();launcher.focus({preventScroll:true});}
  launcher.addEventListener("click",()=>{if(panel.hidden)open(true);else goToPanel();});
  byId("tour-close").addEventListener("click",dismiss);byId("tour-skip").addEventListener("click",dismiss);
  panel.addEventListener("keydown",event=>{if(event.key==="Escape"){event.preventDefault();dismiss();}});
  byId("tour-back").addEventListener("click",()=>{if(index>0){index--;render();}});
  byId("tour-next").addEventListener("click",()=>{if(index<steps.length-1){index++;render();}else{index=0;dismiss();}});
  byId("tour-show").addEventListener("click",()=>{
    clearTarget();const target=steps[index].target && document.querySelector(steps[index].target);
    if(!target || !target.getClientRects().length){byId("tour-target-status").textContent="This section is not currently visible. Check whether it is collapsed, then try again.";return;}
    activeTarget=target;target.classList.add("tour-target-highlight");
    if(!target.matches("a, button, input, select, textarea, [tabindex]")){target.setAttribute("tabindex","-1");addedTabindex=true;}
    target.scrollIntoView({block:"center",behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"});target.focus({preventScroll:true});
    byId("tour-target-status").textContent="Section highlighted. Use Module guide to return to the walkthrough.";
  });
  window.addEventListener("pagehide",clearTarget);
  if("IntersectionObserver" in window) {
    const observer=new IntersectionObserver(entries=>{launcher.dataset.panelVisible=String(!panel.hidden&&entries[0].intersectionRatio>=.95);},{threshold:[0,.95,1]});
    observer.observe(panel);
  }
  root.hidden=false;
  if(!seen)open(false);
}
