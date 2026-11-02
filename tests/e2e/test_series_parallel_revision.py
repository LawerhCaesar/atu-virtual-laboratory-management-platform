import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
def open_lab(page,demo_records,live_server):
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click();page.goto(live_server.url+'/virtual-lab/hev/series-parallel-hybrid/');page.locator('#tour-close').click();expect(page.locator('#sp-status')).to_contain_text('Experiment ready',timeout=30000)
def run(page):
 page.locator('#sp-run').click();expect(page.locator('#sp-status')).to_contain_text('Experiment ready',timeout=30000)
@pytest.mark.parametrize('width',[1440,390])
def test_drivetrain_paths_inputs_help_analysis_and_exports(page,demo_records,live_server,width):
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce');open_lab(page,demo_records,live_server)
 expect(page.locator('[data-key]')).to_have_count(73);expect(page.locator('#sp-drivetrain canvas')).to_be_visible(timeout=20000)
 assert page.locator('#sp-summary,#sp-events,#sp-current,#sp-config').count()==0
 dest=Path('test-results/series-parallel-revision');dest.mkdir(parents=True,exist_ok=True)
 for tick,mode,clutch in [('50','Series drive','open'),('120','Parallel mechanical drive','locked'),('80','Combined drive','locked')]:
  page.locator('#sp-cursor').fill(tick);expect(page.locator('#sp-mode')).to_contain_text(mode);expect(page.locator('#sp-drivetrain')).to_have_attribute('data-clutch',clutch);page.locator('#sp-stage').screenshot(path=str(dest/f'{tick}-{width}.png'))
 page.emulate_media(reduced_motion='no-preference');page.locator('#sp-cursor').fill('100');frame=page.evaluate('SeriesParallelLab.frame');assert float(page.locator('#sp-drivetrain').get_attribute('data-wheel-angle'))==pytest.approx(frame['wheelAngleRad']);assert float(page.locator('#sp-drivetrain').get_attribute('data-shaft-angle'))==pytest.approx(frame['wheelAngleRad']*8)
 for view in ['clutch','electric','drive']:
  page.locator('[data-camera='+view+']').click();expect(page.locator('#sp-drivetrain')).to_have_attribute('data-camera',view)
 page.locator('#sp-charts').screenshot(path=str(dest/f'analysis-{width}.png'))
 page.locator('#sp-scenario').select_option('4');page.locator('#sp-input-initialSpeedKmh').fill('70');page.locator('#sp-input-manualStepEnabled').check();page.locator('#sp-input-manualPowerAfterKw').fill('65');page.locator('#sp-input-manualPowerStepTimeS').fill('10');page.locator('#sp-input-durationS').fill('20');page.locator('#sp-input-stepS').fill('0.05');run(page);expect(page.locator('#sp-cursor')).to_have_attribute('max','400')
 page.locator('#sp-cursor').fill('240');expect(page.locator('#sp-mode')).to_contain_text('Combined drive');expect(page.locator('#sp-operating-note')).to_contain_text('work together')
 page.get_by_role('button',name='Explain Demand step time',exact=True).click();expect(page.get_by_role('tooltip').filter(has_text='ten seconds')).to_be_visible();page.get_by_role('button',name='Explain Demand step time',exact=True).click();expect(page.get_by_role('tooltip').filter(has_text='ten seconds')).to_be_hidden()
 page.locator('#sp-input-fuelPricePerL').fill('10');run(page)
 with page.expect_download() as dl:page.locator('#sp-json').click()
 data=json.loads(Path(dl.value.path()).read_text());assert len(data['frames'])==401;assert data['frames'][-1]['fuelCost']==pytest.approx(data['summary']['fuelUsedLitres']*10);assert 'transitions' in data and 'analysis' in data
 page.locator('#sp-compare').click();expect(page.locator('#sp-comparison table')).to_be_visible(timeout=30000)
 page.get_by_text('Learning guide and reference evidence',exact=True).click();expect(page.locator('#sp-learning-content')).to_contain_text('Step time and calculation interval, simply')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js');violations=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not violations,violations;assert not errors,errors

def test_fuel_constraint_validation_and_master_reset(page,demo_records,live_server):
 open_lab(page,demo_records,live_server);page.locator('#sp-scenario').select_option('4');page.locator('#sp-input-initialSpeedKmh').fill('70');page.locator('#sp-input-initialFuelLitres').fill('0');page.locator('#sp-input-enforceFuelLimit').check();run(page);page.locator('#sp-cursor').fill('100');expect(page.locator('#sp-mode')).to_contain_text('Electric drive');expect(page.locator('#sp-operating-note')).to_contain_text('tank is empty')
 data=page.evaluate('SeriesParallelLab.run');assert data['summary']['fuelUsedLitres']==0;assert all(f['engineShaftPowerKw']==0 for f in data['frames'])
 page.locator('#sp-input-initialFuelLitres').fill('100');run_button=page.locator('#sp-run');run_button.click();expect(page.locator('#sp-error')).to_contain_text('must not exceed');expect(page.locator('#sp-json')).to_be_disabled()
 with page.expect_navigation(wait_until='domcontentloaded'):page.locator('#lab-master-reset').click()
 expect(page.locator('#sp-status')).to_contain_text('Experiment ready',timeout=30000);expect(page.locator('#sp-input-initialFuelLitres')).to_have_value('20');expect(page.locator('#sp-input-enforceFuelLimit')).not_to_be_checked()

def test_missing_guide_does_not_block_experiment(page,demo_records,live_server):
 page.route('**/series-parallel/learning-guide.json',lambda route:route.fulfill(status=503,body='Unavailable'))
 open_lab(page,demo_records,live_server)
 page.get_by_text('Learning guide and reference evidence',exact=True).click();expect(page.locator('#sp-learning-content')).to_contain_text('Guide temporarily unavailable')
 response=page.request.get(live_server.url+'/static/guides/series-parallel-learning-guide.pdf');assert response.status==200;assert response.body().startswith(b'%PDF')
