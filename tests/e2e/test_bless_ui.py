import csv
import io
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
DEST=Path('test-results/bless')

def open_lab(page,demo_records,live_server):
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.goto(live_server.url+'/virtual-lab/fcev/fuel-cell-battery-diesel/')
    expect(page.locator('#tour-title')).to_contain_text('Fuel-Cell / Battery')
    page.get_by_role('button',name='Close module guide',exact=True).click()


def run(page):
    page.get_by_role('button',name='Run scenario',exact=True).click()
    expect(page.locator('#bless-status')).to_contain_text('Calculation complete',timeout=30000)


def example(page,name):
    page.locator('#bless-example').select_option(name)
    page.get_by_role('button',name='Load example',exact=True).click()
    run(page)


def test_bless_default_stale_inputs_exports_and_playback(page,demo_records,live_server):
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    open_lab(page,demo_records,live_server);run(page)
    expect(page.locator('[data-bless-output="battery_soc_pct"]')).to_have_text('61.984 %')
    expect(page.locator('[data-bless-output="energySaving"]')).to_have_text('61.719 %')
    expect(page.locator('[data-bless-output="electricRefill"]')).to_have_text('Enter prices')
    expect(page.locator('#bless-charts figure')).to_have_count(9)
    with page.expect_download() as dl:page.locator('#bless-json').click()
    data=json.loads(Path(dl.value.path()).read_text());assert len(data['samples'])==3601
    assert data['scenario']['parameters']['battery_np']==41
    with page.expect_download() as dl:page.locator('#bless-csv').click()
    rows=list(csv.reader(io.StringIO(Path(dl.value.path()).read_text())))
    assert len(rows)==3601 and len(rows[0])==39
    assert float(rows[-1][3])==data['samples'][-1]['streams']['comparison'][2]
    page.locator('#bless-cursor').fill('100');expect(page.locator('#bless-time')).to_have_text('100')
    page.locator('#bless-step').click();expect(page.locator('#bless-time')).to_have_text('101')
    page.locator('#bless-param-target_speed_km_per_h').fill('60')
    expect(page.locator('#bless-status')).to_contain_text('Results from previous settings')
    expect(page.locator('#bless-sample')).to_contain_text('Results from previous settings')
    run(page);expect(page.locator('[data-bless-output="commanded_distance_km"]')).to_have_text('50.000 km')
    page.clock.install();page.locator('#bless-play').click();page.clock.run_for(2000)
    assert int(page.locator('#bless-time').inner_text())>0
    page.locator('#bless-pause').click();t=page.locator('#bless-time').inner_text();page.clock.run_for(2000);assert page.locator('#bless-time').inner_text()==t
    page.locator('#bless-reset').click();expect(page.locator('#bless-kpis')).to_be_empty();expect(page.locator('#bless-json')).to_be_disabled()
    assert not errors


def test_bless_constraints_cancel_and_roundtrip(page,demo_records,live_server):
    open_lab(page,demo_records,live_server)
    example(page,'uphill_shortfall')
    expect(page.locator('#bless-eligibility')).to_contain_text('No — Requested demand not fully supported')
    page.locator('#bless-cursor').fill('200');expect(page.locator('#bless-demand')).to_contain_text('not supported')
    DEST.mkdir(parents=True,exist_ok=True);page.locator('#bless-stage').screenshot(path=str(DEST/'overload.png'))
    with page.expect_download() as dl:page.locator('#bless-json').click()
    Path(DEST/'overload-result.json').write_text(Path(dl.value.path()).read_text())
    example(page,'hydrogen_depletion');expect(page.locator('[data-bless-output="hydrogen_remaining_kg"]')).to_have_text('0.0000 kg')
    expect(page.locator('#bless-flow')).to_contain_text('Inactive')
    example(page,'regeneration_high_soc');page.locator('#bless-cursor').fill('7')
    expect(page.locator('#bless-flow [data-reverse="true"]')).to_contain_text('Charging')
    example(page,'priced_cycle');expect(page.locator('#bless-eligibility')).to_contain_text('Cost comparison: Available')
    page.locator('#bless-save').click();page.locator('#bless-duration').fill('50');page.locator('#bless-restore').click();expect(page.locator('#bless-duration')).to_have_value('1200')
    with page.expect_download() as dl:page.locator('#bless-scenario-export').click()
    scenario=Path(dl.value.path()).read_text()
    page.locator('#bless-import').set_input_files({'name':'scenario.json','mimeType':'application/json','buffer':scenario.encode()})
    expect(page.locator('#bless-duration')).to_have_value('1200')
    page.locator('#bless-duration').fill('14400');page.locator('#bless-run').click();page.locator('#bless-cancel').click();expect(page.locator('#bless-status')).to_contain_text('cancelled')
    page.locator('#bless-duration').fill('0');page.locator('#bless-run').click();expect(page.locator('#bless-errors')).to_contain_text('Duration')


@pytest.mark.parametrize('width,height',[(1440,900),(1024,768),(390,844)])
def test_bless_responsive_accessible_and_chart_exports(page,demo_records,live_server,width,height):
    page.set_viewport_size({'width':width,'height':height});page.emulate_media(reduced_motion='reduce')
    open_lab(page,demo_records,live_server);run(page)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    report=page.evaluate("async()=>await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})")
    assert not report['violations'],json.dumps(report['violations'],indent=2)
    DEST.mkdir(parents=True,exist_ok=True)
    page.locator('#bless-stage').screenshot(path=str(DEST/f'stage-{width}.png'))
    page.locator('#bless-results').screenshot(path=str(DEST/f'results-{width}.png'))
    page.locator('#bless-analysis').screenshot(path=str(DEST/f'analysis-{width}.png'))
    page.locator('#bless-analysis details summary').click();page.locator('#bless-stream').select_option('electric');expect(page.locator('#bless-table tbody tr')).to_have_count(51)
    for i in [3,6]:
        with page.expect_download() as dl:page.locator(f'[data-chart-export="{i}"]').click()
        text=Path(dl.value.path()).read_text();assert 'Default cycle' in text and 'Time (s)' in text
        if width==1440:(DEST/f'default-chart-{i}.svg').write_text(text)


def test_bless_recorded_walkthrough(browser,demo_records,live_server):
    DEST.mkdir(parents=True,exist_ok=True)
    context=browser.new_context(viewport={'width':1440,'height':900},record_video_dir=str(DEST/'video'),record_video_size={'width':1440,'height':900})
    page=context.new_page()
    try:
        open_lab(page,demo_records,live_server);run(page)
        page.locator('#bless-cursor').fill('300');page.locator('#bless-stage').scroll_into_view_if_needed()
        page.locator('#bless-speed').select_option('60');page.locator('#bless-play').click();page.wait_for_timeout(8000)
        page.locator('#bless-pause').click();page.locator('#bless-cursor').fill('3400');page.wait_for_timeout(3000)
        page.locator('#bless-results').scroll_into_view_if_needed();page.wait_for_timeout(3000)
        example(page,'uphill_shortfall');page.locator('#bless-cursor').fill('200');page.locator('#bless-stage').scroll_into_view_if_needed();page.wait_for_timeout(5000)
        page.locator('#bless-play').click();page.wait_for_timeout(5000);page.locator('#bless-pause').click()
    finally:
        video=page.video;context.close();video.save_as(str(DEST/'walkthrough.webm'))
