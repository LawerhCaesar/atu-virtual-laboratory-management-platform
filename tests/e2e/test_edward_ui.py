import csv
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]

def open_lab(page,demo_records,live_server):
 page.goto(live_server.url+'/accounts/login/')
 page.get_by_label('Email address',exact=True).fill(demo_records['student'].email)
 page.get_by_label('Password',exact=True).fill('DemoPass!742')
 page.get_by_role('button',name='Sign in',exact=True).click()
 page.goto(live_server.url+'/virtual-lab/bev/electric-motor-drive/')
 page.locator('#tour-close').click()
 expect(page.locator('.status')).to_contain_text('Ready',timeout=60000)
 page.locator('.export-options').evaluate('e=>e.open=true')

def test_edward_scenarios_exports_validation(page,demo_records,live_server):
 open_lab(page,demo_records,live_server)
 page.locator('[data-time]').fill('5')
 expect(page.locator('[data-value=speed]')).to_have_text('1,500.0')
 with page.expect_download() as dl:page.locator('[data-export]').click()
 rows=list(csv.reader(Path(dl.value.path()).read_text().splitlines()));assert len(rows)==5002 and len(rows[0])==51
 page.locator('[data-preset]').select_option('pwm');expect(page.locator('.status')).to_contain_text('Ready',timeout=60000)
 page.locator('[data-tab=waves]').click()
 expect(page.locator('[data-mode-note]')).to_contain_text('Switched mode')
 with page.expect_download() as dl:page.locator('[data-fine]').click()
 assert len(Path(dl.value.path()).read_text().splitlines())==10002
 page.locator('[data-tab=converters]').click()
 for lab in ['buck','boost','rectifier']:
  page.locator('[data-lab]').select_option(lab)
  expect(page.locator('.chart-grid')).to_contain_text('Converter currents')
 page.locator('.settings summary').click();page.locator('[data-field=Cdc]').fill('-1');page.locator('[data-run]').click()
 expect(page.locator('.error')).to_be_visible();expect(page.locator('.status')).to_contain_text('retained')

@pytest.mark.parametrize('width',[1440,390])
def test_edward_visual_and_access(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce');open_lab(page,demo_records,live_server)
 page.locator('[data-time]').fill('4');Path('test-results/edward').mkdir(parents=True,exist_ok=True)
 page.screenshot(path=f'test-results/edward/baseline-{width}.png',full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js')
 issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
 assert not issues,issues
