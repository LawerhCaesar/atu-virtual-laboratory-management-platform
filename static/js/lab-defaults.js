/* A fresh module mount restores model inputs/calibration without deleting saved work. */
(()=>{const button=document.getElementById('lab-master-reset');if(button)button.addEventListener('click',()=>{button.disabled=true;button.textContent='Restoring defaults…';location.assign(location.pathname);});})();
