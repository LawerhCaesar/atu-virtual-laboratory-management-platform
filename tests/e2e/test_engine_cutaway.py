import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.e2e.test_engine_demo import open_engine

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.mark.parametrize("width", [1280, 390])
def test_3d_cutaway_tracks_simulation_and_remains_accessible(page, demo_records, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.emulate_media(reduced_motion="reduce" if width == 390 else "no-preference")
    open_engine(page, demo_records, live_server)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    assert not page.locator("#cutaway-viewport canvas").count()
    page.get_by_role("button", name="Load 3D engine", exact=True).click()
    expect(page.locator("#cutaway-status")).to_contain_text("3D ready")
    expect(page.get_by_role("img", name="Interactive generic four-cylinder", exact=False)).to_be_visible()
    if width == 390:
        expect(page.get_by_label("Animate motion", exact=True)).not_to_be_checked()
        expect(page.get_by_label("Illustrative flow effects", exact=True)).not_to_be_checked()
        page.get_by_label("Animate motion", exact=True).check()
    page.clock.install()
    page.get_by_label("Ignition switch", exact=True).check()
    page.get_by_label("Fingerprint authorised", exact=True).check()
    page.get_by_role("button", name="Voice/manual start request", exact=True).click()
    page.get_by_role("button", name="Run", exact=True).click()
    page.clock.run_for(2800)
    expect(page.locator("#engine-state")).to_have_text("RUN")
    expect(page.locator('[data-cutaway-signal="state"]')).to_have_text("RUN")
    page.get_by_role("button", name="Pause", exact=True).click()
    page.clock.run_for(100)
    phase = page.locator("#cutaway-viewport").get_attribute("data-phase")
    fan_phase = page.locator("#cutaway-viewport").get_attribute("data-fan-phase")
    assert float(phase) > 0
    page.clock.run_for(1000)
    assert page.locator("#cutaway-viewport").get_attribute("data-phase") == phase
    assert page.locator("#cutaway-viewport").get_attribute("data-fan-phase") == fan_phase
    page.get_by_label("Illustrative flow effects", exact=True).uncheck()
    page.clock.run_for(100)
    expect(page.locator("#cutaway-viewport")).to_have_attribute("data-effects", "off")
    page.get_by_label("Illustrative flow effects", exact=True).check()
    virtual_time = page.locator("#engine-time").inner_text()
    page.get_by_label("Visual playback scale", exact=True).select_option("0.1")
    page.get_by_role("button", name="Rotate left", exact=True).click()
    page.get_by_role("button", name="Zoom in", exact=True).click()
    page.get_by_label("Transparent casing", exact=True).uncheck()
    page.clock.run_for(100)
    expect(page.locator("#engine-time")).to_have_text(virtual_time)
    assert page.locator("#cutaway-viewport").get_attribute("data-phase") == phase
    page.get_by_label("Demonstration preset").select_option(label="ECT sensor disagreement")
    page.get_by_role("button", name="Load preset", exact=True).click()
    expect(page.locator('[data-cutaway-signal="fan"]')).to_have_text("100.00 %")
    page.clock.run_for(100)
    destination = Path("test-results/engine-cutaway")
    destination.mkdir(parents=True, exist_ok=True)
    page.locator("#engine-cutaway").screenshot(path=str(destination / f"cutaway-{width}.png"), style=".engine-toolbar {position:static !important}")
    page.get_by_role("button", name="Emergency stop", exact=True).click()
    expect(page.locator('[data-cutaway-signal="state"]')).to_have_text("SHUTDOWN")
    expect(page.locator('[data-cutaway-signal="fan"]')).to_have_text("0.00 %")
    page.clock.run_for(1000)
    assert page.locator("#cutaway-viewport").get_attribute("data-phase") == phase
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.add_script_tag(path="node_modules/axe-core/axe.min.js")
    result = page.evaluate("async () => await axe.run(document.querySelector('#engine-cutaway'), {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}})")
    assert not result["violations"], json.dumps(result["violations"], indent=2)
    page.get_by_role("button", name="Reset", exact=True).click()
    page.clock.run_for(100)
    assert float(page.locator("#cutaway-viewport").get_attribute("data-phase")) == 0
    assert float(page.locator("#cutaway-viewport").get_attribute("data-fan-phase")) == 0
    if width == 1280:
        page.get_by_label("Ignition switch", exact=True).check()
        page.get_by_label("Fingerprint authorised", exact=True).check()
        page.get_by_role("button", name="Voice/manual start request", exact=True).click()
        page.get_by_role("button", name="Run", exact=True).click()
        page.clock.run_for(2800)
        page.get_by_role("button", name="Emergency stop", exact=True).click()
        page.clock.run_for(100)
        stopped = page.locator("#cutaway-viewport").get_attribute("data-phase")
        stopped_fan = page.locator("#cutaway-viewport").get_attribute("data-fan-phase")
        page.clock.run_for(1000)
        assert page.locator("#cutaway-viewport").get_attribute("data-phase") == stopped
        assert page.locator("#cutaway-viewport").get_attribute("data-fan-phase") == stopped_fan
        page.get_by_role("button", name="Pause", exact=True).click()
    if width == 1280:
        page.emulate_media(reduced_motion="reduce")
        expect(page.get_by_label("Animate motion", exact=True)).not_to_be_checked()
        expect(page.get_by_label("Illustrative flow effects", exact=True)).not_to_be_checked()
    page.get_by_role("button", name="Close 3D view", exact=True).click()
    expect(page.locator("#cutaway-workspace")).to_be_hidden()
    assert not page.locator("#cutaway-viewport canvas").count()
    if width == 1280:
        page.get_by_role("button", name="Load 3D engine", exact=True).click()
        expect(page.locator("#cutaway-status")).to_contain_text("3D ready")
        page.locator("#cutaway-viewport canvas").evaluate("canvas => canvas.getContext('webgl2').getExtension('WEBGL_lose_context').loseContext()")
        expect(page.locator("#cutaway-status")).to_contain_text("graphics context was lost")
        expect(page.locator("#cutaway-workspace")).to_be_hidden()
    assert not errors


def test_3d_failure_does_not_break_calculations(page, demo_records, live_server):
    open_engine(page, demo_records, live_server)
    page.route("**/cutaway.bundle.mjs", lambda route: route.abort())
    page.get_by_role("button", name="Load 3D engine", exact=True).click()
    expect(page.locator("#cutaway-status")).to_contain_text("3D is unavailable")
    expect(page.get_by_role("button", name="Load 3D engine", exact=True)).to_be_enabled()
    page.get_by_role("button", name="Cooling", exact=True).click()
    expect(page.locator('[data-signal="FanDuty"]')).to_have_text("28.57 %")
    page.get_by_role("button", name="Reset", exact=True).click()
    expect(page.locator("#engine-state")).to_have_text("OFF")
