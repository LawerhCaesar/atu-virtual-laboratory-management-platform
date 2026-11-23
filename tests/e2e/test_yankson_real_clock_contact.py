"""Normally advancing browser clock and automated mouse; not human speech evidence."""
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

@pytest.mark.parametrize('width',[1440,390])
def test_mouse_contact_with_unmocked_clock(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':950})
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address or index number',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.goto(live_server.url+'/virtual-lab/ice/authenticated-engine-starting/')
    page.locator('#tour-close').click()
    page.locator('#ye-record').wait_for(state='attached')
    page.locator('#yp-practice').check()
    records=[]
    try:
        for attempt in range(3):
            page.locator('#ys-reset').click()
            expect(page.locator('#ys-identity-guidance')).to_contain_text('Device verification is not required')
            pad=page.locator('#yp-hold');pad.scroll_into_view_if_needed();b=pad.bounding_box()
            page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2)
            page.mouse.down();page.wait_for_timeout(500);page.mouse.up()
            observed=page.evaluate('({row:YanksonLab.row, debt:YanksonLab.debt, practical:YanksonPractical.metadata(),classification:document.querySelector("#yp-contact-classification").textContent,reason:document.querySelector("#yp-reason").textContent})')
            records.append(observed)
            assert observed['row'][2]==1,observed
            assert observed['practical']['permissionSecondsRemaining']>0,observed
            expect(page.locator('#yp-contact-classification')).to_contain_text('voice permission granted')
    finally:
        folder=Path('test-results/yankson-contact-investigation');folder.mkdir(parents=True,exist_ok=True)
        (folder/f'real-clock-{width}.json').write_text(json.dumps({'inputSource':'Automated mouse events with ordinary wall time; no speech callback or synthetic command','viewportWidth':width,'attempts':records},indent=2))


def test_visible_voice_diagnostic_before_contact(page,demo_records,live_server):
    from test_yankson_ui_follow_up import basic_lab
    from test_yankson_practical import result
    basic_lab(page,demo_records,live_server)
    expect(page.get_by_role('button',name='Test spoken command',exact=True)).to_be_visible()
    assert not page.locator('#ys-input-advanced').evaluate('e=>e.open')
    page.locator('#yp-test-phrase').click()
    expect(page.locator('#yp-speech')).to_contain_text('LISTENING')
    result(page,'start')
    expect(page.locator('#yp-phrase-check')).to_be_visible()
    expect(page.locator('#yp-phrase-check')).to_contain_text('MATCH')
    expect(page.locator('#yp-transcript')).to_contain_text('Recognized: start')
    assert not page.evaluate('YanksonLab.row[2]||YanksonLab.row[3]')
    assert not page.locator('#ys-output-advanced').evaluate('e=>e.open')
    page.locator('#yp-test-phrase').click()
    page.evaluate("recognizers.at(-1).onerror({error:'network'});recognizers.at(-1).onend()")
    expect(page.locator('#yp-speech')).to_contain_text('network')
    expect(page.locator('#yp-phrase-check')).to_contain_text('No final matching transcript')
    assert not page.evaluate('YanksonLab.row[2]||YanksonLab.row[3]')
