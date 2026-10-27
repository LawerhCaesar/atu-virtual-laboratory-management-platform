import json
from pathlib import Path
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

def open_module(page, demo_records, live_server):
    page.goto(live_server.url + '/accounts/login/')
    page.get_by_label('Email address', exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password', exact=True).fill('DemoPass!742')
    page.get_by_role('button', name='Sign in', exact=True).click()
    page.get_by_role('link', name='Virtual laboratory', exact=True).click()
    page.get_by_role('link', name='Enter HEV environment', exact=True).click()
    page.get_by_role('link', name='Open 12 V Micro-Hybrid Stop-Start', exact=True).click()
    expect(page.locator('#micro-status')).to_have_text('Automatic stop permitted')

def test_default_inhibits_export_and_reset(page, demo_records, live_server):
    open_module(page,demo_records,live_server)
    expect(page.locator('[data-micro-output="fuelSavedG"]')).to_have_text('1.46')
    expect(page.locator('[data-micro-output="breakEvenStopTimeS"]')).to_have_text('5.82')
    page.get_by_role('button',name='Save scenario for comparison').click()
    page.get_by_label('Stop duration (s)',exact=True).fill('3')
    expect(page.locator('#micro-reason')).to_contain_text('Code 4')
    expect(page.locator('[data-micro-output="fuelSavedG"]')).to_have_text('0.00')
    page.get_by_role('button',name='Play',exact=True).click()
    page.wait_for_timeout(4800)
    expect(page.locator('#micro-engine')).to_have_text('Engine ON')
    page.get_by_role('button',name='Pause',exact=True).click()
    page.get_by_role('button',name='Save scenario for comparison').click()
    expect(page.locator('#micro-comparison')).to_contain_text('4')
    with page.expect_download() as dl: page.get_by_role('button',name='Export JSON').click()
    payload=json.loads(Path(dl.value.path()).read_text()); assert payload['outputs']['inhibitCode']==4
    page.get_by_role('button',name='Reset to approved defaults').click()
    expect(page.locator('#micro-reason')).to_contain_text('Code 0')
    page.get_by_label('Number of stops (count)',exact=True).fill('1.5')
    expect(page.locator('#micro-error')).to_contain_text('integer')
    expect(page.get_by_role('button',name='Export JSON')).to_be_disabled()

@pytest.mark.parametrize('width',[1280,390])
def test_responsive_and_accessible(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':900}); page.emulate_media(reduced_motion='reduce')
    open_module(page,demo_records,live_server)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    report=page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
    assert not report['violations'], json.dumps(report['violations'],indent=2)
    dest=Path('test-results/micro-hybrid');dest.mkdir(parents=True,exist_ok=True)
    page.locator('#micro-animation-title').scroll_into_view_if_needed();page.wait_for_timeout(500);page.screenshot(path=str(dest/f'default-{width}.png'))
    page.locator('.micro-scene').screenshot(path=str(dest/f'scene-{width}.png'))
    page.get_by_label('Accessory load (W)',exact=True).fill('1000')
    expect(page.locator('#micro-reason')).to_contain_text('Code 7')
    page.locator('#micro-decision').scroll_into_view_if_needed();page.screenshot(path=str(dest/f'inhibited-{width}.png'))
