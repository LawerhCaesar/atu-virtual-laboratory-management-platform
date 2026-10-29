import csv,json
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
def open_lab(page,demo_records,live_server):
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click()
 page.goto(live_server.url+'/virtual-lab/ice/authenticated-engine-starting/');page.locator('#tour-close').click()

def test_start_routes_fault_pause_export(page,demo_records,live_server):
 open_lab(page,demo_records,live_server);page.clock.install()
 page.locator('#ys-long').click();page.clock.run_for(6000);page.locator('#ys-run').click()
 expect(page.locator('#ys-state')).to_contain_text('RUNNING');expect(page.locator('#ys-outputs')).to_contain_text('Starter OFF · Run supply ON')
 time=page.locator('#ys-time').inner_text();page.clock.run_for(2000);assert page.locator('#ys-time').inner_text()==time
 with page.expect_download() as dl:page.locator('#ys-json').click()
 r=json.loads(Path(dl.value.path()).read_text());assert len(r['columns'])==28 and len(r['rows'])==len(r['inputs'])
 page.locator('#ys-reset').click();page.locator('#ys-short').click();page.clock.run_for(500)
 expect(page.locator('#ys-auth')).to_contain_text('permission ·')
 page.locator('#ys-voice-stale').click();expect(page.locator('#ys-reject')).to_contain_text('stale')
 page.locator('#ys-voice-fresh').click();page.clock.run_for(5000);expect(page.locator('#ys-state')).to_contain_text('RUNNING')
 page.locator('#ys-stop').click();expect(page.locator('#ys-state')).to_contain_text('FAULT')
 page.locator('#ys-recover').click();expect(page.locator('#ys-state')).to_contain_text('LOCKED')
 page.locator('#ys-reset').click();page.locator('#ys-ignitionAllowed').uncheck();page.locator('#ys-long').click();page.clock.run_for(6500)
 expect(page.locator('#ys-state')).to_contain_text('FAULT');expect(page.locator('#ys-outputs')).to_contain_text('Starter OFF · Run supply OFF')

@pytest.mark.parametrize('width',[1440,390])
def test_yankson_accessibility(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});open_lab(page,demo_records,live_server)
 Path('test-results/yankson').mkdir(parents=True,exist_ok=True);page.screenshot(path=f'test-results/yankson/baseline-{width}.png',full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js');issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
 assert not issues,issues

def test_permission_expiry_and_can_fault_deadline(page,demo_records,live_server):
 open_lab(page,demo_records,live_server);page.clock.install();page.locator('#ys-short').click();page.clock.run_for(11000)
 expect(page.locator('#ys-auth')).to_have_text('No voice permission')
 page.locator('#ys-voice-fresh').click();expect(page.locator('#ys-reject')).to_contain_text('no current permission')
 page.locator('#ys-reset').click();page.locator('#ys-ignitionAllowed').uncheck();page.locator('#ys-long').click();page.clock.run_for(1800)
 expect(page.locator('#ys-state')).to_contain_text('CRANKING');page.locator('#ys-CANdrop').check();page.clock.run_for(4000)
 expect(page.locator('#ys-state')).to_contain_text('FAULT');expect(page.locator('#ys-outputs')).to_contain_text('CAN INVALID')
