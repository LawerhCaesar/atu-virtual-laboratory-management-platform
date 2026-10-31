from pathlib import Path
import pytest
from playwright.sync_api import expect
from tests.e2e.test_ect_ui import open_lab
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_ect_explorer_help_and_pdf(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce');open_lab(page,demo_records,live_server)
 Path('test-results/ect-learning').mkdir(parents=True,exist_ok=True)
 page.locator('#ect-bonnet-toggle').click();page.locator('#ect-engine-explorer').screenshot(path=f'test-results/ect-learning/bay-stage-{width}.png');expect(page.locator('#ect-bonnet-toggle')).to_have_text('Close bonnet')
 page.locator('#ect-focus-toggle').click();expect(page.locator('#ect-focus-toggle')).to_have_attribute('aria-pressed','true')
 page.locator('#timeline').fill('2300');expect(page.locator('#ect-visual-sensor')).to_have_text('70.59 °C');expect(page.locator('#ect-gap-reading')).to_contain_text('29.41')
 Path('test-results/ect-learning').mkdir(parents=True,exist_ok=True);page.screenshot(path=f'test-results/ect-learning/focus-{width}.png',full_page=True);page.locator('#ect-engine-explorer').screenshot(path=f'test-results/ect-learning/focus-stage-{width}.png')
 page.locator('#ect-settings summary').click();page.get_by_role('button',name='Explain When the temperature changes',exact=True).click();expect(page.get_by_role('tooltip').filter(has_text='waiting time')).to_be_visible()
 page.keyboard.press('Escape');page.locator('#ect-settings summary').click()
 page.locator('#ect-learning-guide summary').click();expect(page.locator('#ect-learning-content')).to_contain_text('Your first experiment')
 link=page.get_by_role('link',name='Download complete learning guide (PDF)');with_response=page.request.get(live_server.url+link.get_attribute('href'));assert with_response.ok and with_response.body().startswith(b'%PDF')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js');violations=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not violations,violations
