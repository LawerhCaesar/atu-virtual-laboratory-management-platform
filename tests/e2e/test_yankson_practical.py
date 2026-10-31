import json
from datetime import datetime,timezone
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
MOCK="""window.SpeechRecognition=class {constructor(){window.recognizers??=[];window.recognizers.push(this);}start(){this.onstart?.();}abort(){} };"""
def open_lab(page,demo_records,live_server):
 page.add_init_script(MOCK)
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click()
 page.goto(live_server.url+'/virtual-lab/ice/authenticated-engine-starting/');page.locator('#tour-close').click();stamp=datetime(2026,1,1,tzinfo=timezone.utc);page.clock.install(time=stamp);page.clock.pause_at(stamp)
def contact(page,ms):
 target=page.locator('#yp-hold');target.focus()
 target.dispatch_event('keydown',{'key':' ','repeat':False});page.clock.run_for(ms);target.dispatch_event('keyup',{'key':' '});
def result(page,phrase,index=-1):
 page.evaluate("([phrase,index])=>{const results=[Object.assign([{transcript:phrase}],{isFinal:true})];window.recognizers.at(index).onresult({results});}",[phrase,index])
def test_voice_personalization_epoch_and_normal_time(page,demo_records,live_server):
 open_lab(page,demo_records,live_server)
 page.locator('#yp-listen').click();expect(page.locator('#yp-reason')).to_contain_text('No current voice permission')
 page.locator('#yp-practice').check();contact(page,300)
 expect(page.locator('#ys-auth')).to_contain_text('permission ·')
 page.locator('#yp-listen').click();result(page,'do not hey start');expect(page.locator('#yp-reason')).to_contain_text('Wrong command')
 page.locator('#yp-command').fill('Start my engine');page.locator('#yp-save').click();page.locator('#yp-listen').click();result(page,'START, MY ENGINE!');page.clock.run_for(4000)
 expect(page.locator('#ys-state')).to_contain_text('RUNNING');expect(page.locator('#ys-outputs')).to_contain_text('Starter OFF · Run supply ON')
 page.locator('#ys-reset').click();contact(page,300);page.locator('#yp-listen').click();page.locator('#ys-reset').click();result(page,'Start my engine');expect(page.locator('#ys-state')).to_contain_text('LOCKED')
 page.locator('#yp-default').click();expect(page.locator('#yp-command')).to_have_value('Hey Start')
 page.locator('#ys-speed').select_option('10');contact(page,500);expect(page.locator('#yp-reason')).to_contain_text('1×')

def test_circuit_cancel_parameters_and_exports(page,demo_records,live_server):
 open_lab(page,demo_records,live_server);page.locator('#yp-practice').check()
 page.locator('#yp-hold').dispatch_event('keydown',{'key':' ','repeat':False});page.clock.run_for(250);page.locator('#yp-hold').dispatch_event('blur')
 expect(page.locator('#ys-auth')).to_have_text('No voice permission')
 page.locator('#yp-circuit summary').click();page.locator('#yp-wire-canl').uncheck();page.clock.run_for(200)
 expect(page.locator('#yp-wiring-status')).to_contain_text('CANL is disconnected')
 contact(page,1700);expect(page.locator('#ys-state')).to_contain_text('LOCKED')
 page.locator('#yp-good').click();page.clock.run_for(200);contact(page,1700);page.clock.run_for(4000)
 expect(page.locator('#ys-state')).to_contain_text('RUNNING')
 with page.expect_download() as dl:page.locator('#ys-json').click()
 data=json.loads(Path(dl.value.path()).read_text());assert data['practical']['circuit']['canl'];assert len(data['columns'])==28;assert data['practical']['events']
 page.locator('#yp-parameters').evaluate("e=>e.closest('details').open=true")
 page.locator('#yp-param-3').fill('5');page.get_by_role('button',name='Apply parameters / new experiment').click()
 expect(page.locator('#ys-state')).to_contain_text('LOCKED');assert page.evaluate('YanksonLab.parameters[3]')==5
 page.locator('#yp-param-1').fill('1.4');page.locator('#yp-param-2').fill('1');page.get_by_role('button',name='Apply parameters / new experiment').click();expect(page.locator('#yp-parameter-error')).to_contain_text('Invalid')

@pytest.mark.parametrize('width',[1440,390])
def test_practical_visual_capabilities_and_errors(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});open_lab(page,demo_records,live_server)
 page.locator('#yp-check').click();expect(page.locator('#yp-capabilities')).to_contain_text('fingerprint contact timing: unavailable')
 page.locator('#yp-practice').check();contact(page,300);page.locator('#yp-listen').click();page.evaluate("window.recognizers.at(-1).onerror({error:'not-allowed'})");expect(page.locator('#yp-speech')).to_contain_text('denied')
 page.clock.resume();page.locator('#yp-circuit summary').click();Path('test-results/yankson-practical').mkdir(parents=True,exist_ok=True);page.screenshot(path=f'test-results/yankson-practical/desk-{width}.png',full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js');issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not issues,issues

def test_delayed_recognition_and_unavailable_services(page,demo_records,live_server):
 open_lab(page,demo_records,live_server);page.locator('#yp-practice').check();contact(page,300)
 page.locator('#yp-listen').click();page.locator('#yp-command').fill('My start');page.locator('#yp-save').click();result(page,'Hey Start');expect(page.locator('#ys-state')).to_contain_text('AUTHORIZED')
 page.locator('#yp-listen').click();page.clock.run_for(11000);result(page,'My start');expect(page.locator('#ys-state')).to_contain_text('LOCKED')
 page.locator('#ys-reset').click();contact(page,300);page.locator('#yp-listen').click();page.locator('#yp-stop-listening').click();result(page,'My start');expect(page.locator('#ys-state')).to_contain_text('AUTHORIZED')
 page.evaluate('delete window.SpeechRecognition;delete window.webkitSpeechRecognition');page.locator('#yp-listen').click();expect(page.locator('#yp-speech')).to_contain_text('unavailable')

def test_pointer_hold_one_shot_and_hidden_cancel(page,demo_records,live_server):
 open_lab(page,demo_records,live_server);page.locator('#yp-practice').check()
 hold=page.locator('#yp-hold');hold.scroll_into_view_if_needed();box=hold.bounding_box();page.mouse.move(box['x']+30,box['y']+30);page.mouse.down();page.clock.run_for(1900);page.mouse.up();page.clock.run_for(4000)
 expect(page.locator('#ys-state')).to_contain_text('RUNNING')
 with page.expect_download() as dl:page.locator('#ys-json').click()
 data=json.loads(Path(dl.value.path()).read_text());assert sum(r[10] for r in data['rows'])==1;assert any(e.get('source')=='mouse press' for e in data['practical']['events'])
 page.locator('#ys-reset').click();hold.focus();hold.dispatch_event('keydown',{'key':' ','repeat':False});page.clock.run_for(250)
 page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
 expect(page.locator('#ys-auth')).to_have_text('No voice permission');expect(page.locator('#ys-status')).to_contain_text('PAUSED')

@pytest.mark.parametrize('code,expected',[('audio-capture','No usable microphone'),('no-speech','No speech'),('network','network failure'),('aborted','cancelled'),('service-not-allowed','unavailable')])
def test_recognition_error_never_starts(page,demo_records,live_server,code,expected):
 open_lab(page,demo_records,live_server);page.locator('#yp-practice').check();contact(page,300);page.locator('#yp-listen').click()
 page.evaluate("code=>window.recognizers.at(-1).onerror({error:code})",code)
 expect(page.locator('#yp-speech')).to_contain_text(expected);expect(page.locator('#ys-state')).to_contain_text('AUTHORIZED')
 expect(page.locator('#yp-listen')).to_be_enabled()

def test_identity_rearm_epoch_and_parameter_countdown(page,demo_records,live_server):
 open_lab(page,demo_records,live_server);contact(page,1700);expect(page.locator('#ys-state')).to_contain_text('LOCKED')
 page.locator('#yp-practice').check();contact(page,300);page.locator('#yp-listen').click();contact(page,300);result(page,'Hey Start');expect(page.locator('#ys-state')).to_contain_text('AUTHORIZED')
 page.locator('#yp-listen').click();result(page,'Hey Start');result(page,'Hey Start');page.clock.run_for(4000);expect(page.locator('#ys-state')).to_contain_text('RUNNING')
 page.get_by_text('Timing and CAN parameters',exact=True).click();page.locator('#yp-param-3').fill('5');page.get_by_role('button',name='Apply parameters / new experiment').click();contact(page,300)
 page.locator('#ys-run').click()
 remaining=page.evaluate('YanksonLab.parameters[3]-(YanksonLab.row[0]-YanksonLab.row[24])')
 assert 4.5<remaining<=5
 expect(page.locator('#ys-auth')).to_contain_text(f'{remaining:.2f} s remaining')
