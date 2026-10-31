import csv
import io
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect

pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
DEST=Path('test-results/battery-energy')


def open_lab(page,demo_records,live_server):
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.goto(live_server.url+'/virtual-lab/bev/battery-energy-management/')
    expect(page.locator('#tour-title')).to_contain_text('Battery Energy Management')
    page.get_by_role('button',name='Close module guide',exact=True).click()
    expect(page.locator('#battery-decision')).not_to_be_empty()


def load(page,id):
    page.locator('#battery-preset').select_option(id)
    page.locator('#battery-load').click()


def test_battery_full_reference_exports_and_cursor(page,demo_records,live_server):
    page.emulate_media(reduced_motion='reduce')
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    open_lab(page,demo_records,live_server)
    page.clock.install()
    page.locator('#battery-speed').select_option('60')
    page.locator('#battery-run').click()
    page.clock.run_for(60100)
    expect(page.locator('#battery-status')).to_contain_text('3600 / 3600 s · 3601 recorded samples')
    expect(page.locator('#battery-soc-label')).to_have_text('25% state of charge')
    with page.expect_download() as dl:page.locator('#battery-csv').click()
    rows=list(csv.DictReader(io.StringIO(Path(dl.value.path()).read_text())))
    assert len(rows)==3601 and len(rows[0])==33
    assert float(rows[1800]['SOC_pct'])==pytest.approx(75)
    assert float(rows[1800]['Requested_A'])==100.8
    assert float(rows[-1]['Temperature_C'])==pytest.approx(31.45383495)
    assert float(rows[-1]['EnergyOut_kWh'])==pytest.approx(17.41533696)
    with page.expect_download() as dl:page.locator('#battery-json').click()
    meta=json.loads(Path(dl.value.path()).read_text())
    assert meta['complete'] and meta['stateAdvances']==3600
    assert meta['appliedInputEvents'][1]['appliedTimeS']==1800
    page.locator('#battery-cursor').fill('1800')
    expect(page.locator('#battery-soc-label')).to_have_text('75% state of charge')
    expect(page.locator('#battery-plots section')).to_have_count(8)
    expect(page.locator('#battery-raw tr')).to_have_count(32)
    page.locator('#battery-reset').click()
    expect(page.locator('#battery-status')).to_contain_text('0 / 3600 s · 1 recorded samples')
    expect(page.locator('#battery-soc-label')).to_have_text('50% state of charge')
    assert not errors


def test_battery_edits_pause_validation_and_lifecycle(page,demo_records,live_server):
    open_lab(page,demo_records,live_server);page.clock.install()
    page.locator('#battery-run').click();page.clock.run_for(2100)
    page.locator('#battery-pause').click();status=page.locator('#battery-status').inner_text()
    page.clock.run_for(2100);assert page.locator('#battery-status').inner_text()==status
    page.locator('#battery-mode').select_option('supply')
    expect(page.locator('#battery-status')).to_contain_text('pending live input')
    page.locator('#battery-step').click()
    expect(page.locator('#battery-readouts')).to_contain_text('50.4 A')
    page.locator('#battery-input-controls-magnitudeA').fill('')
    expect(page.locator('#battery-error')).to_be_visible();expect(page.locator('#battery-run')).to_be_disabled()
    page.locator('#battery-input-controls-magnitudeA').fill('100')
    expect(page.locator('#battery-run')).to_be_enabled()
    page.locator('#battery-input-parameters-initial_soc_pct').fill('60')
    expect(page.locator('#battery-status')).to_contain_text('0 / 3600 s')
    expect(page.locator('#battery-soc-label')).to_have_text('60% state of charge')
    page.locator('#battery-run').click();page.clock.run_for(1100)
    page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
    expect(page.locator('#battery-status')).to_contain_text('tab was hidden')
    status=page.locator('#battery-status').inner_text();page.clock.run_for(3000)
    assert page.locator('#battery-status').inner_text()==status
    page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));window.dispatchEvent(new PageTransitionEvent('pagehide'));window.dispatchEvent(new PageTransitionEvent('pageshow'))")
    page.locator('#battery-baseline').click();page.locator('#battery-run').click();page.clock.run_for(1100)
    expect(page.locator('#battery-status')).to_contain_text('1 / 3600 s')


@pytest.mark.parametrize('width',[1440,768,390])
def test_battery_visual_accessible_and_limit_presets(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':1000})
    open_lab(page,demo_records,live_server)
    DEST.mkdir(parents=True,exist_ok=True)
    for id,expected in [('default','Charging'),('rated','limited'),('derating','limited'),('cold','blocked')]:
        load(page,id)
        expect(page.locator('#battery-decision')).to_contain_text(expected,ignore_case=True)
        page.locator('#battery-stage').screenshot(path=str(DEST/f'{id}-{width}.png'))
    expect(page.locator('#battery-charge-flow')).not_to_have_class('battery-flow active')
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    page.emulate_media(reduced_motion='reduce');load(page,'default');page.locator('#battery-run').click()
    assert page.locator('#battery-charge-flow').evaluate("el=>getComputedStyle(el).animationName")=='none'
    page.locator('#battery-pause').click()
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    violations=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
    assert not violations,json.dumps(violations,indent=2)


def test_battery_preview_recording(browser,demo_records,live_server):
    DEST.mkdir(parents=True,exist_ok=True)
    context=browser.new_context(viewport={'width':1440,'height':1000},record_video_dir=str(DEST/'video'),record_video_size={'width':1440,'height':1000})
    page=context.new_page()
    try:
        open_lab(page,demo_records,live_server)
        for id in ['default','empty','derating','cold']:
            load(page,id);page.locator('#battery-stage').scroll_into_view_if_needed()
            page.locator('#battery-run').click();page.wait_for_timeout(1800)
            page.locator('#battery-pause').click()
            page.locator('#battery-stage').screenshot(path=str(DEST/f'preview-{id}.png'))
        video=page.video
    finally:
        context.close()
    video.save_as(str(DEST/'battery-energy-preview.webm'))
