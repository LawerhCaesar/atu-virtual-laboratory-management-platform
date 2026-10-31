from pathlib import Path
import json
import pytest
from playwright.sync_api import expect
from test_battery_energy_ui import open_lab,load,test_battery_full_reference_exports_and_cursor as reference_run
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]

def no_webgl(page):
 page.add_init_script("(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,...a){return t==='webgl'||t==='webgl2'?null:original.call(this,t,...a);};})();")

@pytest.mark.parametrize('width',[1440,390])
def test_battery_charge_visual_and_help(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce')
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)));open_lab(page,demo_records,live_server)
 expect(page.locator('#battery-title')).to_have_text('BEV Charge and Discharge System')
 expect(page.locator('#battery-real-stage canvas')).to_be_visible(timeout=20000)
 page.get_by_role('button',name='Traction pack',exact=True).click()
 page.locator('#battery-real-stage').evaluate("e=>e.scrollIntoView({block:'center'})")
 out=Path('test-results/battery-charge');out.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(out/f'pack-{width}.png'))
 page.get_by_role('button',name='Vehicle context',exact=True).click();page.screenshot(path=str(out/f'vehicle-{width}.png'))
 page.get_by_role('button',name='Explain Profile change time (s)',exact=True).click()
 expect(page.locator('.battery-tip').filter(has_text='WHEN the profile changes current')).to_be_visible();page.keyboard.press('Escape')
 page.locator('#battery-learning summary').click()
 expect(page.locator('#battery-learning-content')).to_contain_text('The model always calculates once per virtual second')
 with page.expect_download() as dl:page.get_by_role('link',name='Download complete learning guide (PDF)').click()
 assert Path(dl.value.path()).read_bytes().startswith(b'%PDF')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js')
 violations=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
 assert not violations,[(v['id'],[n['html'] for n in v['nodes'][:2]]) for v in violations]
 assert not errors

def test_charge_choices_limits_and_history(page,demo_records,live_server):
 open_lab(page,demo_records,live_server)
 page.locator('#battery-charge-rate').select_option('fast')
 expect(page.locator('#battery-mode')).to_have_value('charge')
 expect(page.locator('#battery-input-controls-magnitudeA')).to_have_value('201.6')
 expect(page.locator('#battery-status')).to_contain_text('pending live input')
 page.locator('#battery-step').click()
 expect(page.locator('#battery-gauge-charge-value')).to_contain_text('201.60 A')
 expect(page.locator('#battery-gauge-supply-value')).to_contain_text('0.00 A')
 page.locator('#battery-cursor').fill('0')
 expect(page.locator('#battery-real-stage')).to_have_attribute('data-current','-50.4')
 page.locator('#battery-charge-rate').select_option('normal');page.locator('#battery-step').click()
 expect(page.locator('#battery-gauge-charge-value')).to_contain_text('50.40 A')
 load(page,'cold');page.locator('#battery-charge-rate').select_option('fast');page.locator('#battery-step').click()
 expect(page.locator('#battery-gauge-charge-value')).to_contain_text('0.00 A')
 expect(page.locator('#battery-station-state')).to_contain_text('blocked')
 load(page,'derating');page.locator('#battery-charge-rate').select_option('fast');page.locator('#battery-step').click()
 actual=float(page.locator('#battery-real-stage').get_attribute('data-current'));assert 0 < abs(actual) < 201.6
 load(page,'taper');page.locator('#battery-charge-rate').select_option('fast');page.locator('#battery-step').click()
 actual=float(page.locator('#battery-real-stage').get_attribute('data-current'));assert 0 < abs(actual) < 201.6

def test_charge_capacity_scaling_and_export(page,demo_records,live_server):
 open_lab(page,demo_records,live_server)
 page.locator('#battery-advanced summary').click();page.locator('#battery-input-parameters-np').fill('12')
 page.locator('#battery-charge-rate').select_option('fast')
 expect(page.locator('#battery-input-controls-magnitudeA')).to_have_value('100.8')
 page.locator('#battery-step').click()
 with page.expect_download() as dl:page.locator('#battery-json').click()
 meta=json.loads(Path(dl.value.path()).read_text())
 assert meta['initialConfiguration']['parameters']['np']==12
 assert meta['appliedInputEvents'][-1]['requestedCurrentA']==-100.8
 assert meta['appliedInputEvents'][-1]['appliedTimeS']==1
 page.locator('#battery-charge-rate').select_option('custom');page.locator('#battery-step').click()
 expect(page.locator('#battery-charge-rate')).to_have_value('custom')

def test_battery_reference_and_fallback(page,demo_records,live_server):
 no_webgl(page);reference_run(page,demo_records,live_server)
 expect(page.locator('#battery-scene')).to_be_visible()
 expect(page.locator('#battery-3d-notice')).to_contain_text('3D is unavailable')
