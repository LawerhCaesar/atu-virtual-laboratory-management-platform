from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_edward_ui import open_lab
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_motor_workspace_help_and_guidance(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce')
 errors=[];page.on('pageerror',lambda error:errors.append(str(error)));open_lab(page,demo_records,live_server)
 expect(page.locator('.drive-3d-stage canvas')).to_be_visible(timeout=20000)
 expect(page.locator('.common-inputs [data-field]')).to_have_count(8)
 b=page.get_by_role('button',name='Explain Load change time (s)',exact=True);b.click()
 expect(page.locator('.motor-tip').filter(has_text='moment when the shaft load changes')).to_be_visible();page.keyboard.press('Escape')
 page.locator('[data-time]').fill('4');expect(page.locator('.drive-readings')).to_contain_text('Selected 4.000 s')
 expect(page.locator('.drive-3d-stage')).to_have_attribute('data-shaft-angle','0')
 page.get_by_role('button',name='Motor close-up',exact=True).click()
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if width==1440:
  a=page.locator('.input-workspace').bounding_box();b=page.locator('.output-workspace').bounding_box();assert b['x']>=a['x']+a['width']
 page.locator('.drive-3d-stage').evaluate("e=>e.scrollIntoView({block:'center'})")
 out=Path('test-results/motor-review');out.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(out/f'motor-{width}.png'))
 page.locator('#motor-learning-guide summary').click()
 expect(page.locator('#motor-learning-content')).to_contain_text('50,000 steps cover one virtual second')
 with page.expect_download() as dl:page.get_by_role('link',name='Download complete learning guide (PDF)').click()
 assert Path(dl.value.path()).read_bytes().startswith(b'%PDF')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js')
 issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
 assert not issues,[(x['id'],[n['html'] for n in x['nodes'][:2]]) for x in issues]
 assert not errors

def test_motor_animation_follows_selected_sample(page,demo_records,live_server):
 open_lab(page,demo_records,live_server)
 page.locator('[data-time]').fill('1.5');expect(page.locator('.drive-readings')).to_contain_text('Selected 1.500 s')
 first=float(page.locator('.drive-3d-stage').get_attribute('data-shaft-angle'));assert first>0
 page.locator('[data-time]').fill('3');expect(page.locator('.drive-readings')).to_contain_text('Selected 3.000 s')
 assert float(page.locator('.drive-3d-stage').get_attribute('data-shaft-angle'))>first
 page.locator('.chart-grid .legend button').first.click();expect(page.locator('.chart-grid .motor-tip').first).to_be_visible()

def test_motor_fallback(page,demo_records,live_server):
 page.add_init_script("(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,...a){return t==='webgl'||t==='webgl2'?null:original.call(this,t,...a);};})();")
 open_lab(page,demo_records,live_server)
 expect(page.locator('.drive-3d-stage')).to_contain_text('3D is unavailable')
 expect(page.locator('[data-rotor]')).to_be_visible()
 page.locator('[data-time]').fill('4');expect(page.locator('[data-value=speed]')).to_have_text('1,500.0')
