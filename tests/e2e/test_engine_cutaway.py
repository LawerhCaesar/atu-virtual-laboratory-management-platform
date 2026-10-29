from datetime import datetime, timezone
import pytest
from playwright.sync_api import expect
from tests.e2e.test_engine_demo import open_engine,start_engine

pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]


@pytest.mark.parametrize('width',[1280,390])
def test_3d_cutaway_tracks_sample_and_honours_pause(page,demo_records,live_server,width):
    page.set_viewport_size({'width':width,'height':900})
    page.emulate_media(reduced_motion='reduce' if width==390 else 'no-preference')
    open_engine(page,demo_records,live_server)
    expect(page.locator('#cutaway-status')).to_contain_text('3D ready',timeout=20000)
    if width==390:expect(page.get_by_label('Animate motion',exact=True)).not_to_be_checked();page.get_by_label('Animate motion',exact=True).check()
    # Freeze wall-clock progression between actions; software WebGL on CI can
    # otherwise trigger the app's deliberate >0.5 s stall auto-pause.
    clock_start=datetime(2026,1,1,tzinfo=timezone.utc)
    page.clock.install(time=clock_start);page.clock.pause_at(clock_start)
    start_engine(page)
    expect(page.locator('[data-cutaway-signal="state"]')).to_have_text('RUN')
    page.get_by_role('button',name='Pause',exact=True).click();page.clock.run_for(100)
    phase=page.locator('#cutaway-viewport').get_attribute('data-phase');assert float(phase)>0
    page.clock.run_for(500);assert page.locator('#cutaway-viewport').get_attribute('data-phase')==phase
    page.get_by_role('button',name='Emergency stop',exact=True).click()
    expect(page.locator('[data-cutaway-signal="state"]')).to_have_text('RUN')
    page.get_by_role('button',name='Step 0.05 s',exact=True).click()
    expect(page.locator('[data-cutaway-signal="state"]')).to_have_text('SHUTDOWN')
    expect(page.locator('[data-cutaway-signal="fan"]')).to_have_text('0.00 %')
    page.get_by_role('button',name='Close 3D view',exact=True).click()
    expect(page.locator('#cutaway-workspace')).to_be_hidden()
    if width==1280:
        page.get_by_role('button',name='Load 3D engine',exact=True).click()
        expect(page.locator('#cutaway-status')).to_contain_text('3D ready')
        page.locator('#cutaway-viewport canvas').evaluate("canvas => canvas.getContext('webgl2').getExtension('WEBGL_lose_context').loseContext()")
        expect(page.locator('#cutaway-status')).to_contain_text('graphics context was lost')
        expect(page.locator('#engine-schematic')).to_be_visible()


def test_3d_failure_does_not_break_calculations(page,demo_records,live_server):
    page.route('**/cutaway.bundle.mjs',lambda route:route.abort())
    open_engine(page,demo_records,live_server)
    expect(page.locator('#cutaway-status')).to_contain_text('3D is unavailable')
    page.get_by_role('button',name='Cooling',exact=True).click()
    expect(page.locator('[data-signal="FanDuty"]')).to_have_text('28.6 %')
    expect(page.locator('#engine-schematic')).to_be_visible()
