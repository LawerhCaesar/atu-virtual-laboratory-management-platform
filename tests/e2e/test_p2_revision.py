import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_p2_hybrid_ui import open_p2,run
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_p2_new_inputs_3d_feedback_fuel_and_guide(page,demo_records,live_server,width):
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce');open_p2(page,demo_records,live_server)
 assert page.locator('.p2-toolbar[aria-label="Simulation controls"] [data-preset]').count()==0
 expect(page.locator('#p2-main-fields .p2-field')).to_have_count(7);expect(page.locator('#p2-advanced-fields .p2-field')).to_have_count(19);expect(page.locator('#p2-drivetrain canvas')).to_be_visible(timeout=30000);expect(page.locator('#p2-drivetrain')).to_have_attribute('data-photos-loaded','2',timeout=30000)
 page.locator('#p2-fuel-setup').evaluate('e=>e.open=true');page.locator('#p2-fuel-estimate-enabled').check();page.locator('#p2-input-initial_fuel_litres').fill('0.01');page.locator('#p2-input-fuel_price_per_l').fill('10');run(page)
 expect(page.locator('#p2-drivetrain')).to_have_attribute('data-clutch','closed');expect(page.locator('[data-p2-feed=feedback]')).to_contain_text('returns to the next allocation step');expect(page.locator('#p2-torque-monitor')).to_contain_text('Diagnostic only');expect(page.locator('#p2-fuel-reading')).to_contain_text('STUDY ESTIMATE')
 data=page.evaluate('P2Lab.result');assert data['summary']['battery_energy_used_wh']==pytest.approx(178.899286,abs=.001);f=data['fuel_inventory']['summary'];assert f['estimated_fuel_used_litres']==pytest.approx(.0575925743);assert f['fuel_budget_deficit_litres']>0
 with page.expect_download() as dl:page.locator('#p2-fuel-csv').click()
 text=Path(dl.value.path()).read_text();assert text.startswith('# fuel_assumptions,');assert 'estimated_fuel_used_litres' in text
 for camera in ['clutch','electric','drive']:
  page.locator('[data-p2-camera='+camera+']').click();expect(page.locator('#p2-drivetrain')).to_have_attribute('data-camera',camera)
 page.get_by_role('button',name='Explain Integration time step',exact=True).click();expect(page.get_by_role('tooltip').filter(has_text='100 updates')).to_be_visible();page.get_by_role('button',name='Explain Integration time step',exact=True).click();expect(page.get_by_role('tooltip').filter(has_text='100 updates')).to_be_hidden()
 page.locator('#p2-save').click();page.locator('#p2-reset').click();expect(page.locator('#p2-fuel-estimate-enabled')).not_to_be_checked();page.locator('#p2-load').click();expect(page.locator('#p2-fuel-estimate-enabled')).to_be_checked();expect(page.locator('#p2-input-initial_fuel_litres')).to_have_value('0.01')
 page.get_by_text('Learning guide and reference evidence',exact=True).click();expect(page.locator('#p2-learning-content')).to_contain_text('100 updates each simulated second');link=page.get_by_role('link',name='Download complete learning guide (PDF)',exact=True);response=page.request.get(live_server.url+link.get_attribute('href'));assert response.status==200;assert response.body().startswith(b'%PDF')
 page.locator('#p2-reset').click();page.get_by_role('button',name='Low · 60 Nm',exact=True).click();run(page);expect(page.locator('#p2-drivetrain')).to_have_attribute('data-clutch','open');expect(page.locator('#p2-fuel-reading')).to_contain_text('not estimated')
 page.emulate_media(reduced_motion='no-preference');page.locator('#p2-scrub').fill('10');r=page.evaluate('P2Lab.result');shaft=float(page.locator('#p2-drivetrain').get_attribute('data-shaft-angle'));wheel=float(page.locator('#p2-drivetrain').get_attribute('data-wheel-angle'));assert shaft==pytest.approx(10*r['summary']['motor_speed_rad_s']);assert wheel==pytest.approx(shaft/(r['parameters']['gear_ratio']*r['parameters']['final_drive_ratio']))
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');dest=Path('test-results/p2-revision');dest.mkdir(parents=True,exist_ok=True);page.locator('.p2-visual').screenshot(path=str(dest/f'bench-feedback-{width}.png'))
 page.add_script_tag(path='node_modules/axe-core/axe.min.js');issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not issues,issues;assert not errors,errors

def test_p2_invalid_inventory_and_webgl_fallback(page,demo_records,live_server):
 page.add_init_script("const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return /webgl/.test(kind)?null:original.call(this,kind,...args)}")
 open_p2(page,demo_records,live_server);expect(page.locator('#p2-drivetrain')).to_contain_text('3D is unavailable',timeout=30000);page.locator('#p2-input-initial_fuel_litres').fill('56');expect(page.locator('#p2-run')).to_be_disabled();expect(page.locator('#p2-input-initial_fuel_litres-error')).to_contain_text('Must not exceed')
 page.locator('#p2-reset').click();run(page);expect(page.locator('#p2-operating')).to_contain_text('Blended');expect(page.locator('[data-p2-feed=plant]')).to_contain_text('70.00 Nm')
