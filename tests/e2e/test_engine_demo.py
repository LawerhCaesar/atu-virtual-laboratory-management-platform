import csv
import io
import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def open_engine(page, demo_records, live_server):
    page.goto(live_server.url + "/accounts/login/")
    page.get_by_label("Email address", exact=True).fill(demo_records["student"].email)
    page.get_by_label("Password", exact=True).fill("DemoPass!742")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page).to_have_url(live_server.url + "/dashboard/")
    page.get_by_role("link", name="Engine live data", exact=True).click()
    expect(page.get_by_role("heading", name="Engine Live-Data Demonstration", exact=True)).to_be_visible()
    expect(page.locator("#engine-tabs button")).to_have_count(5)


def test_engine_input_caps_pause_emergency_and_csv(page, demo_records, live_server):
    open_engine(page, demo_records, live_server)
    page.clock.install()
    expect(page.locator("#engine-state")).to_have_text("OFF")
    page.get_by_label("Battery voltage (V)", exact=True).fill("16")
    page.get_by_label("Battery voltage (V)", exact=True).press("Tab")
    expect(page.locator("#accepted-BatteryVoltage")).to_contain_text("14.90 V")
    page.get_by_role("button", name="Load preset", exact=True).click()
    expect(page.locator("#engine-state")).to_have_text("OFF")
    page.get_by_label("Ignition switch", exact=True).check()
    page.get_by_label("Fingerprint authorised", exact=True).check()
    page.get_by_role("button", name="Voice/manual start request", exact=True).click()
    page.get_by_role("button", name="Run", exact=True).click()
    page.clock.run_for(2400)
    expect(page.locator("#engine-state")).to_have_text("RUN")
    page.get_by_role("button", name="Pause", exact=True).click()
    frozen = page.locator("#engine-time").inner_text()
    page.clock.run_for(5000)
    expect(page.locator("#engine-time")).to_have_text(frozen)
    page.get_by_role("button", name="Fuel and injection", exact=True).click()
    expect(page.locator('[data-signal="InjectorPW"]')).to_have_text("1.6790 ms")
    page.get_by_label("Oxygen-sensor voltage (V)", exact=True).fill("0.10")
    page.get_by_label("Oxygen-sensor voltage (V)", exact=True).press("Tab")
    expect(page.locator('[data-signal="STFT"]')).to_have_text("14.70 %")
    expect(page.locator('[data-signal="InjectorPW"]')).to_have_text("1.9258 ms")
    page.get_by_role("button", name="Cooling", exact=True).click()
    expect(page.locator('[data-signal="FanDuty"]')).to_have_text("28.57 %")
    expect(page.locator('[data-signal="WaterPumpDuty"]')).to_have_text("70.00 %")
    assert page.locator("#engine-chart polyline").first.get_attribute("points")
    assert not page.locator("#engine-values input").count()
    page.get_by_label("Demonstration preset").select_option(label="ECT sensor disagreement")
    page.get_by_role("button", name="Load preset", exact=True).click()
    expect(page.locator('[data-signal="FanDuty"]')).to_have_text("100.00 %")
    expect(page.locator('[data-signal="WaterPumpDuty"]')).to_have_text("100.00 %")
    page.get_by_role("button", name="Emergency stop", exact=True).click()
    expect(page.locator("#engine-state")).to_have_text("SHUTDOWN")
    expect(page.locator('[data-signal="FanDuty"]')).to_have_text("0.00 %")
    expect(page.locator('[data-signal="WaterPumpDuty"]')).to_have_text("0.00 %")
    expect(page.locator("#engine-emergency")).to_be_disabled()
    with page.expect_download() as download:
        page.get_by_role("button", name="Export CSV", exact=True).click()
    rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text())))
    assert rows[-1]["EmergencyStop"] == "1"
    assert rows[-1]["EngineState"] == "4"
    assert rows[-1]["WaterPumpDuty"] == "0"
    page.get_by_role("button", name="Reset", exact=True).click()
    expect(page.locator("#engine-state")).to_have_text("OFF")
    expect(page.locator("#engine-time")).to_have_text("0.00")
    expect(page.locator("#engine-emergency")).to_be_enabled()
    expect(page.locator("#engine-chart-status")).to_contain_text("0 recorded")
    page.get_by_role("link", name="Back to dashboard").click()
    expect(page).to_have_url(live_server.url + "/dashboard/")


@pytest.mark.parametrize("width", [1280, 390])
def test_engine_views_are_accessible_and_responsive(page, demo_records, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    open_engine(page, demo_records, live_server)
    if width == 390:
        page.get_by_role("button", name="Hide input controls", exact=True).click()
    page.add_script_tag(path="node_modules/axe-core/axe.min.js")
    for view in ["Overview", "Fuel and injection", "Idle and ignition", "Cooling", "Start and run"]:
        page.get_by_role("button", name=view, exact=True).click()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        results = page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}})")
        assert not results["violations"], json.dumps(results["violations"], indent=2)
        destination = Path("test-results/engine-live-data")
        destination.mkdir(parents=True, exist_ok=True)
        (destination / f"axe-{width}-{view.split()[0].lower()}.json").write_text(json.dumps(results, indent=2))
        if view in ["Overview", "Cooling"]:
            if view == "Cooling":
                page.locator("#engine-system").scroll_into_view_if_needed()
            page.screenshot(path=str(destination / f"{width}-{view.lower()}.png"), full_page=False)
