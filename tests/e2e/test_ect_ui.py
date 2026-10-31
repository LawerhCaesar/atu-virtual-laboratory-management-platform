import csv
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
DEST=Path('test-results/ect')

def open_lab(page,demo_records,live_server):
    page.emulate_media(reduced_motion="reduce")
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.goto(live_server.url+'/virtual-lab/ice/coolant-temperature/')
    expect(page.locator('#tour-title')).to_contain_text('Coolant Temperature')
    page.locator('#tour-next').click();page.locator('#tour-show').click()
    expect(page.locator('#ect-engine-explorer')).to_have_class('ect-explorer tour-target-highlight')
    page.get_by_role('button',name='Close module guide',exact=True).click()

def end(page):page.locator('#timeline').fill('12000')
def value(page,key):return float(page.locator(f'[data-value="{key}"]').inner_text())

def test_ect_scenarios_exports_and_validation(page,demo_records,live_server):
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)));open_lab(page,demo_records,live_server)
    end(page);assert value(page,'ADC_Count')==268
    assert value(page,'Sensor_Temperature_C')==100
    with page.expect_download() as dl:page.locator('#export').click()
    rows=list(csv.DictReader(Path(dl.value.path()).read_text().splitlines()))
    assert len(rows)==12001
    assert float(rows[2000]['Sensor_Temperature_C'])==pytest.approx(20.0444444444)
    assert float(rows[-1]['Reconstructed_Temperature_C'])==pytest.approx(100.001692613)
    for preset,temp in [('cooling',20),('fixed',85),('clamped',130)]:
        page.locator('#preset').select_option(preset);end(page)
        assert value(page,'Sensor_Temperature_C')==temp
        expect(page.locator('#input-status')).to_contain_text('CLAMPED' if preset=='clamped' else 'VALID')
    for preset,count in [('lowRail',0),('highRail',3)]:
        page.locator('#preset').select_option(preset);end(page)
        assert value(page,'ADC_Count')==count
        expect(page.locator('#conversion-status')).to_contain_text('INVALID')
        expect(page.locator('#estimate-state')).to_have_text('FALLBACK / INVALID')
    page.locator('#ect-settings summary').click()
    page.get_by_label('Time constant (s)',exact=True).fill('0')
    page.get_by_role('button',name='Apply and reset',exact=True).click()
    expect(page.locator('#settings-error')).to_contain_text('positive')
    assert value(page,'ADC_Count')==3
    page.get_by_role('button',name='Restore defaults',exact=True).click()
    page.get_by_label('Time constant (s)',exact=True).fill('6')
    page.get_by_role('button',name='Apply and reset',exact=True).click()
    expect(page.locator('#settings-error')).to_have_text('')
    expect(page.locator('#timeline')).to_have_value('0')
    page.locator('#reset').click();assert value(page,'Sensor_Temperature_C')==20
    assert not errors

def test_ect_playback_pause_hidden_and_keyboard(page,demo_records,live_server):
    open_lab(page,demo_records,live_server);page.clock.install();page.locator('#speed').select_option('20')
    page.locator('#play').click();page.clock.run_for(1600);page.locator('#play').click()
    t=page.locator('#timeline').input_value();assert int(t)>2000
    page.clock.run_for(1000);expect(page.locator('#timeline')).to_have_value(t)
    page.locator('#play').click()
    page.evaluate("Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
    expect(page.locator('#run-status')).to_contain_text('page was hidden')
    page.locator('#reset').click();page.locator('#timeline').focus();page.keyboard.press('End')
    expect(page.locator('#timeline')).to_have_value('12000')
    page.locator('#reset').click();expect(page.locator('#timeline')).to_have_value('0')

@pytest.mark.parametrize('width',[1440,390])
def test_ect_visual_accessibility(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':1050});page.emulate_media(reduced_motion='reduce')
    open_lab(page,demo_records,live_server);DEST.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(DEST/f'initial-{width}.png'),full_page=True)
    page.locator('#timeline').fill('2300');page.screenshot(path=str(DEST/f'warmup-{width}.png'),full_page=True)
    end(page);page.screenshot(path=str(DEST/f'final-{width}.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    violations=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
    assert not violations,__import__("json").dumps(violations,indent=2)
    page.locator('#preset').select_option('lowRail');end(page)
    page.screenshot(path=str(DEST/f'rail-invalid-{width}.png'),full_page=True)
    expect(page.locator('#estimate-state')).to_have_text('FALLBACK / INVALID')
