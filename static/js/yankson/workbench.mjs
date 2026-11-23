/* Relocate the existing controls without replacing listeners or the controller. */
const { mountInputLayout } = await import(window.YanksonAssetURL('./layout.mjs', import.meta.url));
export function mountWorkbench() {
  const get=s=>document.querySelector(s), app=get('#yp-workbench');
  const originalSimulation=get('#ys-short').closest('details');
  const bench=document.createElement('div');bench.id='ys-workbench';
  const toolbar=document.createElement('div');toolbar.id='ys-layout-toolbar';toolbar.setAttribute('aria-label','Workspace layout');
  const left=document.createElement('aside');left.id='ys-inputs';left.setAttribute('aria-label','Inputs and controls');
  const right=document.createElement('section');right.id='ys-output-pane';right.setAttribute('aria-label','Outputs and results');
  app.before(toolbar,bench);bench.append(left,right);
  const workflow=document.createElement('p');workflow.className='ys-workflow';
  workflow.textContent='1 · Check microphone → 2 · Authorise by contact → 3 · Say “Start”';left.append(workflow);
  const quick=document.createElement('div');quick.id='ys-quick-controls';
  const quickButtons=document.createElement('div');quickButtons.className='ys-quick-buttons';
  const clock=get('#ys-run').closest('section');
  quickButtons.append(get('#ys-reset'),get('#ys-stop'));quick.append(quickButtons);left.append(quick);
  function details(parent,title,id) {
    const box=document.createElement('details');box.className='ys-input-group';if(id)box.id=id;
    const summary=document.createElement('summary');summary.textContent=title;box.append(summary);parent.append(box);return box;
  }
  function step(title,id) {
    const section=document.createElement('section');section.className='ys-basic-step';section.id=id;
    const heading=document.createElement('h3');heading.textContent=title;section.append(heading);left.append(section);return section;
  }
  const micStep=step('1 · Check microphone','ys-microphone-step');
  micStep.append(get('#ya-mic-start').parentElement);
  const micHelp=document.createElement('p');micHelp.className='small';micHelp.textContent='Allow access and speak; check the waveform on the right.';micStep.append(micHelp);
  const voiceCheck=get('#yp-test-phrase');voiceCheck.textContent='Test spoken command';
  voiceCheck.className='btn btn-outline-primary';micStep.append(voiceCheck);
  const voiceHelp=document.createElement('p');voiceHelp.className='small';voiceHelp.textContent='Check recognition first: say the target phrase and read the transcript. This test never starts the engine and needs no contact hold.';micStep.append(voiceHelp);
  const padHelp=get('#yp-hold').nextElementSibling?.classList.contains('ya-help')?get('#yp-hold').nextElementSibling:null;
  const listenTip=get('#yp-listen').nextElementSibling?.classList.contains('ya-help')?get('#yp-listen').nextElementSibling:null;
  const identityTip=get('#ya-verify').nextElementSibling?.classList.contains('ya-help')?get('#ya-verify').nextElementSibling:null;
  const contactStep=step('2 · Authorise by contact','ys-contact-step');
  const identityControls=document.createElement('div');identityControls.className='ys-identity-controls';
  identityControls.append(get('#ya-verify'));if(identityTip)identityControls.append(identityTip);identityControls.append(get('#yp-practice').closest('label'));contactStep.append(identityControls);
  const controls=document.createElement('div');controls.className='ys-contact-controls';
  controls.append(get('#yp-hold'),get('#yp-contact-timer'));
  if(padHelp){controls.classList.add('ys-contact-with-help');controls.append(padHelp);}
  contactStep.append(controls);contactStep.append(get('#yp-progress'),get('#yp-contact-classification'),get('#yp-thresholds'));
  const longHint=document.createElement('p');longHint.className='small';longHint.textContent='Short release → Listen. Long hold starts directly.';contactStep.append(longHint);
  const speak=step('3 · Say “Start”','ys-speech-step');speak.querySelector('h3').id='ys-say-title';
  const listenButtons=document.createElement('div');listenButtons.className='ys-quick-buttons';
  listenButtons.append(get('#yp-listen'),get('#yp-stop-listening'));if(listenTip)listenButtons.append(listenTip);speak.append(listenButtons,get('#yp-listen-help'));
  const advanced=details(left,'Advanced settings','ys-input-advanced');
  function group(title,nodes,id) { const section=details(advanced,title,id);for(const node of nodes.filter(Boolean))section.append(node);return section; }
  group('Device registration and capabilities',[get('.ys-device-panel'),get('#yp-check'),get('#yp-capabilities')]);
  group('Optional command personalisation',[get('#yp-command').closest('section')],'ys-personalisation');
  group('Run clock and model pacing',[clock]);
  const master=get('#lab-master-reset');if(master)group('Master reset',[master.parentElement]);
  group('Simulated test events and original supervisor display',[get('#ys-short').closest('section')],'ys-simulated-inputs');
  group('Components and connections',[get('#yp-circuit')]);
  group('Electrical inputs',[get('#ya-electric-fields'),get('#ya-check').parentElement]);
  group('Calibration and supervisor faults',[get('#yp-parameters').closest('details'),get('#ys-faults')]);
  group('Guided experiments',[get('#yp-experiments').closest('details')]);
  group('Lecturer exercises',[get('#ya-exercise-title').closest('details')]);
  group('Output view and camera',[get('#ya-tab-engine').closest('nav'),get('#ya-camera-wide').parentElement]);
  const title=document.createElement('h2');title.textContent='Live response';right.append(title);
  const strip=document.createElement('div');strip.id='ys-readiness-strip';strip.setAttribute('aria-label','Current starting status');right.append(strip);
  const feedback=document.createElement('section');feedback.id='ys-live-feedback';feedback.className='content-panel';
  const feedbackTitle=document.createElement('h3');feedbackTitle.textContent='Listen and observe';
  const permission=document.createElement('output');permission.id='ys-permission-countdown';permission.setAttribute('aria-label','Voice permission remaining');
  const deviceStatus=get('#ya-device-status');
  get('.ys-device-panel').append(deviceStatus);
  const identityGuidance=document.createElement('p');identityGuidance.id='ys-identity-guidance';identityGuidance.setAttribute('role','status');
  function syncIdentityGuidance() {
    identityGuidance.textContent=get('#yp-practice').checked ? 'Practice identity selected (simulated). Device verification is not required for this practice route; use the contact pad.' : deviceStatus.textContent;
  }
  new MutationObserver(syncIdentityGuidance).observe(deviceStatus,{subtree:true,childList:true,characterData:true});
  get('#yp-practice').addEventListener('change',syncIdentityGuidance);
  syncIdentityGuidance();
  feedback.append(feedbackTitle,identityGuidance,permission,get('#yp-speech'),get('#yp-transcript'),get('#yp-reason'),get('#yp-start-source'));
  const phraseCheck=get('#yp-phrase-check');phraseCheck.hidden=true;feedback.append(phraseCheck);
  voiceCheck.addEventListener('click',()=>{
    phraseCheck.hidden=false;
    const bounds=feedback.getBoundingClientRect();
    if(bounds.top<0 || bounds.bottom>innerHeight)feedback.scrollIntoView({block:'start',behavior:'instant'});
  });
  right.append(feedback);
  get('#yp-listen').addEventListener('click',()=>{
    const bounds=feedback.getBoundingClientRect();
    if(bounds.top<0 || bounds.bottom>innerHeight)feedback.scrollIntoView({block:'start',behavior:'instant'});
  });
  const microphone=get('#ya-microphone');right.append(microphone);microphone.querySelector('details').open=true;
  const technical=details(right,'Advanced settings · diagnostics and records','ys-output-advanced');
  details(technical,'Microphone sample bytes (diagnostic)','ys-microphone-bytes').append(get('#ya-mic-bytes'));
  const oldStatus=get('.yp-status-grid');
  const detailed=details(technical,'Detailed readiness, contact and latest decision','ys-status-details');detailed.append(oldStatus);
  for(const selector of ['#yp-contact-result','#yp-diagnostic-count','#ys-contact','#ys-auth','#ys-reject']) detailed.append(get(selector));
  const latestSpeech=document.createElement('p');latestSpeech.id='ys-latest-speech';latestSpeech.className='small';technical.append(latestSpeech);
  const wiring=get('.yp-diagram-scroll');get('#ya-circuit-panel').prepend(wiring);get('#ya-circuit-panel').append(get('#yp-wiring-status'));
  const results=get('#ya-results');right.insertBefore(results,technical);
  technical.append(get('#ya-signals-panel'),get('#ya-circuit-panel'),get('#ys-supervisor'),get('#ys-chart').closest('section'),get('#ys-results'));
  const guideDownload=get('#ya-learning a[download]');if(guideDownload)technical.append(guideDownload);
  for(const name of ['signals','circuit'])get('#ya-tab-'+name).addEventListener('click',()=>{technical.open=true;});
  const stateOutputs=[];
  function refresh(row=window.YanksonLab.row) {
    syncIdentityGuidance();
    const metadata=window.YanksonPractical.readiness();
    const values=[['Identity',get('#yp-identity-source').textContent.replace('Identity: ','')],['Engine',get('#yp-engine-state').textContent.replace('Virtual engine: ','')],['Starter',row[3]?'ON':'OFF'],['Run supply',row[7]?'ON':'OFF']];
    if(!stateOutputs.length) for(const [label] of values){const card=document.createElement('div'),name=document.createElement('strong'),value=document.createElement('span');name.textContent=label;card.append(name,value);strip.append(card);stateOutputs.push(value);}
    values.forEach((entry,i)=>stateOutputs[i].textContent=entry[1]);
    permission.textContent=metadata.permissionSecondsRemaining>0?metadata.permissionSecondsRemaining.toFixed(1)+' s voice permission remaining':'No current voice permission';
    get('#ys-say-title').textContent='3 · Say “'+metadata.activeCommand+'”';
    workflow.textContent='1 · Check microphone → 2 · Authorise by contact → 3 · Say “'+metadata.activeCommand+'”';
    latestSpeech.textContent=get('#yp-transcript').textContent+' · '+get('#yp-diagnostic-count').textContent;
  }
  for(const name of ['sample','microphone','evidence','command','pause','reset','stop','run-start'])window.addEventListener('yankson:'+name,event=>refresh(name==='sample'?event.detail:undefined));
  refresh();mountInputLayout(bench,left,toolbar);
  const guideLauncher=get("#tour-launch");if(guideLauncher)toolbar.append(guideLauncher);
  app.hidden=true;app.setAttribute('aria-hidden','true');
  // The original wrapper is now empty; retain only the moved controls.
  if(originalSimulation && !originalSimulation.querySelector('input,button,section'))originalSimulation.remove();
  window.dispatchEvent(new Event('yankson:workbench-ready'));
}
