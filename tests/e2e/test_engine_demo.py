import csv
import io
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect

pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]


def open_engine(page,demo_records,live_server):
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.get_by_role('link',name='Virtual laboratory',exact=True).click()
    page.get_by_role('link',name='Enter ICE environment',exact=True).click()
    page.get_by_role('link',name='Open Engine Live Data Demonstration',exact=True).click()
    expect(page.get_by_role('heading',name='Engine Live Data Demonstration',exact=True)).to_be_visible()
    expect(page.locator('#tour-title')).to_have_text('Explore Engine Live Data Demonstration')
    page.get_by_role('button',name='Close module guide',exact=True).click()


def start_engine(page):
    page.get_by_role('button',name='Run simulation',exact=True).click()
    page.get_by_label('Ignition switch',exact=True).check()
    page.get_by_label('Simulated authorisation',exact=True).check()
    page.get_by_role('button',name='Start engine',exact=True).click()
    page.clock.run_for(3000)
    expect(page.locator('#engine-state')).to_have_text('RUN')


def test_live_run_pause_pending_emergency_preset_and_csv(page,demo_records,live_server):
    page.emulate_media(reduced_motion='reduce')
    open_engine(page,demo_records,live_server)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.clock.install()
    expect(page.get_by_role('button',name='Start engine',exact=True)).to_be_disabled()
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_disabled()
    page.get_by_role('button',name='Fuel and injection',exact=True).click()
    start_engine(page)
    expect(page.locator('[data-signal="InjectorPW"]')).to_have_text('1.679 ms')
    destination=Path('test-results/engine-live-data');destination.mkdir(parents=True,exist_ok=True)
    page.locator('#engine-chart').scroll_into_view_if_needed();page.screenshot(path=str(destination/'warm-run-trends.png'))
    page.get_by_role('button',name='Pause',exact=True).click()
    time=page.locator('#engine-time').inner_text();page.clock.run_for(1000)
    expect(page.locator('#engine-time')).to_have_text(time)
    page.get_by_label('Oxygen-sensor voltage (V)',exact=True).fill('0.10')
    expect(page.locator('#engine-pending')).to_contain_text('pending')
    expect(page.locator('[data-signal="InjectorPW"]')).to_have_text('1.679 ms')
    page.get_by_role('button',name='Step 0.05 s',exact=True).click()
    expect(page.locator('[data-signal="InjectorPW"]')).to_have_text('1.926 ms')
    expect(page.locator('[data-signal="STFT"]')).to_have_text('14.7 %')
    page.get_by_role('button',name='Emergency stop',exact=True).click()
    expect(page.locator('#engine-state')).to_have_text('RUN')
    expect(page.locator('#engine-pending')).to_contain_text('pending')
    page.get_by_role('button',name='Step 0.05 s',exact=True).click()
    expect(page.locator('#engine-state')).to_have_text('SHUTDOWN')
    page.get_by_role('button',name='Cooling',exact=True).click()
    expect(page.locator('[data-signal="FanDuty"]')).to_have_text('0.0 %')
    expect(page.locator('[data-signal="WaterPumpDuty"]')).to_have_text('0.0 %')
    with page.expect_download() as dl:page.get_by_role('button',name='Export CSV',exact=True).click()
    rows=list(csv.DictReader(io.StringIO(Path(dl.value.path()).read_text())))
    assert rows[-1]['EmergencyStop']=='1' and rows[-1]['EngineState']=='4'
    assert rows[-2]['O2SensorVoltage']=='0.1' and rows[-2]['EngineState']=='3'
    assert len(rows[0])==46 and rows[0]['SimulationTime']=='0'
    page.get_by_label('Demonstration preset').select_option(label='ECT sensor disagreement')
    page.get_by_role('button',name='Load preset',exact=True).click()
    expect(page.get_by_role('button',name='Clear emergency',exact=True)).to_be_enabled()
    expect(page.locator('#engine-state')).to_have_text('OFF')
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_disabled()
    page.get_by_role('button',name='Clear emergency',exact=True).click()
    page.get_by_role('button',name='Step 0.05 s',exact=True).click()
    expect(page.locator('[data-signal="FanDuty"]')).to_have_text('100.0 %')
    expect(page.locator('[data-signal="WaterPumpDuty"]')).to_have_text('100.0 %')
    assert not errors


def test_reject_invalid_inputs_cap_and_off_cooling(page,demo_records,live_server):
    open_engine(page,demo_records,live_server)
    voltage=page.get_by_label('Battery voltage (V)',exact=True)
    voltage.fill('16');expect(page.locator('#accepted-BatteryVoltage')).to_contain_text('14.90 V')
    voltage.fill('');expect(page.locator('#accepted-BatteryVoltage')).to_contain_text('last accepted')
    page.get_by_role('button',name='Step 0.05 s',exact=True).click()
    expect(page.locator('#engine-state')).to_have_text('OFF')
    page.get_by_label('Virtual ECT1 sensor voltage (V)',exact=True).fill('0.6')
    page.get_by_label('Virtual ECT2 sensor voltage (V)',exact=True).fill('0.6')
    page.get_by_role('button',name='Step 0.05 s',exact=True).click()
    page.get_by_role('button',name='Cooling',exact=True).click()
    expect(page.locator('[data-signal="FanDuty"]')).to_have_text('100.0 %')
    expect(page.locator('[data-signal="WaterPumpDuty"]')).to_have_text('60.0 %')
    expect(page.locator('#engine-chart-status')).to_contain_text('2 recorded')
    expect(page.locator('#engine-chart text').filter(has_text='15 °C threshold')).to_have_count(1)
    page.get_by_label('Add another signal to the trends').select_option('ActualRPM')
    expect(page.locator('#engine-chart text').filter(has_text='Imposed actual RPM')).to_have_count(2)
    page.get_by_label('Inspect recorded sample').fill('0')
    expect(page.locator('#engine-chart-readout')).to_contain_text('0.00 s')
    page.get_by_role('button',name='Reset all',exact=True).click()
    expect(page.locator('#engine-mode')).to_contain_text('simulation paused')
    expect(page.get_by_role('button',name='Export CSV',exact=True)).to_be_disabled()


@pytest.mark.parametrize('width',[1280,390])
def test_engine_views_accessibility_and_visual_evidence(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':900});page.emulate_media(reduced_motion='reduce')
    open_engine(page,demo_records,live_server)
    page.get_by_role('button',name='Step 0.05 s',exact=True).click()
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    for view in ['Overview','Fuel and injection','Idle and ignition','Cooling','Start and run']:
        page.get_by_role('button',name=view,exact=True).click()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        report=page.evaluate("async()=>await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})")
        assert not report['violations'],json.dumps(report['violations'],indent=2)
    dest=Path('test-results/engine-live-data');dest.mkdir(parents=True,exist_ok=True)
    page.locator('#engine-schematic').scroll_into_view_if_needed();page.screenshot(path=str(dest/f'schematic-{width}.png'))
    page.get_by_role('button',name='Cooling',exact=True).click()
    page.locator('#engine-system').scroll_into_view_if_needed();page.screenshot(path=str(dest/f'cooling-{width}.png'))
    page.locator('#engine-chart').scroll_into_view_if_needed();page.screenshot(path=str(dest/f'trends-{width}.png'))
