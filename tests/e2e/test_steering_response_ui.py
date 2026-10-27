import csv
import io
import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]

def open_steering(page,demo_records,live_server):
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.get_by_role('link',name='Virtual laboratory',exact=True).click()
    page.get_by_role('link',name='Enter VD environment',exact=True).click()
    expect(page.locator('.lab-model-grid article')).to_have_count(2)
    page.get_by_role('link',name='Open Vehicle Steering Response',exact=True).click()
    expect(page.locator('#steering-title')).to_contain_text('Vehicle Steering Response')
    expect(page.locator('#tour-title')).to_have_text('Explore Vehicle Steering Response')
    page.get_by_role('button',name='Close module guide',exact=True).click()

def run(page):
    page.get_by_role('button',name='Run simulation',exact=True).click()
    expect(page.locator('#steering-status')).to_contain_text('Calculation complete',timeout=20000)

def output(page,key):
    return page.locator(f'[data-steering-output="{key}"]')

def test_reference_charts_exports_and_playback(page,demo_records,live_server):
    open_steering(page,demo_records,live_server);run(page)
    expect(output(page,'yawRateDegPerS')).to_have_text('4.703')
    expect(output(page,'sideslipDeg')).to_have_text('-0.17837')
    expect(output(page,'xM')).to_have_text('153.963')
    expect(page.locator('.steering-plot-group')).to_have_count(4)
    expect(page.locator('.steering-chart-grid svg')).to_have_count(10)
    expect(page.locator('.steering-chart-grid svg polyline')).to_have_count(11)
    with page.expect_download() as dl:
        page.get_by_role('button',name='Export JSON',exact=True).click()
    data=json.loads(Path(dl.value.path()).read_text())
    assert len(data['samples'])==1001 and len(data['platformVector'])==11
    assert data['platformVector']==[data['final'][key] for key in data['outputVectorOrder']]
    assert data['final']['yawRateDegPerS']==pytest.approx(4.70272086,abs=1e-7)
    with page.expect_download() as dl:
        page.get_by_role('button',name='Export CSV',exact=True).click()
    rows=list(csv.DictReader(io.StringIO(Path(dl.value.path()).read_text())))
    assert len(rows)==len(data['samples'])
    assert float(rows[-1]['yM'])==data['final']['yM']
    scrub=page.get_by_label('Playback position',exact=False)
    scrub.evaluate("e=>{e.value='0.5';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    expect(page.locator('#steering-wheel-fl')).to_have_attribute('transform','translate(1.2 -0.8245) rotate(0)')
    scrub.evaluate("e=>{e.value='2';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    row=data['samples'][200]
    assert f"rotate({-row['headingDeg']})" in page.locator('#steering-car').get_attribute('transform')
    expect(page.locator('#steering-wheel-fl')).to_have_attribute('transform','translate(1.2 -0.8245) rotate(-1)')
    assert page.locator('#steering-trail').get_attribute('points')
    page.clock.install()
    page.get_by_role('button',name='Restart playback',exact=True).click()
    page.get_by_role('button',name='Play animation',exact=True).click()
    page.clock.run_for(2000)
    page.get_by_role('button',name='Pause animation',exact=True).click()
    before=page.locator('#steering-time').inner_text();assert float(before)>1
    page.clock.run_for(1000);expect(page.locator('#steering-time')).to_have_text(before)
    page.get_by_role('button',name='Clear results',exact=True).click()
    expect(page.get_by_role('button',name='Export JSON',exact=True)).to_be_disabled()
    expect(page.locator('#steering-full-path')).to_have_attribute('points','')

def test_edits_profiles_validation_and_baseline_scenario(page,demo_records,live_server):
    open_steering(page,demo_records,live_server)
    page.get_by_label('Road-wheel steering amplitude (deg)',exact=True).fill('0');run(page)
    expect(output(page,'yawRateDegPerS')).to_have_text('0.000')
    expect(output(page,'yM')).to_have_text('0.000')
    page.get_by_label('Output time step (s)',exact=True).fill('0.1')
    expect(page.locator('#steering-error')).to_contain_text('0.001–0.05')
    expect(page.get_by_role('button',name='Run simulation',exact=True)).to_be_disabled()
    expect(page.get_by_role('button',name='Export JSON',exact=True)).to_be_disabled()
    page.get_by_role('button',name='Reset to defaults',exact=True).click()
    expect(page.get_by_label('Road-wheel steering amplitude (deg)',exact=True)).to_have_value('1')
    page.get_by_label('Simulation duration (s)',exact=True).fill('2.005');run(page)
    expect(page.locator('#steering-time')).to_have_text('2.005')
    for preset in ['sine','doublet','baseline']:
        page.get_by_label('Scenario',exact=True).select_option(preset)
        page.get_by_role('button',name='Load scenario',exact=True).click();run(page)
    expect(page.get_by_label('Base vehicle mass (kg)',exact=True)).to_have_value('2000')
    a=float(page.get_by_label('CG to front axle (m)',exact=True).input_value())
    b=float(page.get_by_label('CG to rear axle (m)',exact=True).input_value())
    assert a+b==pytest.approx(2.875)

@pytest.mark.parametrize('width',[1280,390])
def test_accessible_responsive_trajectory_and_visual_evidence(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':900});page.emulate_media(reduced_motion='reduce')
    open_steering(page,demo_records,live_server);run(page)
    expect(page.get_by_role('button',name='Play animation',exact=True)).to_be_disabled()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    report=page.evaluate("async () => await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
    assert not report['violations'],json.dumps(report['violations'],indent=2)
    dest=Path('test-results/steering-response');dest.mkdir(parents=True,exist_ok=True)
    if width == 1280:
        page.screenshot(path=str(dest/f'full-interface-{width}.png'),full_page=True)
    else:
        page.screenshot(path=str(dest/f'mobile-page-{width}.png'))
    page.locator('#steering-visual-title').scroll_into_view_if_needed()
    page.locator('.steering-visual').screenshot(path=str(dest/f'trajectory-{width}.png'))
    scrub=page.locator('#steering-scrub');scrub.evaluate("e=>{e.value='2';e.dispatchEvent(new Event('input',{bubbles:true}));}")
    page.locator('.steering-visual').screenshot(path=str(dest/f'steering-event-{width}.png'))
