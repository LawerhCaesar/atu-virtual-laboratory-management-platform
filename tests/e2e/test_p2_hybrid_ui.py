import csv
import io
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect

pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]


def open_p2(page,demo_records,live_server):
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.get_by_role('link',name='Virtual laboratory',exact=True).click()
    page.get_by_role('link',name='Enter HEV environment',exact=True).click()
    expect(page.locator('.lab-model-grid article')).to_have_count(4)
    page.get_by_role('link',name='Open P2 Full-Parallel Hybrid',exact=True).click()
    expect(page.locator('#tour-title')).to_have_text('Explore P2 Full-Parallel Hybrid')
    page.get_by_role('button',name='Close module guide',exact=True).click()


def run(page):
    page.get_by_role('button',name='Run simulation',exact=True).click()
    expect(page.locator('#p2-status')).to_contain_text('Calculation complete',timeout=20000)


def output(page,key):return page.locator(f'[data-p2-output="{key}"]')


def test_p2_reference_export_charts_and_replay(page,demo_records,live_server):
    # Isolate module replay from cross-document navigation transitions before
    # installing Playwright's virtual clock. Restoring motion tests the real scene.
    page.emulate_media(reduced_motion='reduce')
    open_p2(page,demo_records,live_server)
    page.emulate_media(reduced_motion='no-preference')
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    run(page)
    expect(output(page,'engine_torque_nm')).to_have_text('70.000')
    expect(output(page,'motor_torque_nm')).to_have_text('70.000')
    expect(output(page,'battery_energy_used_wh')).to_have_text('178.899')
    expect(page.locator('[data-scope-group]')).to_have_count(7)
    expect(page.locator('#p2-charts figure')).to_have_count(19)
    expect(page.locator('#p2-charts .p2-chart-legend')).to_have_count(19)
    expect(page.locator('#p2-engine-path')).to_have_attribute('data-active','true')
    with page.expect_download() as dl:page.get_by_role('button',name='Export JSON',exact=True).click()
    data=json.loads(Path(dl.value.path()).read_text())
    assert len(data['time_series'])==3001 and len(data['summary'])==23
    with page.expect_download() as dl:page.get_by_role('button',name='Export HybridResults CSV',exact=True).click()
    rows=list(csv.reader(io.StringIO(Path(dl.value.path()).read_text())))
    assert len(rows)==3002 and len(rows[0])==13
    assert rows[0][1:]==['T_req_Nm','T_engine_Nm','T_motor_Nm','T_wheel_requested_Nm','T_wheel_actual_Nm','SOC_percent','Battery_current_A','Battery_energy_Wh','Battery_loss_energy_Wh','Battery_efficiency_percent','Torque_RMSE_Nm','Torque_regime_code']
    assert float(rows[-1][8])==data['summary']['battery_energy_used_wh']
    page.get_by_label('Recorded time',exact=False).evaluate("e=>{e.value='15';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    expect(output(page,'battery_energy_used_wh')).to_have_text('89.450')
    expect(page.locator('#p2-sample')).to_contain_text('Recorded sample at 15.000')
    page.get_by_role('button',name='Zoom all charts',exact=True).click()
    expect(page.locator('#p2-window')).to_have_text('7.50–22.50 s')
    page.get_by_role('button',name='Reset chart zoom',exact=True).click()
    expect(page.locator('#p2-window')).to_have_text('0.00–30.00 s')
    with page.expect_download() as dl:page.locator('#p2-charts').get_by_role('button',name='Export chart SVG',exact=True).first.click()
    assert '<svg' in Path(dl.value.path()).read_text()
    page.clock.install();page.get_by_role('button',name='Restart replay',exact=True).click()
    page.get_by_role('button',name='Play response',exact=True).click();page.clock.run_for(2000)
    page.get_by_role('button',name='Pause response',exact=True).click()
    value=page.locator('#p2-time').inner_text();assert float(value)>1.5
    page.clock.run_for(500);expect(page.locator('#p2-time')).to_have_text(value)
    expect(page.locator('.p2-scene')).to_have_attribute('data-playing','false')
    assert not errors


def test_p2_inputs_limits_sessions_and_comparison(page,demo_records,live_server):
    open_p2(page,demo_records,live_server)
    page.get_by_label('Requested torque (Nm)',exact=True).fill('-1')
    expect(page.get_by_role('button',name='Run simulation',exact=True)).to_be_disabled()
    expect(page.locator('#p2-input-requested_torque_nm-error')).to_contain_text('0–400')
    page.get_by_role('button',name='Low · 60 Nm',exact=True).click()
    page.get_by_label('Initial SOC (fraction)',exact=True).fill('.25');run(page)
    expect(output(page,'motor_torque_nm')).to_have_text('0.000')
    expect(output(page,'engine_torque_nm')).to_have_text('60.000')
    expect(page.locator('[data-component=clutch]')).to_contain_text('CLOSED')
    expect(page.locator('#p2-warnings')).to_contain_text('SOC protection')
    page.get_by_role('button',name='Save session locally',exact=True).click()
    page.get_by_role('button',name='Reset to defaults',exact=True).click()
    expect(page.get_by_role('button',name='Export JSON',exact=True)).to_be_disabled()
    page.get_by_role('button',name='Load saved session',exact=True).click()
    expect(page.get_by_label('Initial SOC (fraction)',exact=True)).to_have_value('0.25')
    page.get_by_role('button',name='Reset to defaults',exact=True).click()
    page.get_by_label('Requested torque (Nm)',exact=True).fill('300')
    page.get_by_role('button',name='Compare Low / Medium / High',exact=True).click()
    expect(page.locator('#p2-status')).to_contain_text('Comparison complete',timeout=20000)
    expect(page.get_by_label('Requested torque (Nm)',exact=True)).to_have_value('140')
    expect(page.locator('#p2-comparison-table')).to_contain_text('153.937')
    expect(page.locator('#p2-comparison-table')).to_contain_text('178.899')
    expect(page.locator('#p2-comparison-table')).to_contain_text('303.708')
    expect(page.locator('#p2-comparison-charts figure')).to_have_count(10)
    with page.expect_download() as dl:page.get_by_role('button',name='Export comparison JSON',exact=True).click()
    data=json.loads(Path(dl.value.path()).read_text());assert len(data['cases'])==3
    with page.expect_download() as dl:page.get_by_role('button',name='Export comparison CSV',exact=True).click()
    assert len(list(csv.DictReader(io.StringIO(Path(dl.value.path()).read_text()))))==3
    page.get_by_label('Requested torque (Nm)',exact=True).fill('400')
    expect(page.locator('#p2-comparison')).not_to_be_visible()
    page.get_by_label('Motor speed (rpm)',exact=True).fill('6000');run(page)
    expect(page.locator('#p2-warnings')).to_contain_text('Engine torque saturation')
    assert float(output(page,'torque_rmse_nm').inner_text())>0


@pytest.mark.parametrize('width',[1280,390])
def test_p2_responsive_accessible_and_evidence(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce')
    open_p2(page,demo_records,live_server)
    dest=Path('test-results/p2-hybrid');dest.mkdir(parents=True,exist_ok=True)
    for name,torque in [('Low',60),('Medium',140),('High',240)]:
        page.get_by_role('button',name=f'{name} · {torque} Nm',exact=True).click();run(page)
        expect(page.locator('[data-component=clutch]')).to_contain_text('OPEN' if name=='Low' else 'CLOSED')
        expect(page.locator('#p2-engine-path')).to_have_attribute('data-active','false' if name=='Low' else 'true')
        expect(page.get_by_role('button',name='Play response',exact=True)).to_be_disabled()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.locator('.p2-visual').scroll_into_view_if_needed()
        page.screenshot(path=str(dest/f'{name.lower()}-{width}.png'))
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    report=page.evaluate("async()=>await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
    assert not report['violations'],json.dumps(report['violations'],indent=2)
    page.locator('#p2-plots').scroll_into_view_if_needed();page.screenshot(path=str(dest/f'charts-{width}.png'))
    page.get_by_label('Requested torque (Nm)',exact=True).fill('300')
    page.get_by_role('button',name='Compare Low / Medium / High',exact=True).click()
    expect(page.locator('#p2-status')).to_contain_text('Comparison complete',timeout=20000)
    expect(page.get_by_label('Requested torque (Nm)',exact=True)).to_have_value('140')
    page.locator('#p2-comparison').scroll_into_view_if_needed();page.screenshot(path=str(dest/f'comparison-{width}.png'))
    # The print report contains the final sample, even while replay shows an earlier one.
    page.evaluate('window.print=()=>{}')
    page.get_by_role('button',name='Print result summary',exact=True).click()
    page.emulate_media(media='print')
    expect(page.locator('#p2-print-report')).to_be_visible()
    expect(page.locator('#p2-print-report')).to_contain_text('178.899286')
