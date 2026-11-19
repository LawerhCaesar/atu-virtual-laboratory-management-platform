"""Additional review acceptance checks. Synthetic browser inputs, never human voice evidence."""
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_yankson_practical import open_lab, contact
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]


def test_CIR_01_all_functional_paths_and_delivery(page,demo_records,live_server):
    open_lab(page,demo_records,live_server)
    page.locator('#yp-circuit').evaluate('e=>e.open=true')
    observations=[]
    mapping={'power':(7,0),'reference':(8,0),'interlock':(8,0),'match':(1,0),'contact':(0,0),'voice':(4,0),'canh':(9,1),'canl':(9,1),'transceiver':(9,1),'starter':(14,0),'run':(14,0)}
    for wire,(column,value) in mapping.items():
        page.locator('#yp-wire-'+wire).uncheck()
        page.locator('#ys-reset').click()
        page.locator('#ys-long').click()
        page.clock.run_for(2200)
        data=page.evaluate('YanksonLab.snapshot()')
        assert data['inputs'] and all(r[column+1]==value for r in data['inputs'])
        if wire in ['power','reference','interlock','match','contact','canh','canl','transceiver']:
            assert not any(r[3] for r in data['rows'])
        if wire=='voice':
            assert any(r[3] for r in data['rows']), 'Direct contact must remain independent of voice wire'
        if wire=='starter':
            assert any(r[3] for r in data['rows']), 'Requested actuation remains visible'
            trace=page.evaluate('YanksonTeaching.trace().supplementary')
            assert not any(r['energizedStarter'] for r in trace)
            expect(page.locator('#ya-stand-status')).to_contain_text('OFF / RELEASED')
        observations.append({'wire':wire,'effectiveInputColumn':column,'constrainedValue':value,'maximumStarterRequest':max(r[3] for r in data['rows']),'finalState':data['rows'][-1][1]})
        page.locator('#yp-wire-'+wire).check()
    page.locator('#ys-reset').click()
    page.locator('#ys-long').click()
    page.clock.run_for(5000)
    expect(page.locator('#ys-state')).to_contain_text('RUNNING')
    Path('test-results/corrections/all-paths.json').write_text(json.dumps(observations,indent=2))


@pytest.mark.parametrize('wire',['match','contact'])
@pytest.mark.parametrize('milliseconds',[300,1700])
@pytest.mark.parametrize('method',['keyboard','pointer'])
def test_CIR_02_live_contact_blocked(page,demo_records,live_server,wire,milliseconds,method):
    open_lab(page,demo_records,live_server)
    page.locator('#yp-practice').check()
    page.locator('#yp-circuit').evaluate('e=>e.open=true')
    page.locator('#yp-wire-'+wire).uncheck()
    if method=='keyboard':
        contact(page,milliseconds)
    else:
        target=page.locator('#yp-hold');target.scroll_into_view_if_needed();box=target.bounding_box();page.mouse.move(box['x']+30,box['y']+30);page.mouse.down();page.clock.run_for(milliseconds);page.mouse.up()
    page.clock.run_for(500)
    assert page.evaluate('YanksonLab.row[2]+YanksonLab.row[3]')==0


def test_UI_02_help_toggle_zoom_and_camera(page,demo_records,live_server):
    open_lab(page,demo_records,live_server)
    tip=page.get_by_role('button',name='Explain Contact pad',exact=True)
    tip.click()
    expect(tip).to_have_attribute('aria-expanded','true')
    tip.click()
    expect(tip).to_have_attribute('aria-expanded','false')
    tip.press('Tab')
    tip.focus()
    expect(tip).to_have_attribute('aria-expanded','false')
    tip.press('Enter')
    expect(tip).to_have_attribute('aria-expanded','true')
    tip.press('Escape')
    expect(tip).to_have_attribute('aria-expanded','false')
    page.locator('#ya-stand canvas').wait_for(state='visible')
    before=page.evaluate('YanksonLab.time')
    page.locator('#ya-camera-starter').click()
    expect(page.locator('#ya-stand')).to_have_attribute('data-camera','starter')
    page.locator('#ya-transparent').click()
    expect(page.locator('#ya-stand')).to_have_attribute('data-transparent','true')
    page.locator('#ya-transparent').click()
    expect(page.locator('#ya-stand')).to_have_attribute('data-transparent','false')
    assert page.evaluate('YanksonLab.time')==before
    page.evaluate("document.documentElement.style.zoom='200%'")
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.locator('#ys-stop').click()
    expect(page.locator('#ys-status')).to_contain_text('PAUSED')


def test_VIS_03_no_webgl_and_reduced_motion(page,demo_records,live_server):
    page.emulate_media(reduced_motion='reduce')
    page.add_init_script("""const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind.startsWith('webgl')?null:original.call(this,kind,...args)}""")
    open_lab(page,demo_records,live_server)
    expect(page.locator('#ya-stand')).to_contain_text('3D unavailable')
    page.locator('#yp-practice').check()
    contact(page,1700)
    page.clock.run_for(4000)
    expect(page.locator('#ys-state')).to_contain_text('RUNNING')
    expect(page.locator('#ya-stand-status')).to_contain_text('starter not requested')


def test_EXP_03_trial_controls_calibration_and_inventory(page,demo_records,live_server):
    open_lab(page,demo_records,live_server)
    page.locator('#yp-parameters').evaluate('e=>e.closest("details").open=true')
    changes={1:.2,2:1.6,3:11,4:3.5,5:650,6:.25,7:.12,8:.03,11:60,20:.6}
    for index,value in changes.items():page.locator('#yp-param-'+str(index)).fill(str(value))
    page.get_by_role('button',name='Apply parameters / new experiment',exact=True).click()
    actual=page.evaluate('YanksonLab.parameters')
    assert all(actual[index]==value for index,value in changes.items())
    page.locator('#yp-parameter-default').click()
    assert page.evaluate('JSON.stringify(YanksonLab.parameters)===JSON.stringify(YanksonEngine.defaults)')
    values={'batteryV':12.8,'wireOhm':.015,'starterOhm':.07,'fuseA':300,'canHighV':3.4,'canLowV':1.4,'terminationOhm':65,'coilOhm':90}
    for name,value in values.items():page.locator('#ya-electrical-'+name).fill(str(value))
    page.locator('#ya-check').click()
    actual=page.evaluate('YanksonCircuit.snapshot().configuration.electrical')
    assert actual==values
    page.locator('#ya-good').click()
    assert page.evaluate('YanksonCircuit.snapshot().computed.current')==pytest.approx(180)
    for field,value in {'question':'EXP-03 test record','change':'baseline - no change','expected':'Locked; no starter','observed':'Locked; starter off','conditions':'Automated synthetic UI, no human microphone'}.items():page.locator('#ye-'+field).fill(value)
    page.locator('#ye-result').select_option('PASS')
    page.locator('#ye-record').click()
    expect(page.locator('#ye-trials')).to_contain_text('EXP-03 test record')
    page.locator('#ye-reference').fill('extensions.xml - automated test evidence')
    page.locator('#ye-attach').click()
    assert len(page.evaluate('YanksonEvidence.snapshot().references'))==1
    with page.expect_download() as download:page.locator('#ys-json').click()
    data=json.loads(Path(download.value.path()).read_text())
    assert len(data['evidence']['trials'])==1
    assert not any(t['inputSource']=='operator-attested human speech' for t in data['evidence']['trials'])
    page.locator('#ye-replay-speed').select_option('.25')
    before=page.evaluate('YanksonLab.time')
    page.locator('#ye-play').click()
    page.clock.run_for(50)
    expect(page.locator('#ye-play-status')).to_contain_text('0.25×')
    assert page.evaluate('YanksonLab.time')==before
    page.locator('#ye-pause').click()
    inventory=page.locator('#ys-workbench button,#ys-workbench input,#ys-workbench select,#ys-workbench textarea,#ys-workbench a[download],#ya-learning a[download]').evaluate_all('''nodes=>nodes.map(e=>({id:e.id,tag:e.tagName,type:e.type||null,label:e.getAttribute('aria-label')||e.labels?.[0]?.textContent?.trim()||e.textContent.trim(),pane:e.closest('#ys-inputs')?'input':'output',disabled:e.disabled||false}))''')
    Path('test-results/corrections/control-inventory.json').write_text(json.dumps({'browser':page.context.browser.version,'userAgent':page.evaluate('navigator.userAgent'),'source':'automated Chrome headless; speech mocked','controls':inventory},indent=2))


def test_UI_03_remaining_simulated_controls_and_master_reset(page,demo_records,live_server):
    import csv
    open_lab(page,demo_records,live_server)
    before=page.evaluate('YanksonLab.time')
    page.locator('#ys-step').click()
    assert page.evaluate('YanksonLab.time')==pytest.approx(before+.01)
    page.locator('#ys-fail').click()
    page.clock.run_for(500)
    assert not page.evaluate('YanksonLab.row[2]')
    assert any(r[11] for r in page.evaluate('YanksonLab.snapshot().rows'))
    page.locator('#ys-reset').click()
    page.locator('#ys-press').click()
    page.locator('#ys-run').click()
    page.clock.run_for(300)
    page.locator('#ys-release').click()
    assert page.evaluate('YanksonLab.row[2]')==1
    page.locator('#ys-voice-wrong').click()
    assert not page.evaluate('YanksonLab.row[14]')
    page.locator('#yp-circuit').evaluate('e=>e.open=true')
    page.locator('#yp-wire-voice').uncheck()
    page.locator('#ys-voice-fresh').click()
    assert page.evaluate('YanksonLab.row[3]')==0
    assert page.evaluate('YanksonLab.snapshot().rawInputs.at(-1)[5]')==1
    assert page.evaluate('YanksonLab.snapshot().inputs.at(-1)[5]')==0
    page.locator('#yp-good').click()
    page.locator('#ys-voice-fresh').click()
    page.clock.run_for(4000)
    expect(page.locator('#ys-state')).to_contain_text('RUNNING')
    with page.expect_download() as download:page.locator('#ys-csv').click()
    rows=list(csv.reader(Path(download.value.path()).read_text().splitlines()))
    assert len(rows)>10 and all(len(row)==28 for row in rows)
    page.locator('#ya-clear').click()
    expect(page.locator('#yp-identity-source')).to_contain_text('none')
    page.locator('#ys-load').fill('40')
    page.locator('#lab-master-reset').click()
    page.wait_for_load_state('domcontentloaded')
    page.locator('#ys-workbench').wait_for()
    expect(page.locator('#ys-load')).to_have_value('0')
    assert page.evaluate('YanksonLab.parameters[3]')==10
