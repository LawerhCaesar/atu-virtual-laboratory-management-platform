import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
DEST=Path('test-results/engine-generator')

def open_lab(page,demo_records,live_server):
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.goto(live_server.url+'/virtual-lab/hev/engine-generator/')
    expect(page.locator('#tour-title')).to_contain_text('Engine–Generator')
    page.get_by_role('button',name='Close module guide',exact=True).click()

def run(page):
    page.locator('#eg-run').click();expect(page.locator('#eg-status')).to_contain_text('Complete',timeout=30000)

def test_engine_generator_reference_exports_maps_and_validation(page,demo_records,live_server):
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)));open_lab(page,demo_records,live_server);run(page)
    expect(page.locator('#eg-status')).to_contain_text('1201 samples')
    expect(page.locator('#eg-summary')).to_contain_text('0.589619')
    with page.expect_download() as dl:page.locator('#eg-json').click()
    r=json.loads(Path(dl.value.path()).read_text());assert len(r['samples'])==1201
    assert r['summary']['totalFuelG']==pytest.approx(157.5984286)
    with page.expect_download() as dl:page.locator('#eg-csv').click()
    assert Path(dl.value.path()).read_text().startswith('# metadata,')
    with page.expect_download() as dl:page.locator('#eg-save').click()
    scenario=Path(dl.value.path()).read_bytes()
    page.locator('#eg-meanLoadKW').fill('25');expect(page.locator('#eg-status')).to_contain_text('new run')
    page.locator('#eg-import').set_input_files({'name':'scenario.json','mimeType':'application/json','buffer':scenario})
    expect(page.locator('#eg-meanLoadKW')).to_have_value('18')
    page.locator('#eg-cursor').fill('0');assert 'P_gen_kW' in page.locator('#eg-payload').input_value()
    page.locator('#eg-meanLoadKW').fill('');expect(page.locator('#eg-error')).to_be_visible();expect(page.locator('#eg-run')).to_be_disabled()
    page.locator('#eg-meanLoadKW').fill('18');expect(page.locator('#eg-run')).to_be_enabled()
    page.locator('#eg-maps summary').click();m=r['maps'];m['generatorEfficiency'][0]=2
    page.locator('#eg-map-json').fill(json.dumps(m));page.locator('#eg-apply-maps').click()
    expect(page.locator('#eg-error')).to_contain_text('between 0 and 1')
    page.locator('#eg-reset-maps').click();expect(page.locator('#eg-error')).to_be_hidden()
    run(page);page.locator('#eg-zoom').select_option('10')
    with page.expect_download() as dl:page.get_by_role('button',name='Export Power SVG',exact=True).click()
    svg=Path(dl.value.path()).read_text();assert 'modelVersion' in svg and '<path' in svg
    assert not errors

def test_engine_generator_live_pause_and_hidden(page,demo_records,live_server):
    open_lab(page,demo_records,live_server);page.clock.install();page.locator('#eg-live').click();page.clock.run_for(2200)
    page.locator('#eg-pause').click();status=page.locator('#eg-status').inner_text();page.clock.run_for(2000);assert page.locator('#eg-status').inner_text()==status
    page.locator('#eg-live').click();page.evaluate("Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
    expect(page.locator('#eg-status')).to_contain_text('tab was hidden')
    page.locator('#eg-reset').click();expect(page.locator('#eg-status')).to_contain_text('0 / 120 s · 1 samples')

@pytest.mark.parametrize('width',[1440,390])
def test_engine_generator_visual_and_accessibility(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':1050});open_lab(page,demo_records,live_server);run(page);DEST.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(DEST/f'baseline-{width}.png'),full_page=True)
    page.locator('#eg-preset').select_option('limited');page.locator('#eg-load-preset').click();run(page)
    expect(page.locator('#eg-limits')).to_contain_text('30 kW')
    page.locator('#eg-stage').screenshot(path=str(DEST/f'limited-{width}.png'))
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.emulate_media(reduced_motion='reduce');page.locator('#eg-defaults').click();page.locator('#eg-live').click()
    assert page.locator('#eg-fuel-motion').evaluate('e=>getComputedStyle(e).animationName')=='none'
    page.locator('#eg-pause').click();page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    violations=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
    assert not violations,json.dumps(violations,indent=2)


def test_engine_generator_preview(browser,demo_records,live_server):
    DEST.mkdir(parents=True,exist_ok=True)
    context=browser.new_context(viewport={'width':1440,'height':1050},record_video_dir=str(DEST/'video'),record_video_size={'width':1440,'height':1050})
    page=context.new_page()
    try:
        open_lab(page,demo_records,live_server)
        page.locator('#eg-speed').select_option('10');page.locator('#eg-live').click()
        page.locator('#eg-stage').scroll_into_view_if_needed();page.wait_for_timeout(4000)
        page.locator('#eg-pause').click();page.locator('#eg-stage').screenshot(path=str(DEST/'flow-desktop.png'))
        page.locator('#eg-preset').select_option('limited');page.locator('#eg-load-preset').click()
        page.locator('#eg-live').click();page.locator('#eg-stage').scroll_into_view_if_needed();page.wait_for_timeout(3000)
        page.locator('#eg-pause').click();video=page.video
    finally:context.close()
    video.save_as(str(DEST/'engine-generator-preview.webm'))
