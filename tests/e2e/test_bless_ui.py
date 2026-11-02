import csv
import io
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
from apps.core.fcev_market import seed_book
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
DEST=Path('test-results/bless');DEST.mkdir(parents=True,exist_ok=True)

def open_lab(page,demo_records,live_server):
    page.route('**/virtual-lab/fcev/market-prices/',lambda route:route.fulfill(json=seed_book()))
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address or index number',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.goto(live_server.url+'/virtual-lab/fcev/fuel-cell-battery-diesel/')
    expect(page.locator('#tour-title')).to_contain_text('FCEV Range Extended System')
    page.get_by_role('button',name='Close module guide',exact=True).click()

def run(page):
    page.locator('#bless-run').click();expect(page.locator('#bless-status')).to_contain_text('Calculation complete',timeout=30000)

def example(page,name):
    page.locator('#bless-example').select_option(name);page.locator('#bless-load-example').click();run(page)

def advanced(page,tab='study'):
    page.locator('#bless-advanced').evaluate('e=>e.open=true');page.locator('#bless-tab-'+tab).click()

def test_distance_pair_currency_and_custom_prices(page,demo_records,live_server):
    page.emulate_media(reduced_motion='reduce');open_lab(page,demo_records,live_server)
    page.locator('#bless-distance').fill('5');run(page)
    data=page.evaluate('FcevLab.result');distance=data['samples'][-1]['streams']['comparison'][1]
    assert distance>=5 and data['samples'][-2]['streams']['comparison'][1]<5
    assert data['study']['distanceReached'];assert len(data['study']['batteryOnly']['samples'])==len(data['samples'])
    assert page.locator('#bless-vehicle').count()==0
    assert page.locator('#bless-electric').bounding_box()['y']<page.locator('#bless-diesel').bounding_box()['y']
    expect(page.locator('#bless-price-sources')).to_contain_text('reference_snapshot') if page.locator('#bless-price-sources').is_visible() else None
    before=page.evaluate('FcevLab.scenario.parameters')
    page.locator('#bless-currency').select_option('USD')
    after=page.evaluate('FcevLab.scenario.parameters')
    for key in ['electricity_ghs_per_kwh','delivered_hydrogen_ghs_per_kg','diesel_ghs_per_litre']:assert after[key]==pytest.approx(before[key],abs=1e-10)
    assert page.evaluate('FcevLab.result.samples.at(-1).streams.comparison[1]')==distance
    page.locator('#bless-param-delivered_hydrogen_ghs_per_kg').fill('20')
    assert page.evaluate('FcevLab.scenario.parameters.delivered_hydrogen_ghs_per_kg')==pytest.approx(232.4)
    expect(page.locator('#bless-price-status')).to_contain_text('custom')
    expect(page.locator('#bless-json')).to_be_disabled()
    page.locator('#bless-price-refresh').click();expect(page.locator('#bless-price-refresh')).to_be_enabled(timeout=10000)
    expect(page.locator('#bless-param-delivered_hydrogen_ghs_per_kg')).to_have_value('20')
    run(page);assert page.evaluate('FcevLab.result.study.priceMode')=='custom'
    page.locator('#bless-reset').click();expect(page.locator('#bless-kpis')).to_be_empty();expect(page.locator('#bless-distance')).to_have_value('100')
    assert page.locator('[data-param][readonly]').count()==0
    advanced(page,'battery');page.locator('#bless-param-battery_np').fill('42');page.locator('#bless-param-battery_current_ratings_C').fill('1.5, 2');page.locator('#bless-distance').fill('2');run(page)
    assert page.evaluate('FcevLab.result.scenario.parameters.battery_np')==42
    assert page.evaluate('FcevLab.result.scenario.parameters.battery_current_ratings_C')==[1.5,2]
    page.locator('#bless-reset').click();expect(page.locator('#bless-param-battery_np')).to_have_value('41')

def test_native_example_full_resolution_exports_and_extended_roundtrip(page,demo_records,live_server):
    open_lab(page,demo_records,live_server);example(page,'default_cycle')
    expect(page.locator('[data-bless-output=battery_soc_pct]')).to_have_text('61.984 %')
    expect(page.locator('[data-bless-output=energySaving]')).to_have_text('61.719 %')
    expect(page.locator('[data-bless-output=electricRefill]')).to_have_text('Unavailable')
    expect(page.locator('.bless-chart')).to_have_count(18)
    with page.expect_download() as dl:page.locator('#bless-json').click()
    data=json.loads(Path(dl.value.path()).read_text());assert len(data['samples'])==3601;assert len(data['samples'][0]['streams']['electric'])==51
    with page.expect_download() as dl:page.locator('#bless-csv').click()
    rows=list(csv.reader(io.StringIO(Path(dl.value.path()).read_text())));assert len(rows)==3601 and len(rows[0])==39
    page.locator('#bless-cursor').fill('100');expect(page.locator('#bless-time')).to_have_text('100')
    expect(page.locator('.chart-reading').first).to_contain_text('100 s')
    page.locator('#bless-save').click();advanced(page);page.locator('#bless-duration').fill('50');page.locator('#bless-restore').click();expect(page.locator('#bless-duration')).to_have_value('3600')
    with page.expect_download() as dl:page.locator('#bless-scenario-export').click()
    content=Path(dl.value.path()).read_text();assert json.loads(content)['fcevStudyOptions']['mode']=='duration'
    page.locator('#bless-import').set_input_files({'name':'scenario.json','mimeType':'application/json','buffer':content.encode()})
    expect(page.locator('#bless-mode')).to_have_value('duration')

def test_constraints_limits_and_cancellation(page,demo_records,live_server):
    open_lab(page,demo_records,live_server);example(page,'uphill_shortfall')
    expect(page.locator('#bless-eligibility')).to_contain_text('Native comparison eligible: No')
    expect(page.locator('#bless-demand')).to_contain_text('not fully supported')
    example(page,'hydrogen_depletion');expect(page.locator('[data-bless-output=hydrogen_remaining_kg]')).to_have_text('0.000 kg')
    example(page,'priced_cycle');expect(page.locator('#bless-eligibility')).to_contain_text('Cost saving eligible: Yes')
    page.locator('#bless-mode').select_option('distance');page.locator('#bless-distance').fill('1000');advanced(page);page.locator('#bless-duration').fill('2');run(page)
    expect(page.locator('#bless-route-summary')).to_contain_text('time limit reached before target')
    page.locator('#bless-duration').fill('14400');page.locator('#bless-run').click();page.locator('#bless-cancel').click();expect(page.locator('#bless-status')).to_contain_text('cancelled')
    page.locator('#bless-duration').fill('0');expect(page.locator('#bless-errors')).to_contain_text('Duration');expect(page.locator('#bless-run')).to_be_disabled()

@pytest.mark.parametrize('width',[1440,1024,390])
def test_analytical_layout_help_guide_and_accessibility(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':900});page.emulate_media(reduced_motion='reduce');open_lab(page,demo_records,live_server)
    page.locator('#bless-distance').fill('2');run(page)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    button=page.get_by_role('button',name='Explain Overall distance',exact=True);button.click();expect(button).to_have_attribute('aria-expanded','true');button.click();expect(button).to_have_attribute('aria-expanded','false')
    advanced(page,'battery');expect(page.locator('#bless-panel-battery')).to_be_visible();advanced(page,'electric');expect(page.locator('#bless-panel-electric')).to_be_visible()
    page.locator('#bless-learning-guide > summary').click()
    link=page.get_by_role('link',name='Download complete learning guide (PDF)');response=page.request.get(live_server.url+link.get_attribute('href'));assert response.status==200;assert response.body().startswith(b'%PDF')
    page.locator('#fcev-hiace-reference > summary').click();expect(page.locator('#fcev-hiace-reference')).to_contain_text('1GD-FTV')
    page.add_script_tag(path='node_modules/axe-core/axe.min.js');report=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations")
    assert not report,json.dumps(report,indent=2)
    for key in ['stage','electric','diesel','results']:page.locator('#bless-'+key).screenshot(path=str(DEST/f'{key}-{width}.png'))
    with page.expect_download() as dl:page.get_by_role('button',name='Download Battery state of charge chart SVG',exact=True).click()
    assert '<svg' in Path(dl.value.path()).read_text()

def test_pending_and_failed_quotes_preserve_custom_experiment(page,demo_records,live_server):
    open_lab(page,demo_records,live_server);page.locator('#bless-distance').fill('2')
    expect(page.locator('#bless-price-refresh')).to_be_enabled(timeout=10000)
    page.unroute('**/virtual-lab/fcev/market-prices/');pending=[]
    page.route('**/virtual-lab/fcev/market-prices/',lambda route:pending.append(route))
    page.locator('#bless-price-refresh').click();expect(page.locator('#bless-run')).to_be_disabled()
    page.locator('#bless-param-delivered_hydrogen_ghs_per_kg').fill('100');expect(page.locator('#bless-run')).to_be_enabled();run(page)
    assert pending
    revised=seed_book();revised['hydrogen']['value']=999;pending[0].fulfill(json=revised)
    expect(page.locator('#bless-price-refresh')).to_be_enabled(timeout=10000)
    expect(page.locator('#bless-param-delivered_hydrogen_ghs_per_kg')).to_have_value('100')
    assert page.evaluate('FcevLab.result.scenario.parameters.delivered_hydrogen_ghs_per_kg')==100
    page.unroute('**/virtual-lab/fcev/market-prices/');page.route('**/virtual-lab/fcev/market-prices/',lambda route:route.abort())
    page.locator('#bless-price-refresh').click();expect(page.locator('#bless-price-refresh')).to_be_enabled(timeout=10000)
    expect(page.locator('#bless-price-status')).to_contain_text('Online refresh unavailable')
    expect(page.locator('#bless-param-delivered_hydrogen_ghs_per_kg')).to_have_value('100')
