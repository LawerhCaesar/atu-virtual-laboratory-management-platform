from datetime import datetime,timezone
import pytest
from playwright.sync_api import expect
from test_yankson_practical import contact
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
def login(page,user,live_server):
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address or index number',exact=True).fill(user.email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click();page.goto(live_server.url+'/virtual-lab/ice/authenticated-engine-starting/');page.locator('#tour-close').click();expect(page.locator('#ya-tab-engine')).to_be_visible()
def test_real_webauthn_ceremony_and_fault_recovery(page,demo_records,live_server):
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 cdp=page.context.new_cdp_session(page);cdp.send('WebAuthn.enable');cdp.send('WebAuthn.addVirtualAuthenticator',{'options':{'protocol':'ctap2','transport':'internal','hasResidentKey':True,'hasUserVerification':True,'isUserVerified':True,'automaticPresenceSimulation':True}})
 login(page,demo_records['student'],live_server)
 page.locator('#ya-register').click();expect(page.locator('#ya-device-status')).to_contain_text('Device registered',timeout=20000)
 expect(page.locator('#yp-identity-source')).to_contain_text('none')
 def corrupt(route):
  import json
  payload=route.request.post_data_json;payload['response']['signature']='AA';route.continue_(post_data=json.dumps(payload))
 page.route('**/device/verify/complete/',corrupt);page.locator('#ya-verify').click();expect(page.locator('#ya-device-status')).to_contain_text('could not be verified',timeout=20000);expect(page.locator('#yp-identity-source')).to_contain_text('none');page.unroute('**/device/verify/complete/',corrupt)
 page.locator('#ya-verify').click();expect(page.locator('#ya-device-status')).to_contain_text('Device verified',timeout=20000)
 expect(page.locator('#yp-practice')).not_to_be_checked()
 stamp=datetime(2026,1,1,tzinfo=timezone.utc);page.clock.install(time=stamp);page.clock.pause_at(stamp)
 contact(page,1700);page.clock.run_for(4000);expect(page.locator('#ys-state')).to_contain_text('RUNNING')
 page.locator('#ys-reset').click();expect(page.locator('#yp-identity-source')).to_contain_text('none')
 page.locator('#ya-tab-circuit').click();page.locator('#ya-electrical-canHighV').fill('1.5');page.locator('#ya-check').click();expect(page.locator('#ya-preflight')).to_contain_text('failed')
 page.locator('#yp-practice').check();contact(page,1700);page.clock.run_for(1000);expect(page.locator('#ys-state')).to_contain_text('LOCKED')
 page.locator('#ya-good').click();contact(page,1700);page.clock.run_for(4000);expect(page.locator('#ys-state')).to_contain_text('RUNNING')
 page.locator('#ya-tab-signals').click();expect(page.locator('#ya-can')).to_contain_text('expected DLC 8');expect(page.locator('#ya-chain')).to_contain_text('RUNNING')
 assert not errors,errors

def test_staff_question_persistence_and_student_copy(page,demo_records,live_server):
 login(page,demo_records['lecturer'],live_server);page.locator('#ya-tab-circuit').click();page.locator('#ya-electrical-terminationOhm').fill('120');page.locator('#ya-exercise-title').fill('Find the missing terminator');page.locator('#ya-instructions').fill('Repair CAN termination and prove starting with valid feedback.');page.locator('#ya-save-exercise').click();expect(page.locator('#ya-exercise-status')).to_contain_text('Exercise saved')
 from apps.core.models import StartingExercise
 exercise=StartingExercise.objects.get(title='Find the missing terminator');assert exercise.owner_id==demo_records['lecturer'].pk
 page.context.clear_cookies();login(page,demo_records['student'],live_server);page.locator('#ya-tab-circuit').click();page.locator('#ya-exercise-id').fill(str(exercise.pk));page.locator('#ya-load-exercise').click();expect(page.locator('#ya-exercise-status')).to_contain_text('Loaded Find');expect(page.locator('#ya-electrical-terminationOhm')).to_have_value('120');expect(page.locator('#ya-preflight')).to_contain_text('failed')
 page.locator('#ya-electrical-terminationOhm').fill('60');page.locator('#ya-save-exercise').click();expect(page.locator('#ya-exercise-status')).to_contain_text('Lecturer or administrator required');exercise.refresh_from_db();assert exercise.configuration['electrical']['terminationOhm']==120

@pytest.mark.parametrize('width',[1440,390])
def test_revision_views_guide_and_accessibility(page,demo_records,live_server,width):
 from pathlib import Path
 from test_yankson_practical import MOCK,result
 page.set_viewport_size({'width':width,'height':1000});page.add_init_script(MOCK);login(page,demo_records['student'],live_server)
 expect(page.locator('#ya-stand canvas')).to_be_visible(timeout=15000);expect(page.locator('#ya-learning')).to_contain_text('Controller parameter glossary')
 stamp=datetime(2026,1,1,tzinfo=timezone.utc);page.clock.install(time=stamp);page.clock.pause_at(stamp)
 page.locator('#yp-practice').check();contact(page,300);page.locator('#yp-listen').click();result(page,'Hey Start');page.clock.run_for(4000)
 page.locator('#ya-tab-signals').click();expect(page.locator('#ya-binary')).to_contain_text('01101000');expect(page.locator('#ya-command')).to_contain_text('00000001');expect(page.locator('#ya-chain')).to_contain_text('RUNNING')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.evaluate('YanksonLab.pause()');page.clock.resume()
 page.add_script_tag(path='node_modules/axe-core/axe.min.js');issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not issues,issues
 page.clock.resume();folder=Path('test-results/yankson-revision');folder.mkdir(parents=True,exist_ok=True)
 for tab in ['engine','signals','circuit']:
  page.locator('#ya-tab-'+tab).click();page.locator('#ya-results').scroll_into_view_if_needed();page.screenshot(path=str(folder/f'{tab}-{width}.png'))
  if tab=='engine':
   page.locator('#ya-camera-starter').click();page.screenshot(path=str(folder/f'starter-closeup-{width}.png'));page.locator('#ya-camera-wide').click()
 link=page.get_by_role('link',name='Download complete learning guide (PDF)');assert page.request.get(link.get_attribute('href')).status==200

def test_ideal_fuse_latches_until_repaired_and_replaced(page,demo_records,live_server):
 login(page,demo_records['student'],live_server);stamp=datetime(2026,1,1,tzinfo=timezone.utc);page.clock.install(time=stamp);page.clock.pause_at(stamp)
 page.locator('#yp-practice').check();page.locator('#ya-tab-circuit').click();page.locator('#ya-electrical-fuseA').fill('100');contact(page,1700);page.clock.run_for(100)
 expect(page.locator('#ya-electrical-values')).to_contain_text('fuse OPEN');page.locator('#ys-reset').click();expect(page.locator('#ya-electrical-values')).to_contain_text('fuse OPEN')
 page.locator('#ya-fuse').click();expect(page.locator('#ya-preflight')).to_contain_text('Overload still present')
 page.locator('#ya-electrical-fuseA').fill('250');page.locator('#ya-fuse').click();expect(page.locator('#ya-electrical-values')).to_contain_text('fuse intact');contact(page,1700);page.clock.run_for(4000);expect(page.locator('#ys-state')).to_contain_text('RUNNING')

def test_microphone_permission_failure_and_local_analyser(page,demo_records,live_server):
 login(page,demo_records['student'],live_server);page.locator('#ya-tab-signals').click();page.get_by_text('Check your actual microphone · waveform and sample bytes',exact=True).click()
 page.evaluate("()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('denied','NotAllowedError')}}")
 page.locator('#ya-mic-start').click();expect(page.locator('#ya-mic-status')).to_contain_text('permission denied')
 page.evaluate("""()=>{navigator.mediaDevices.getUserMedia=async()=>{window.testAudio=new AudioContext();const o=testAudio.createOscillator(),d=testAudio.createMediaStreamDestination();o.frequency.value=220;o.connect(d);o.start();await testAudio.resume();window.testMicStream=d.stream;return d.stream;};}""")
 page.locator('#ya-mic-start').click();expect(page.locator('#ya-mic-bytes')).to_contain_text('Latest 16',timeout=10000);expect(page.locator('#ya-mic-status')).to_contain_text('samples/s')
 page.locator('#ya-mic-stop').click();expect(page.locator('#ya-mic-bytes')).to_contain_text('No retained');assert page.evaluate("testMicStream.getTracks().every(t=>t.readyState==='ended')");page.evaluate('testAudio.close()')
