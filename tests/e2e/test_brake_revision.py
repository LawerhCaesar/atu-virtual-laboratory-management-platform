import json,re
from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_brakelab_ui import open_brake,output
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_hub_help_calibration_pdf_and_reset(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce');errors=[];page.on('pageerror',lambda e:errors.append(str(e)));open_brake(page,demo_records,live_server);page.locator('#tour-close').click()
 expect(page.locator('#brake-hub-stage canvas')).to_be_visible(timeout=20000);expect(page.locator('#brake-learning-content')).to_contain_text('Time, step time and playback')
 page.get_by_text('Advanced calibration',exact=True).click();page.locator('#brake-cal-gearRatio').fill('1');expect(output(page,'regenerativeForceN')).to_have_text('534.2');expect(page.locator('#brake-hub-stage')).to_have_attribute('data-gear-ratio','1')
 with page.expect_download() as dl:page.locator('#brake-export').click()
 data=json.loads(Path(dl.value.path()).read_text());assert data['calibration']['gearRatio']==1;assert data['result']['frictionForceN']==pytest.approx(1565.8064516)
 page.get_by_role('button',name='Explain Hub gear ratio',exact=True).click();tip=page.get_by_role('tooltip').filter(has_text='nine motor revolutions');expect(tip).to_be_visible();page.get_by_role('button',name='Explain Hub gear ratio',exact=True).click();expect(tip).to_be_hidden()
 page.locator('#brake-cal-regenEfficiency').fill('1.2');expect(page.locator('#brake-run')).to_be_disabled();expect(page.locator('#brake-export')).to_be_disabled();page.locator('#brake-calibration-reset').click();expect(output(page,'regenerativeForceN')).to_have_text('2100.0');expect(page.locator('#brake-cal-gearRatio')).to_have_value('9')
 page.locator('#brake-cal-socStopPct').fill('98');page.locator('#brake-input-batterySocPct').fill('95');assert float(output(page,'regenerativeForceN').inner_text())>0
 page.locator('#brake-calibration-reset').click();expect(output(page,'regenerativeForceN')).to_have_text('0.0');expect(output(page,'frictionForceN')).to_have_text('2100.0')
 page.locator('#brake-reset').click();page.get_by_role('button',name='Explain Regenerative force',exact=True).click();expect(page.get_by_role('tooltip').filter(has_text='wheel-driven generator path')).to_be_visible();page.get_by_role('button',name='Explain Regenerative force',exact=True).click();dest=Path('test-results/brake-revision');dest.mkdir(parents=True,exist_ok=True);page.locator('.brake-visual').screenshot(path=str(dest/f'hub-{width}.png'));page.get_by_role('button',name='Generator cutaway',exact=True).click();page.locator('#brake-hub-stage').screenshot(path=str(dest/f'generator-{width}.png'));page.get_by_role('button',name='Brake-disc close-up',exact=True).click();page.locator('#brake-hub-stage').screenshot(path=str(dest/f'disc-{width}.png'))
 page.get_by_text('Learning guide and reference evidence',exact=True).click();link=page.get_by_role('link',name='Download complete learning guide (PDF)');assert page.request.get(live_server.url+link.get_attribute('href')).body().startswith(b'%PDF')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.add_script_tag(path='node_modules/axe-core/axe.min.js');violations=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not violations,violations;assert not errors,errors

def test_hub_backdrive_angle_friction_and_fallback(page,demo_records,live_server):
 open_brake(page,demo_records,live_server);page.locator('#tour-close').click();expect(page.locator('#brake-hub-stage canvas')).to_be_visible(timeout=20000);page.clock.install();page.locator('#brake-run').click();page.clock.run_for(1000);stage=page.locator('#brake-hub-stage');wheel,motor=stage.evaluate('e=>[Number(e.dataset.wheelAngle),Number(e.dataset.motorAngle)]');assert wheel>0;assert motor==pytest.approx(wheel*9)
 page.locator('#brake-pause').click();before=stage.get_attribute('data-wheel-angle');page.clock.run_for(200);expect(stage).to_have_attribute('data-wheel-angle',before)
 page.locator('#brake-input-batterySocPct').fill('95');expect(stage).to_have_attribute('data-regen','0');assert float(stage.get_attribute('data-friction'))>0
