import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_engine_generator_ui import open_lab,run
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_photos_inventory_help_graphs_and_pdf(page,demo_records,live_server,width):
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_viewport_size({'width':width,'height':1000});open_lab(page,demo_records,live_server)
 photos=page.locator('#eg-component-photos img');expect(photos).to_have_count(4);assert photos.evaluate_all('nodes=>nodes.every(i=>i.complete&&i.naturalWidth>0)')
 for part in ['tank','engine','generator','dc-link','all']:
  page.locator('[data-component='+part+']').click();expect(page.locator('#eg-component-photos')).to_have_attribute('data-focus',part)
  expect(page.locator('#eg-component-photos figure:visible')).to_have_count(4 if part=='all' else 1)
 page.get_by_role('button',name='Explain Calculation interval',exact=True).click();expect(page.get_by_role('tooltip').filter(has_text='ten updates')).to_be_visible();page.get_by_role('button',name='Explain Calculation interval',exact=True).click();expect(page.get_by_role('tooltip').filter(has_text='ten updates')).to_be_hidden()
 page.locator('#eg-initialFuelLitres').fill('0.1');page.locator('#eg-fuelPricePerL').fill('10');run(page);expect(page.locator('#eg-fuel-budget')).to_contain_text('budget exceeded');expect(page.locator('#eg-plots > section')).to_have_count(6)
 data=page.evaluate('EngineGeneratorLab.result');assert data['summary']['fuelUsedLitres']==pytest.approx(data['summary']['totalFuelG']/740);assert data['summary']['fuelCost']==pytest.approx(data['summary']['fuelUsedLitres']*10);assert data['summary']['generatedEnergyKWh']==pytest.approx(.5896190336,rel=.001)
 expect(page.locator('#eg-interpretation')).to_contain_text('Whole-run conversion efficiency')
 expect(page.locator('#eg-interpretation')).to_contain_text('not a vehicle range prediction')
 page.get_by_text('Learning guide and reference evidence',exact=True).click();expect(page.locator('#eg-learning-content')).to_contain_text('Calculation interval means');link=page.get_by_role('link',name='Download complete learning guide (PDF)',exact=True);response=page.request.get(live_server.url+link.get_attribute('href'));assert response.status==200;assert response.body().startswith(b'%PDF')
 page.locator('#eg-defaults').click();page.emulate_media(reduced_motion='reduce');page.locator('#eg-live').click();assert page.locator('#eg-fuel-motion').evaluate('e=>getComputedStyle(e).animationName')=='none';page.locator('#eg-pause').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 dest=Path('test-results/engine-generator-revision');dest.mkdir(parents=True,exist_ok=True);page.locator('#eg-stage').screenshot(path=str(dest/f'components-{width}.png'));page.locator('#eg-plots').screenshot(path=str(dest/f'graphs-{width}.png'))
 page.add_script_tag(path='node_modules/axe-core/axe.min.js');issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations");assert not issues,issues;assert not errors,errors

def test_shared_printable_guide_contains_learning_content_without_controls(page,demo_records,live_server):
 page.context.add_init_script('window.print=()=>{window.guidePrinted=true;}')
 open_lab(page,demo_records,live_server);page.get_by_text('Learning guide and reference evidence',exact=True).click()
 with page.expect_popup() as opened:page.locator('#lab-guide-print').click()
 popup=opened.value;expect(popup.locator('body')).to_contain_text('Calculation interval means');expect(popup.locator('body')).to_contain_text('Input labels and available explanations');assert popup.locator('button,input,select,textarea,[role=tooltip]').count()==0;assert popup.evaluate('window.guidePrinted') is True
 popup.close()
