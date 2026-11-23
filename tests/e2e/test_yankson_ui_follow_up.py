"""Local UI review. Recognition callbacks are mocked, not human-speech evidence."""
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_yankson_practical import MOCK,contact,result,freeze_lab_clock
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]

def basic_lab(page,demo_records,live_server,width=1440):
 page.set_viewport_size({'width':width,'height':950});page.emulate_media(reduced_motion='reduce');page.add_init_script(MOCK)
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address or index number',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click()
 page.goto(live_server.url+'/virtual-lab/ice/authenticated-engine-starting/');page.locator('#tour-close').click();page.locator('#ye-record').wait_for(state='attached');freeze_lab_clock(page)

@pytest.mark.parametrize('width',[1440,390])
def test_simple_default_and_accessibility(page,demo_records,live_server,width):
 basic_lab(page,demo_records,live_server,width)
 assert not page.locator('#ys-input-advanced').evaluate('e=>e.open')
 assert not page.locator('#ys-output-advanced').evaluate('e=>e.open')
 expect(page.locator('#ys-say-title')).to_have_text('3 · Say “Start”')
 for selector in ['#yp-hold','#yp-contact-timer','#yp-listen','#ya-mic-start']:
  expect(page.locator(selector)).to_be_visible()
 boxes=[page.locator(s).bounding_box() for s in ['#yp-hold','#yp-contact-timer','#yp-listen']]
 assert max(b['y']+b['height'] for b in boxes)-min(b['y'] for b in boxes)<340
 assert not page.locator('#ys-output-pane input,#ys-output-pane select,#ys-output-pane textarea').count()
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 expect(page.locator('#ya-engine-panel')).to_contain_text('Future concept')
 assert 'physical objective was not achieved' not in page.locator('main').inner_text().lower()
 page.evaluate('YanksonLab.pause()');page.clock.resume();page.add_script_tag(path='node_modules/axe-core/axe.min.js')
 issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not issues,issues
 folder=Path('test-results/yankson-ui-follow-up');folder.mkdir(parents=True,exist_ok=True)
 page.locator('#ya-stand').scroll_into_view_if_needed();expect(page.locator('#ya-stand canvas')).to_be_visible(timeout=15000);expect(page.locator('#ya-stand-status')).to_contain_text('State',timeout=15000)
 page.locator('#ys-workbench').screenshot(path=str(folder/f'default-{width}.png'))

@pytest.mark.parametrize('milliseconds,label',[(140,'Rejected'),(150,'short contact'),(1490,'short contact'),(1500,'long contact'),(1510,'long contact')])
def test_measured_boundaries_and_frozen_release(page,demo_records,live_server,milliseconds,label):
 basic_lab(page,demo_records,live_server);page.locator('#yp-practice').check()
 expect(page.locator('#yp-contact-timer')).to_have_text('0.00 s')
 contact(page,milliseconds)
 expect(page.locator('#yp-contact-timer')).to_have_text(f'{milliseconds/1000:.2f} s')
 expect(page.locator('#yp-contact-classification')).to_contain_text(label)
 frozen=page.locator('#yp-contact-timer').inner_text();page.clock.run_for(200);expect(page.locator('#yp-contact-timer')).to_have_text(frozen)
 expect(page.locator('#yp-contact-result')).to_contain_text('0.01 s controller sampling')
 data=page.evaluate('YanksonLab.snapshot()');folder=Path('test-results/yankson-ui-follow-up');folder.mkdir(parents=True,exist_ok=True)
 (folder/f'boundary-{milliseconds}.json').write_text(json.dumps({'wallHoldMs':milliseconds,'classification':label,'modelContactMaxS':max(r[12] for r in data['rows']),'longEvents':sum(r[10] for r in data['rows']),'startRequests':sum(r[13] for r in data['rows']),'authorizedAfterRelease':bool(page.evaluate('YanksonLab.row[2]')),'displayedControllerDecision':page.locator('#yp-contact-classification').inner_text(),'source':'automated keyboard hold, not human speech'},indent=2))

@pytest.mark.parametrize('cancel',['blur','pointercancel','reset'])
def test_cancelled_contact_and_reset_never_start(page,demo_records,live_server,cancel):
 basic_lab(page,demo_records,live_server);page.locator('#yp-practice').check();pad=page.locator('#yp-hold');pad.focus();pad.dispatch_event('keydown',{'key':' ','repeat':False});page.clock.run_for(300)
 assert .27 <= float(page.locator('#yp-contact-timer').inner_text().split()[0]) <= .30
 if cancel=='reset':page.locator('#ys-reset').click()
 else:pad.dispatch_event(cancel)
 page.clock.run_for(200)
 assert not page.evaluate('YanksonLab.row[2] || YanksonLab.row[3]')
 assert not page.evaluate('YanksonLab.snapshot().rows.some(r=>r[13])')
 assert page.locator('#yp-progress').evaluate('e=>e.value')==0
 if cancel=='reset':expect(page.locator('#yp-contact-timer')).to_have_text('0.00 s')
 else:expect(page.locator('#yp-contact-classification')).to_contain_text('Rejected: cancelled')


def test_direct_hold_one_shot_and_mocked_voice_source(page,demo_records,live_server):
 basic_lab(page,demo_records,live_server);page.locator('#yp-practice').check();contact(page,5000)
 expect(page.locator('#yp-start-source')).to_contain_text('long contact (measured screen pad)')
 assert page.evaluate('YanksonLab.snapshot().rows.reduce((n,r)=>n+r[10],0)')==1
 page.locator('#ys-reset').click();contact(page,300)
 expect(page.locator('#ys-permission-countdown')).to_contain_text('voice permission remaining')
 page.locator('#yp-listen').click();result(page,'Hey Start')
 expect(page.locator('#yp-reason')).to_contain_text('Wrong command')
 assert not page.evaluate('YanksonLab.row[3]')
 page.locator('#yp-listen').click();result(page,'Start');page.clock.run_for(4000)
 expect(page.locator('#ys-state')).to_contain_text('RUNNING')
 expect(page.locator('#yp-start-source')).to_contain_text('accepted voice (browser recognition)')
 page.locator('#ys-reset').click();expect(page.locator('#ys-permission-countdown')).to_have_text('No current voice permission')
 page.locator('#yp-listen').click();expect(page.locator('#yp-reason')).to_contain_text('No current voice permission')
 expect(page.locator('#yp-listen-help')).to_contain_text('Unavailable')


def test_keyboard_mouse_width_and_layout_only_restore(page,demo_records,live_server):
 basic_lab(page,demo_records,live_server)
 divider=page.locator('#ys-input-divider');divider.focus();before=int(divider.get_attribute('aria-valuenow'));divider.press('ArrowRight');assert int(divider.get_attribute('aria-valuenow'))==before+10
 box=divider.bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+20);page.mouse.down();page.mouse.move(box['x']+box['width']/2+40,box['y']+20);page.mouse.up();assert int(divider.get_attribute('aria-valuenow'))>before+10
 page.locator('#yp-practice').check();contact(page,300);assert page.evaluate('YanksonLab.row[2]')
 page.locator('#ys-input-toggle').click();expect(page.locator('#ys-inputs')).to_be_hidden();expect(page.locator('#ys-output-pane')).to_be_visible()
 preference=page.evaluate("JSON.parse(localStorage.getItem('atu:yankson:layout:v1:'+document.querySelector('#yp-workbench').dataset.user))")
 assert set(preference)=={'width','collapsed'}
 page.clock.resume();page.reload();page.locator('#ye-record').wait_for(state='attached')
 if page.locator('#tour-close').is_visible():page.locator('#tour-close').click()
 expect(page.locator('#ys-inputs')).to_be_hidden();assert not page.evaluate('YanksonLab.row[2]')
 expect(page.locator('#yp-contact-timer')).to_have_text('0.00 s');expect(page.locator('#yp-command')).to_have_value('Start')
 page.locator('#ys-input-toggle').click();expect(page.locator('#yp-hold')).to_be_visible()
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')


def test_pause_clears_usable_permission_display(page,demo_records,live_server):
 basic_lab(page,demo_records,live_server);page.locator('#yp-practice').check();contact(page,300)
 expect(page.locator('#ys-permission-countdown')).to_contain_text('voice permission remaining')
 page.evaluate('YanksonLab.pause()')
 expect(page.locator('#ys-permission-countdown')).to_have_text('No current voice permission')
 expect(page.locator('#yp-listen-help')).to_contain_text('Unavailable')
 page.locator('#yp-listen').click();expect(page.locator('#yp-reason')).to_contain_text('No current voice permission')
 assert not page.evaluate('YanksonLab.row[3]')
