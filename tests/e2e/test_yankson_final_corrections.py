"""Correction-brief regressions. Speech callbacks here are explicitly mocked."""
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_yankson_practical import open_lab, contact, result

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

@pytest.mark.parametrize('wire', ['match', 'contact'])
@pytest.mark.parametrize('route,duration', [('short', 600), ('long', 2000)])
def test_CIR_02_open_paths_block_presets(page, demo_records, live_server, wire, route, duration):
    open_lab(page, demo_records, live_server)
    page.get_by_text('Simulated test events and original supervisor display', exact=True).click()
    page.locator('#yp-circuit > summary').click()
    page.locator('#yp-wire-' + wire).uncheck()
    page.locator('#ys-' + route).click()
    page.clock.run_for(duration)
    assert page.evaluate('YanksonLab.row[2]') == 0
    assert page.evaluate('YanksonLab.row[3]') == 0
    with page.expect_download() as download:
        page.locator('#ys-json').click()
    data = json.loads(Path(download.value.path()).read_text())
    assert not any(row[9] or row[10] for row in data['rows'])

@pytest.mark.parametrize('route,duration,expected', [('short', 600, 'AUTHORIZED'), ('long', 5000, 'RUNNING')])
def test_CIR_02_connected_baseline(page, demo_records, live_server, route, duration, expected):
    open_lab(page, demo_records, live_server)
    page.get_by_text('Simulated test events and original supervisor display', exact=True).click()
    page.locator('#ys-' + route).click()
    page.clock.run_for(duration)
    expect(page.locator('#ys-state')).to_contain_text(expected)


def test_VOI_01_diagnostic_match_never_authorizes(page, demo_records, live_server):
    open_lab(page, demo_records, live_server)
    page.locator('#yp-test-phrase').click()
    expect(page.locator('#ya-signals-panel')).to_be_visible()
    expect(page.locator('#yp-speech')).to_contain_text('LISTENING')
    result(page, 'HEY, START!')
    expect(page.locator('#yp-diagnostic-count')).to_contain_text('MATCH')
    assert page.evaluate('YanksonLab.row[2] + YanksonLab.row[3]') == 0
    page.locator('#yp-test-phrase').click()
    result(page, 'do not hey start')
    expect(page.locator('#yp-diagnostic-count')).to_contain_text('NO MATCH')
    assert page.evaluate('YanksonPractical.metadata().diagnosticMatches') == 1


def test_VOI_04_startup_timeout_and_error_retention(page, demo_records, live_server):
    open_lab(page, demo_records, live_server)
    page.evaluate('() => { SpeechRecognition.prototype.start = function(){}; }')
    page.locator('#yp-test-phrase').click()
    expect(page.locator('#yp-speech')).to_contain_text('STARTING SERVICE')
    page.clock.run_for(8100)
    expect(page.locator('#yp-speech')).to_contain_text('STARTUP_TIMEOUT')
    expect(page.locator('#yp-test-phrase')).to_be_enabled()
    page.locator('#yp-test-phrase').click()
    page.evaluate("recognizers.at(-1).onerror({error:'network'});recognizers.at(-1).onend()")
    expect(page.locator('#yp-speech')).to_contain_text('network failure')


def test_MIC_03_late_permission_stream_is_stopped(page, demo_records, live_server):
    open_lab(page, demo_records, live_server)
    page.evaluate('() => { navigator.mediaDevices.getUserMedia = () => new Promise(resolve => { window.resolveCapture = resolve; }); }')
    page.locator('#ya-mic-start').click()
    expect(page.locator('#ya-mic-wave')).to_be_visible()
    expect(page.locator('#ya-mic-status')).to_contain_text('Requesting microphone')
    page.clock.run_for(5100)
    expect(page.locator('#ya-mic-status')).to_contain_text('unanswered prompt')
    page.locator('#ya-mic-stop').click()
    page.evaluate('window.tracksStopped=0;resolveCapture({getTracks:()=>[{stop(){tracksStopped++}}]})')
    assert page.evaluate('tracksStopped') == 1
    assert page.evaluate('YanksonLab.row[1]') == 0


def test_EXP_01_selected_run_reset_and_replay(page, demo_records, live_server):
    open_lab(page, demo_records, live_server)
    page.locator('#yp-practice').check()
    contact(page, 1700)
    page.clock.run_for(4000)
    expect(page.locator('#ys-state')).to_contain_text('RUNNING')
    with page.expect_download() as download:
        page.locator('#ys-json').click()
    data = json.loads(Path(download.value.path()).read_text())
    assert len(data['columns']) == 28
    assert len(data['inputs']) == len(data['rows'])
    assert data['signalTrace']['supplementary']
    page.locator('#ye-replay-file').set_input_files({'name':'run.json','mimeType':'application/json','buffer':json.dumps(data).encode()})
    expect(page.locator('#ye-replay-status')).to_contain_text('PASS')
    previous = data['evidence']['runId']
    page.locator('#ys-reset').click()
    assert page.evaluate('YanksonEvidence.runId') != previous
    assert page.evaluate('YanksonTeaching.trace().events.length') == 0
    assert page.evaluate('YanksonPractical.metadata().events.length') == 0


def test_CAN_01_received_fault_fields(page, demo_records, live_server):
    open_lab(page, demo_records, live_server)
    page.locator('#ya-tab-signals').click()
    page.locator('#ys-badID').check()
    page.locator('#ys-badDLC').check()
    page.locator('#ys-run').click()
    page.clock.run_for(200)
    expect(page.locator('#ya-can')).to_contain_text('Received ID 0x101')
    expect(page.locator('#ya-can')).to_contain_text('received DLC 4')
    expect(page.locator('#ya-can')).to_contain_text('valid false')


@pytest.mark.parametrize('width', [1440, 1024, 768, 390])
def test_UI_01_workbench_and_keyboard(page, demo_records, live_server, width):
    page.set_viewport_size({'width':width,'height':1000})
    open_lab(page, demo_records, live_server)
    expect(page.locator('#ys-workbench')).to_be_visible()
    assert page.locator('#ys-output-pane input, #ys-output-pane select, #ys-output-pane textarea').count() == 0
    assert page.locator('#ys-inputs #yp-listen, #ys-inputs #ya-mic-start, #ys-inputs #ya-register').count() == 3
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if width >= 1024:
        assert page.locator('#ys-inputs').bounding_box()['x'] < page.locator('#ys-output-pane').bounding_box()['x']
    page.locator('#yp-practice').check()
    contact(page, 300)
    expect(page.locator('#ys-auth')).to_contain_text('permission')
    page.evaluate('YanksonLab.pause()')
    page.clock.resume()
    folder = Path('test-results/corrections/layouts')
    folder.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(folder / f'workbench-{width}.png'))
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    issues = page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
    assert not issues, issues
