(() => {
 const host=document.getElementById('edward-lab');if(!host)return;
 const lab=EdwardBEV.mount(host),style=document.createElement('style');
 style.textContent=':host{display:block}h1{font-family:Georgia,serif}.tour-target-highlight{outline:3px solid #d6a73b!important;outline-offset:4px}';host.shadowRoot.append(style);
 window.addEventListener('pagehide',()=>lab.destroy(),{once:true});
 window.addEventListener('pageshow',event=>{if(event.persisted)location.reload();});
})();
