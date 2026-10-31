from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_engine_demo import open_engine,start_engine
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_workspace_sections_help_and_layout(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce')
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 open_engine(page,demo_records,live_server)
 expect(page.locator('#engine-tabs button')).to_have_count(4)
 expect(page.locator('#engine-cutaway')).to_have_count(0)
 for name,meaning in [('Fuel and injection','Fuel delivery'),('Idle and ignition','Idle target'),('Cooling','Cooling demand'),('Start and run','Start/run permission')]:
  page.get_by_role('button',name=name,exact=True).click()
  expect(page.locator('#engine-schematic svg')).to_have_attribute('aria-label',__import__('re').compile(meaning))
  expect(page.locator('#engine-chart')).to_be_visible()
 page.get_by_role('button',name='Fuel and injection',exact=True).click()
 button=page.locator('#engine-chart-legend button').first;button.click()
 expect(page.locator('#engine-chart-legend .engine-info-popup').first).to_be_visible()
 page.keyboard.press('Escape')
 page.locator('#engine-learning-guide summary').click()
 expect(page.locator('#engine-learning-content')).to_contain_text('0.05 seconds')
 with page.expect_download() as download:page.get_by_role('link',name='Download complete learning guide (PDF)').click()
 assert Path(download.value.path()).read_bytes().startswith(b'%PDF')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if width==1440:
  left=page.locator('.engine-input-panel').bounding_box();right=page.locator('.engine-results').bounding_box()
  assert right['x']>left['x']+left['width']
  a=page.locator('.engine-process-panel').bounding_box();b=page.locator('.engine-graph-panel').bounding_box();assert b['x']>a['x']+a['width']
 page.add_script_tag(path='node_modules/axe-core/axe.min.js')
 findings=page.evaluate("async()=> (await axe.run('#engine-demo',{runOnly:{type:'tag',values:['wcag2a','wcag2aa']}})).violations")
 assert not findings,[(x['id'],x['nodes'][0]['html']) for x in findings]
 page.locator('#engine-learning-guide summary').click()
 page.locator('#engine-system').evaluate("el=>el.scrollIntoView({block:'start'})")
 out=Path('test-results/engine-workspace');out.mkdir(parents=True,exist_ok=True)
 page.screenshot(path=str(out/f'workspace-{width}.png'),full_page=False)
 assert not errors

def test_process_follows_history_and_latest(page,demo_records,live_server):
 page.emulate_media(reduced_motion='reduce');open_engine(page,demo_records,live_server);page.clock.install()
 start_engine(page);page.get_by_role('button',name='Pause',exact=True).click()
 expect(page.locator('#process-value-2')).to_have_text('1.68 ms')
 page.get_by_label('Oxygen-sensor voltage (V)',exact=True).fill('0.10');page.get_by_role('button',name='Step 0.05 s',exact=True).click()
 expect(page.locator('#process-value-2')).to_have_text('1.93 ms')
 page.get_by_label('Inspect recorded sample').fill('0')
 expect(page.locator('#process-sample-time')).to_contain_text('Recorded sample: 0.00 s')
 page.get_by_role('button',name='Return to latest sample').click()
 expect(page.locator('#process-value-2')).to_have_text('1.93 ms')
 expect(page.locator('#process-sample-time')).to_have_text('Latest accepted model sample')

 page.set_viewport_size({'width':1440,'height':1050})
 page.locator('#engine-system').evaluate("el=>el.scrollIntoView({block:'start'})")
 page.screenshot(path='test-results/engine-workspace/warm-run-workspace.png',full_page=False)
