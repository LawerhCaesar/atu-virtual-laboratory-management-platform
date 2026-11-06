from pathlib import Path
import pytest
from playwright.sync_api import expect
from tests.e2e.test_ect_ui import open_lab
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_photographic_car_open_focus_and_model_readings(page,demo_records,live_server,width):
 errors=[];page.on('pageerror',lambda error:errors.append(str(error)));page.set_viewport_size({'width':width,'height':1000});open_lab(page,demo_records,live_server)
 for img in page.locator('[data-ect-photo]').all():expect(img).to_have_js_property('complete',True);assert img.evaluate('e=>e.naturalWidth')>1000
 stage=page.locator('#ect-engine-explorer');dest=Path('test-results/ect-frontal');dest.mkdir(parents=True,exist_ok=True)
 stage.screenshot(path=str(dest/f'closed-{width}.png'));page.locator('#ect-bonnet-toggle').click();expect(page.locator('#ect-bonnet-toggle')).to_have_text('Close bonnet');stage.screenshot(path=str(dest/f'open-{width}.png'))
 page.locator('#timeline').fill('2300');expect(page.locator('#ect-photo-temperature')).to_have_text('ECT · 70.6 °C');expect(page.locator('#ect-visual-sensor')).to_have_text('70.59 °C')
 page.locator('#ect-focus-toggle').click();expect(page.locator('.ect-scene-scroll')).to_be_visible();stage.screenshot(path=str(dest/f'cooling-{width}.png'))
 page.locator('#ect-full-view').click();expect(page.locator('.ect-scene-scroll')).to_be_hidden();page.locator('#ect-bonnet-toggle').click();expect(page.locator('#ect-bonnet-toggle')).to_have_text('Open bonnet');assert not errors,errors
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js');issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not issues,issues
