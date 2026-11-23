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
