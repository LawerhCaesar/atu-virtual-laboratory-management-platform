"""Acceptance artifacts for the owner's 21 November handover; no human-speech claim."""
from contextlib import contextmanager
from pathlib import Path
import json
import pytest
from playwright.sync_api import expect
from test_yankson_ui_follow_up import basic_lab
from test_yankson_practical import contact, result

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]
ARTIFACTS = Path('test-results/yankson-test-results-follow-up')


@contextmanager
def acceptance(page, case, source, expected):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    item = {'case': case, 'inputSource': source, 'expected': expected,
            'configuration': page.evaluate('({parameters:YanksonLab.parameters, circuit:YanksonCircuit.snapshot().configuration, viewport:[innerWidth,innerHeight], phrase:document.querySelector("#yp-command").value, language:document.querySelector("#yp-language").value, identity:document.querySelector("#yp-identity-source").textContent, userAgent:navigator.userAgent})'),
            'observed': {}, 'status': 'NOT RUN'}
    try:
        yield item['observed']
    except Exception as error:
        item['status'] = 'FAIL'
        item['error'] = str(error)
        raise
    else:
        item['status'] = 'PASS'
    finally:
        (ARTIFACTS / (case + '.json')).write_text(json.dumps(item, indent=2))


def test_UI_01_waveform_revealed_and_layout_screenshots(page, demo_records, live_server):
    basic_lab(page, demo_records, live_server, 1366)
    page.set_viewport_size({'width': 1366, 'height': 768})
    with acceptance(page, 'UI-01-software', 'Automated Chrome; pending getUserMedia stub, no captured human audio', 'Microphone action opens waveform and brings it into viewport; basic/expanded layouts retain one copy of each control') as observed:
        page.evaluate('() => { navigator.mediaDevices.getUserMedia=()=>new Promise(()=>{}); }')
        page.locator('#ya-microphone details').evaluate('e=>e.open=false')
        page.evaluate('scrollTo(0,0)')
        page.locator('#ya-mic-start').click()
        expect(page.locator('#ya-mic-status')).to_contain_text('Requesting microphone')
        box = page.locator('#ya-mic-wave').bounding_box()
        assert box['y'] >= 0 and box['y'] + box['height'] <= 768
        assert page.locator('#ya-microphone details').evaluate('e=>e.open')
        assert not page.locator('#ys-input-advanced').evaluate('e=>e.open')
        for selector in ['#yp-hold', '#yp-listen', '#yp-contact-timer']:
            assert page.locator(selector).count() == 1
        observed.update(waveformBounds=box, waveformVisible=True, duplicateBasicControls=False)
        page.evaluate('YanksonLab.pause()')
        page.clock.resume()
        page.screenshot(path=str(ARTIFACTS / 'basic-laptop.png'))
        page.locator('#ya-mic-stop').click()
        page.locator('#ys-input-advanced').evaluate('e=>e.open=true')
        page.locator('#ys-output-advanced').evaluate('e=>e.open=true')
        page.screenshot(path=str(ARTIFACTS / 'expanded-laptop.png'), full_page=True)
        page.locator('#ys-input-advanced').scroll_into_view_if_needed()
        page.screenshot(path=str(ARTIFACTS / 'expanded-input-controls.png'))


def test_TOUCH_01_mouse_duration_matches_export(page, demo_records, live_server):
    basic_lab(page, demo_records, live_server)
    with acceptance(page, 'TOUCH-01-software', 'Automated mouse pointer events in Chrome with controlled 1x browser clock; not an owner-operated hold', 'Timer advances, freezes on mouse release and matches exported measured event; sampled model timing remains separate') as observed:
        page.locator('#yp-practice').check()
        pad = page.locator('#yp-hold')
        pad.scroll_into_view_if_needed()
        box = pad.bounding_box()
        page.mouse.move(box['x'] + 25, box['y'] + 25)
        page.mouse.down()
        page.clock.run_for(350)
        live = float(page.locator('#yp-contact-timer').inner_text().split()[0])
        assert .32 <= live <= .35
        page.mouse.up()
        frozen = page.locator('#yp-contact-timer').inner_text()
        event = page.evaluate('YanksonPractical.metadata().events.filter(e=>e.type==="measured contact").at(-1)')
        assert event['source'] == 'mouse press'
        assert float(frozen.split()[0]) == pytest.approx(event['durationSeconds'], abs=.005)
        assert event['timing']['measuredMinusModelContactSeconds'] == pytest.approx(event['durationSeconds'] - event['modelDurationSeconds'])
        page.clock.run_for(250)
        expect(page.locator('#yp-contact-timer')).to_have_text(frozen)
        observed.update(displayed=frozen, exportedEvent=event)


def test_TOUCH_02_native_boundary_edges(page, demo_records, live_server):
    basic_lab(page, demo_records, live_server)
    with acceptance(page, 'TOUCH-02-native', 'Deterministic native-engine input samples; separate from measured screen-pad timing', 'Release-edge durations .14/.15/1.49/1.50/1.51 s yield rejected/short/short/neither/long; held sample at 1.50 s fires long once') as observed:
        cases = page.evaluate('''() => {
          const E=YanksonEngine;
          return [14,15,149,150,151].map(ticks=>{
            const engine=E.createEngine(), u=E.defaultInput(), rows=[];
            rows.push(engine.step(u));
            for(let k=0;k<ticks;k++){u[0]=1;u[1]=k===0?1:0;rows.push(engine.step(u));}
            u[0]=0;u[1]=0;const released=engine.step(u);rows.push(released);
            const held=E.createEngine(),v=E.defaultInput(),heldRows=[held.step(v)];
            for(let k=0;k<=ticks;k++){v[0]=1;v[1]=k===0?1:0;heldRows.push(held.step(v));}
            return {ticks,releaseDuration:released[12],shortEvents:rows.reduce((s,r)=>s+r[9],0),longEvents:rows.reduce((s,r)=>s+r[10],0),requests:rows.reduce((s,r)=>s+r[13],0),heldLongEvents:heldRows.reduce((s,r)=>s+r[10],0)};
          });
        }''')
        assert [(d['shortEvents'], d['longEvents']) for d in cases] == [(0,0),(1,0),(1,0),(0,0),(0,1)]
        assert cases[3]['heldLongEvents'] == 1
        assert cases[4]['heldLongEvents'] == 1
        observed.update(cases=cases, boundaryCaveat='Release exactly at 1.50 s differs from a held sample at 1.50 s in the unchanged native controller. This is edge-order semantics, not rounding. No new MATLAB parity claim.')


def test_RESET_01_current_record_and_reported_history(page, demo_records, live_server):
    basic_lab(page, demo_records, live_server)
    with acceptance(page, 'RESET-01', 'Automated short mouse-equivalent keyboard contact; owner-supplied history summary', 'Reset clears measured timer/progress/permission/events; new run ID and one current row; saved prior record and reported evidence remain separate') as observed:
        page.locator('#yp-practice').check()
        contact(page, 350)
        prior = page.evaluate('({evidence:YanksonEvidence.snapshot(), practical:YanksonPractical.metadata()})')
        assert prior['practical']['events']
        page.locator('#ys-reset').click()
        current = page.evaluate('({run:YanksonLab.snapshot(),evidence:YanksonEvidence.snapshot(),practical:YanksonPractical.metadata(),teaching:YanksonTeaching.trace()})')
        expect(page.locator('#yp-contact-timer')).to_have_text('0.00 s')
        expect(page.locator('#yp-contact-classification')).to_have_text('Not held yet.')
        assert page.locator('#yp-progress').evaluate('e=>e.value') == 0
        assert current['practical']['permissionSecondsRemaining'] == 0
        assert current['practical']['events'] == []
        assert current['teaching']['events'] == []
        assert current['evidence']['trials'] == []
        assert len(current['run']['rows']) == 1
        assert prior['evidence']['runId'] != current['evidence']['runId']
        history = current['evidence']['followUpReportedEvidence']
        assert history == prior['evidence']['followUpReportedEvidence']
        assert history['november17']['voiceAcceptedModelTime'] == 10.34
        assert 'NOT COMPLETED' in history['november21']['voiceRetest']
        observed.update(priorRun=prior['evidence']['runId'], newRun=current['evidence']['runId'], priorEventCount=len(prior['practical']['events']), currentEventCount=0, currentRows=1, historyUnchanged=True)
        (ARTIFACTS / 'reset-saved-prior.json').write_text(json.dumps(prior, indent=2))
        (ARTIFACTS / 'reset-current.json').write_text(json.dumps(current, indent=2))


def test_VOICE_02_unavailable_expired_nonmatching_and_after_direct(page, demo_records, live_server):
    basic_lab(page, demo_records, live_server)
    with acceptance(page, 'VOICE-02-software', 'Automated Chrome with explicitly mocked recognition callback, no human speech', 'No permission, expired permission and wrong phrase cannot start; after direct start, nearby Listen guidance calls for reset and fresh short contact') as observed:
        page.locator('#yp-listen').click()
        expect(page.locator('#yp-listen-help')).to_contain_text('No current voice permission')
        page.locator('#yp-practice').check()
        contact(page, 350)
        page.clock.run_for(10500)
        page.locator('#yp-listen').click()
        expect(page.locator('#yp-listen-help')).to_contain_text('No current voice permission')
        assert not page.evaluate('YanksonLab.row[3]')
        contact(page, 350)
        page.locator('#yp-listen').click()
        result(page, 'do not start')
        assert not page.evaluate('YanksonLab.snapshot().rows.some(r=>r[14]||r[3])')
        expect(page.locator('#yp-reason')).to_contain_text('Wrong command')
        page.locator('#ys-reset').click()
        contact(page, 5000)
        page.locator('#yp-listen').click()
        expect(page.locator('#yp-listen-help')).to_contain_text('Reset experiment')
        expect(page.locator('#yp-start-source')).to_contain_text('long contact')
        observed.update(wrongPhraseAccepted=False, noPermissionStarted=False, expiredPermissionStarted=False, afterDirectGuidance=page.locator('#yp-listen-help').inner_text(), actualSource=page.locator('#yp-start-source').inner_text())


def test_REG_01_interlocks_and_original_crank_deadline(page, demo_records, live_server):
    basic_lab(page, demo_records, live_server)
    with acceptance(page, 'REG-01', 'Automated synthetic contact and fault toggles; unchanged controller', 'Open identity/contact and invalid CAN block starting; CAN loss during cranking retains original 3 s deadline; emergency stop/reset clear outputs') as observed:
        page.evaluate("document.querySelectorAll('#ys-workbench details.ys-input-group').forEach(e=>e.open=true)")
        page.locator('#yp-circuit').evaluate('e=>e.open=true')
        blocked = []
        for wire in ['match', 'contact']:
            page.locator('#yp-wire-' + wire).uncheck()
            for milliseconds in [350, 2000]:
                page.locator('#ys-reset').click()
                page.locator('#yp-practice').check()
                contact(page, milliseconds)
                page.clock.run_for(300)
                assert not page.evaluate('YanksonLab.snapshot().rows.some(r=>r[2]||r[3])')
                blocked.append({'wire':wire, 'holdMs':milliseconds, 'authorizedOrStarted':False})
            page.locator('#yp-wire-' + wire).check()
        page.locator('#ys-reset').click()
        page.locator('#yp-practice').check()
        page.locator('#ys-badID').check()
        contact(page, 2000)
        assert not page.evaluate('YanksonLab.snapshot().rows.some(r=>r[3])')
        page.locator('#ys-reset').click()
        page.locator('#yp-practice').check()
        page.locator('#ys-ignitionAllowed').uncheck()
        contact(page, 1800)
        assert page.evaluate('YanksonLab.row[1]') == 2
        original = page.evaluate('YanksonLab.row[23]')
        page.locator('#ys-CANdrop').check()
        page.clock.run_for(3500)
        data = page.evaluate('YanksonLab.snapshot()')
        fault = next(r for r in data['rows'] if r[1] == 4)
        assert fault[6] == 21
        assert fault[0] - original == pytest.approx(3, abs=.011)
        assert fault[3] == fault[7] == 0
        page.locator('#ys-stop').click()
        assert not page.evaluate('YanksonLab.row[3]||YanksonLab.row[7]')
        page.locator('#ys-reset').click()
        assert page.evaluate('YanksonLab.row[1]') == 0
        observed.update(disconnectedCases=blocked, invalidCANStarted=False, originalCrankStart=original, faultTime=fault[0], deadlineSeconds=fault[0]-original, starterOff=True, runSupplyOff=True, resetState='LOCKED')


def test_UI_02_layout_and_visible_decision_record(page, demo_records, live_server):
    basic_lab(page, demo_records, live_server)
    with acceptance(page, 'UI-02', 'Automated Chrome layout, keyboard and mouse; isolated demo account', 'Narrow pane and mobile layout remain unclipped; collapse/show retains outputs; Listen reveals latest decision; only layout preference persists') as observed:
        divider = page.locator('#ys-input-divider')
        divider.focus()
        divider.press('Home')
        assert divider.get_attribute('aria-valuenow') == '280'
        width_at_home = page.locator('#ys-inputs').bounding_box()['width']
        assert width_at_home <= 280
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.locator('#ys-input-toggle').click()
        expect(page.locator('#ys-inputs')).to_be_hidden()
        expect(page.locator('#ys-output-pane')).to_be_visible()
        page.locator('#ys-input-toggle').click()
        divider.focus()
        divider.press('ArrowRight')
        assert divider.get_attribute('aria-valuenow') == '290'
        for width in [1366,390]:
            page.set_viewport_size({'width':width,'height':768})
            page.evaluate('scrollTo(0,document.body.scrollHeight)')
            page.locator('#yp-listen').click()
            box = page.locator('#ys-live-feedback').bounding_box()
            assert box['y'] >= -1 and box['y']+box['height'] <= 768
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.locator('#ys-input-toggle').click()
            expect(page.locator('#ys-inputs')).to_be_hidden()
            page.locator('#ys-input-toggle').click()
            expect(page.locator('#yp-hold')).to_be_visible()
        preference=page.evaluate("JSON.parse(localStorage.getItem('atu:yankson:layout:v1:'+document.querySelector('#yp-workbench').dataset.user))")
        assert set(preference)=={'width','collapsed'}
        observed.update(desktopMinimumWidth=width_at_home,keyboardWidthAfterArrow=290,viewportWidthsChecked=[1366,390],noHorizontalOverflow=True,decisionBroughtIntoView=True,savedPreference=preference)
