from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_fuel_delivery_ui import open_fuel
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_fuel_revision_guidance_and_3d(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce')
 errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
 open_fuel(page,demo_records,live_server)
 expect(page.locator('#fuel-3d-canvas canvas')).to_be_visible(timeout=20000)
 page.get_by_role('button',name='Injector cutaway',exact=True).click()
 expect(page.locator('#fuel-3d-title')).to_contain_text('INJECTOR CUTAWAY')
 page.locator('#fuel-3d-stage').evaluate("e=>e.scrollIntoView({block:'center'})")
 out=Path('test-results/fuel-review');out.mkdir(parents=True,exist_ok=True)
 page.screenshot(path=str(out/f'injector-{width}.png'))
 page.get_by_role('button',name='Vehicle context',exact=True).click()
 page.screenshot(path=str(out/f'vehicle-{width}.png'))
 page.get_by_role('button',name='Injector',exact=True).click()
 page.screenshot(path=str(out/f'injector-focus-{width}.png'))
 page.locator('#fuel-learning-guide summary').click()
 expect(page.locator('#fuel-learning-content')).to_contain_text('ten calculations cover one virtual second')
 expect(page.locator('#fuel-learning-content dt')).to_have_count(44)
 with page.expect_download() as download:page.get_by_role('link',name='Download complete learning guide (PDF)').click()
 assert Path(download.value.path()).read_bytes().startswith(b'%PDF')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors
