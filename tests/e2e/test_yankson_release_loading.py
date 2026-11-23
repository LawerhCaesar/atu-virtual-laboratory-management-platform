"""Cold/reload release identity; no human speech is simulated as acceptance evidence."""
import pytest
from playwright.sync_api import expect
from test_yankson_ui_follow_up import basic_lab
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]


def test_release_modules_and_layout_stay_current_after_reload(page,demo_records,live_server):
    requested=[]
    page.on('request',lambda request:requested.append(request.url))
    basic_lab(page,demo_records,live_server)
    page.clock.resume()
    for attempt in range(2):
        page.locator('#ye-record').wait_for(state='attached')
        expect(page.locator('#ys-say-title')).to_have_text('3 · Say “Start”')
        expect(page.get_by_role('button',name='Test spoken command',exact=True)).to_be_visible()
        assert page.locator('#yp-workbench').is_hidden()
        hashes=page.evaluate('YanksonBuild.sha256')
        for name in ['workbench.mjs','layout.mjs','microphone.mjs','guide.mjs','electrical.mjs','experiments.mjs','learning-guide.json']:
            assert any('/'+name+'?v='+hashes[name] in url for url in requested), (name,requested)
        guide=page.locator('a[download="Authenticated-Engine-Starting-Learning-Guide.pdf"]')
        assert guide.get_attribute('href').endswith('?v='+hashes['authenticated-starting-learning-guide.pdf'])
        page.wait_for_timeout(1500)
        expect(page.get_by_role('button',name='Test spoken command',exact=True)).to_be_visible()
        expect(page.locator('#ys-say-title')).to_have_text('3 · Say “Start”')
        assert not page.evaluate('YanksonLab.row[2]')
        if not attempt:
            page.reload()
            if page.locator('#tour-close').is_visible():page.locator('#tour-close').click()


def test_workspace_boot_does_not_wait_for_optional_guide(page,demo_records,live_server):
    from pathlib import Path
    held=[]
    page.route('**/learning-guide.json?*',lambda route:held.append(route))
    basic_lab(page,demo_records,live_server)
    expect(page.locator('#ys-layout-source')).to_have_attribute('data-ready','true')
    expect(page.get_by_role('button',name='Test spoken command',exact=True)).to_be_visible()
    expect(page.locator('#yp-workbench')).to_be_hidden()
    assert held
    for route in held:route.fulfill(status=200,content_type='application/json',body=Path('static/js/yankson/learning-guide.json').read_bytes())
    expect(page.locator('#ya-learning')).to_contain_text('Controller parameter glossary')


def test_failed_boot_reports_error_without_legacy_fallback(page,demo_records,live_server):
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address or index number',exact=True).fill(demo_records['student'].email)
    page.get_by_label('Password',exact=True).fill('DemoPass!742')
    page.get_by_role('button',name='Sign in',exact=True).click()
    page.route('**/workbench.mjs?*',lambda route:route.abort())
    page.goto(live_server.url+'/virtual-lab/ice/authenticated-engine-starting/')
    expect(page.locator('#ys-layout-loading')).to_have_attribute('role','alert')
    expect(page.locator('#ys-layout-loading')).to_contain_text('could not load')
    expect(page.locator('#ys-layout-source')).to_be_hidden()
    expect(page.locator('#yp-workbench')).to_be_hidden()
