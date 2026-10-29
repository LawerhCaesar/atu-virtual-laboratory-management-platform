from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_series_parallel(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000})
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click()
 page.goto(live_server.url+'/virtual-lab/hev/series-parallel-hybrid/');page.locator('#tour-close').click()
 expect(page.locator('#sp-charts > section')).to_have_count(6)
 Path('test-results/series-parallel').mkdir(parents=True,exist_ok=True)
 for tick,name,mode in [('80','combined','COMBINED_DRIVE'),('190','regeneration','REGENERATIVE'),('240','charging','ENGINE_CHARGING')]:
  page.locator('#sp-cursor').fill(tick);expect(page.locator('#sp-mode')).to_contain_text(mode);page.screenshot(path=f'test-results/series-parallel/{name}-{width}.png',full_page=True)
 with page.expect_download() as dl:page.locator('#sp-csv').click()
 assert len(Path(dl.value.path()).read_text().splitlines())==302
 page.locator('#sp-play').click();page.wait_for_timeout(400);page.locator('#sp-stop').click()
 page.locator('#sp-reset').click();expect(page.locator('#sp-time')).to_have_text('0.0 / 30 s')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js')
 issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
 assert not issues,issues
