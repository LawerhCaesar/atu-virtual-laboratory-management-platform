"""Focused correction evidence; browser exports are simulated values, not vehicle measurements."""
from pathlib import Path
from datetime import datetime,timezone
import pytest
from playwright.sync_api import expect
from test_engine_demo import open_engine,start_engine
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]

def freeze_clock(page):
    stamp=datetime(2026,11,16,tzinfo=timezone.utc)
    page.clock.install(time=stamp)
    page.clock.set_fixed_time(stamp)
    page.clock.pause_at(stamp)
    page.clock.set_system_time(stamp)

def test_engine_pause_correction(page,demo_records,live_server):
    open_engine(page,demo_records,live_server)
    freeze_clock(page)
    start_engine(page)
    page.locator('#engine-pause').click()
    expect(page.locator('#engine-pending')).to_have_text('Paused')
    paused=page.locator('#engine-time').inner_text()
    page.clock.run_for(500)
    expect(page.locator('#engine-time')).to_have_text(paused)
    page.locator('#engine-step').click()
    assert float(page.locator('#engine-time').inner_text())==pytest.approx(float(paused)+.05)
    page.locator('#engine-run').click()
    page.clock.run_for(100)
    page.locator('#engine-pause').click()
    assert float(page.locator('#engine-time').inner_text())>float(paused)+.05
    Path('test-results/corrections/screenshots').mkdir(parents=True,exist_ok=True)
    page.screenshot(path='test-results/corrections/screenshots/engine-pause-after.png')


@pytest.mark.parametrize('width',[1440,390])
def test_engine_scope_and_self_describing_export(page,demo_records,live_server,width):
    import csv,io,json
    page.set_viewport_size({'width':width,'height':1000})
    open_engine(page,demo_records,live_server)
    assert not page.get_by_role('button',name='Explain Fingerprint authorised',exact=True).count()
    expect(page.get_by_role('button',name='Explain Simulated authorisation',exact=True)).to_be_attached()
    freeze_clock(page)
    start_engine(page)
    page.locator('#engine-pause').click()
    page.get_by_role('button',name='Start and run',exact=True).click()
    expect(page.locator('#engine-schematic')).to_contain_text('Start request accepted')
    with page.expect_download() as download:page.locator('#engine-export-package').click()
    data=json.loads(Path(download.value.path()).read_text())
    assert len(data['signalDictionary'])==46
    assert all(s['unit'] for s in data['signalDictionary'])
    with page.expect_download() as download:page.locator('#engine-export').click()
    plain=Path(download.value.path()).read_text()
    assert plain==data['csv']['content'].replace('\r\n','\n')
    rows=list(csv.DictReader(io.StringIO(plain)))
    assert data['window']['retainedSamples']==len(rows)
    assert data['window']['lastTimeS']==float(rows[-1]['SimulationTime'])
    assert data['transitions']['totalTransitions']==3
    assert data['transitions']['events'][0]['fromState']=='OFF'
    assert 'physical 1NZ' not in page.locator('#engine-demo').inner_text()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.locator('#engine-learning-guide > summary').click()
    expect(page.locator('#engine-learning-content')).to_contain_text('5.05')
    page.screenshot(path=f'test-results/corrections/screenshots/engine-after-{width}.png')


def test_fuel_preview_record_and_comparison_clarity(page,demo_records,live_server):
    import json
    from test_fuel_delivery_ui import open_fuel
    errors=[];page.on("pageerror",lambda error:errors.append(str(error)))
    open_fuel(page,demo_records,live_server)
    if page.locator("#tour-close").is_visible():page.locator("#tour-close").click()
    freeze_clock(page)
    page.locator('#fuel-run').click()
    page.clock.run_for(30000)
    expect(page.locator('#fuel-mode')).to_have_text('Complete')
    with page.expect_download() as download:page.locator('#fuel-csv').click()
    original=Path(download.value.path()).read_bytes()
    page.get_by_label('Fuel optimisation scale (ratio)',exact=True).fill('.98')
    expect(page.locator('#fuel-preview-context')).to_contain_text('differs')
    expect(page.locator('#fuel-export-context')).to_contain_text('Current inputs differ')
    with page.expect_download() as download:page.locator('#fuel-csv').click()
    assert Path(download.value.path()).read_bytes()==original
    with page.expect_download() as download:page.locator('#fuel-json').click()
    data=json.loads(Path(download.value.path()).read_text())
    assert data['contexts']['currentPreview']['inputs']['fuelOptimisationScale']==.98
    assert data['contexts']['lastRecordedRun']['lastInputs']['fuelOptimisationScale']==1
    assert data['history'][-1]['inputs']['fuelOptimisationScale']==1
    page.locator('#fuel-compare').click()
    expect(page.locator('#fuel-comparison')).to_contain_text('Fresh comparison')
    expect(page.locator('#fuel-comparison')).to_contain_text('Completed-run fuel change')
    page.locator('#fuel-comparison').screenshot(path='test-results/corrections/screenshots/fuel-fresh-comparison.png')
    page.get_by_label('Measured lambda (ratio)',exact=True).fill('.95')
    page.locator('#fuel-recommend').click()
    expect(page.locator('#fuel-scale-advice')).to_contain_text('does not compensate')
    expect(page.locator('#fuel-scale-warning')).to_contain_text('lambda')
    expect(page.locator('#fuel-duty-status')).to_contain_text('theoretical demand')
    page.locator('#fuel-scale-advice').scroll_into_view_if_needed()
    page.screenshot(path='test-results/corrections/screenshots/fuel-suggested-scale-warning.png')
    page.locator('#fuel-analysis-title').scroll_into_view_if_needed()
    page.screenshot(path='test-results/corrections/screenshots/fuel-recorded-preview.png')
    assert not errors
