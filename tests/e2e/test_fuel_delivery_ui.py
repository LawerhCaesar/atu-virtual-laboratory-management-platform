import csv
import io
import json
import re
from pathlib import Path

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def open_fuel(page, demo_records, live_server):
    page.goto(live_server.url + "/accounts/login/")
    page.get_by_label("Email address", exact=True).fill(demo_records["student"].email)
    page.get_by_label("Password", exact=True).fill("DemoPass!742")
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.get_by_role("link", name="Virtual laboratory", exact=True).click()
    page.get_by_role("link", name="Enter ICE environment", exact=True).click()
    expect(page.locator(".lab-model-grid article")).to_have_count(1)
    expect(page.get_by_role("link", name="Open Engine Live Data Demonstration", exact=True)).to_have_count(0)
    page.get_by_role("link", name="Open Fuel Delivery Optimisation", exact=True).click()
    expect(page.get_by_role("heading", name="Fuel Delivery Optimisation", exact=True)).to_be_visible()
    expect(page.locator("#fuel-kpis [data-fuel-output]")).to_have_count(14)


def output(page, key):
    return page.locator(f'#fuel-kpis [data-fuel-output="{key}"]')


def test_3d_explorer_matches_results_and_fallback(page, demo_records, live_server):
    open_fuel(page, demo_records, live_server)
    expect(page.locator("#fuel-3d-canvas canvas")).to_be_visible(timeout=20000)
    expect(page.locator("#fuel-3d-flow")).to_have_text("1.701 g/s")
    expect(page.locator("#fuel-3d-pulse")).to_have_text("8.471 ms")
    page.get_by_label("Air flow (g/s)", exact=True).fill("50")
    expect(page.locator("#fuel-3d-flow")).to_have_text("3.401 g/s")
    expect(page.locator("#fuel-3d-pulse")).to_have_text(output(page, "injectorPulseWidthMs").inner_text() + " ms")
    page.get_by_role("button", name="Injector", exact=True).click()
    expect(page.locator("#fuel-component-explanation")).to_contain_text("dead time")
    page.get_by_role("button", name="2D schematic", exact=True).click()
    expect(page.locator("#fuel-schematic")).to_be_visible()
    page.get_by_role("button", name="3D view", exact=True).click()
    expect(page.locator("#fuel-3d-canvas canvas")).to_be_visible()
    page.get_by_role("button", name="Reset camera", exact=True).click()
    destination = Path("test-results/fuel-delivery")
    destination.mkdir(parents=True, exist_ok=True)
    page.locator("#fuel-3d-stage").scroll_into_view_if_needed()
    page.screenshot(path=str(destination / "fuel-3d.png"))


def test_3d_unavailable_preserves_schematic(page, demo_records, live_server):
    page.add_init_script("""(() => { const original = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(type, ...args) {
        return type === 'webgl' || type === 'webgl2' ? null : original.call(this, type, ...args);
      }; })();""")
    open_fuel(page, demo_records, live_server)
    expect(page.locator("#fuel-3d-error")).to_contain_text("3D is unavailable")
    expect(page.locator("#fuel-schematic")).to_be_visible()
    expect(page.get_by_role("button", name="3D view", exact=True)).to_be_disabled()


def test_fuel_defaults_deterministic_time_export_and_comparison(page, demo_records, live_server):
    open_fuel(page, demo_records, live_server)
    page.clock.install()
    expect(output(page, "injectorPulseWidthMs")).to_have_text("8.471")
    expect(output(page, "cumulativeFuelG")).to_have_text("0.000")
    expect(page.locator("#fuel-time")).to_have_text("0.00")
    page.get_by_role("button", name="Run new simulation", exact=True).click()
    page.clock.run_for(30000)
    expect(page.locator("#fuel-mode")).to_have_text("Complete")
    expect(page.locator("#fuel-time")).to_have_text("30.00")
    expect(output(page, "cumulativeFuelG")).to_have_text("51.020")
    expect(output(page, "bsfcGPerKWh")).to_have_text("292.325")
    expect(page.locator("#fuel-record-status")).to_contain_text("300 recorded")
    expect(page.locator("#fuel-charts svg")).to_have_count(6)
    assert page.locator("#fuel-chart-0 polyline").first.get_attribute("points")
    with page.expect_download() as download:
        page.get_by_role("button", name="Export JSON", exact=True).click()
    data = json.loads(Path(download.value.path()).read_text())
    assert data["moduleId"] == "fuel-delivery-optimisation"
    assert len(data["integrationVector"]) == 8 and len(data["history"]) == 300
    assert data["outputs"]["cumulativeFuelG"] == pytest.approx(51.0204081633)
    with page.expect_download() as download:
        page.get_by_role("button", name="Export CSV", exact=True).click()
    rows = list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text())))
    assert len(rows) == 300
    assert float(rows[-1]["simulationTimeS"]) == pytest.approx(30)
    assert rows[-1]["input_fuelOptimisationScale"] == "1"
    page.get_by_label("Fuel optimisation scale (ratio)", exact=True).fill("0.98")
    page.get_by_role("button", name="Compare baseline and adjusted", exact=True).click()
    expect(page.locator("#fuel-comparison")).to_be_visible()
    expect(page.locator("#fuel-comparison")).to_contain_text("51.020")
    expect(page.locator("#fuel-comparison")).to_contain_text("50.000")
    expect(page.locator("#fuel-time")).to_have_text("30.00")
    page.get_by_role("button", name="Reset", exact=True).click()
    expect(page.locator("#fuel-time")).to_have_text("0.00")
    expect(output(page,"ltftPct")).to_have_text("0.000")
    expect(page.locator("#fuel-comparison")).not_to_be_visible()


def test_fuel_feedback_motion_pause_validation_and_fresh_navigation(page, demo_records, live_server):
    open_fuel(page, demo_records, live_server)
    page.clock.install()
    page.get_by_label("Measured lambda (ratio)", exact=True).fill("1.05")
    expect(output(page,"stftPct")).to_have_text("6.000")
    page.get_by_role("button", name="Run new simulation", exact=True).click()
    page.clock.run_for(5000)
    phase = page.locator("#fuel-schematic").get_attribute("data-phase")
    assert float(phase) > 0
    page.get_by_role("button", name="Pause", exact=True).click()
    time = page.locator("#fuel-time").inner_text()
    assert float(output(page,"ltftPct").inner_text()) == pytest.approx(float(time) * 6 * .003, abs=.00051)
    phase = page.locator("#fuel-schematic").get_attribute("data-phase")
    page.clock.run_for(2000)
    expect(page.locator("#fuel-time")).to_have_text(time)
    expect(page.locator("#fuel-schematic")).to_have_attribute("data-phase", phase)
    page.get_by_role("button", name="Resume", exact=True).click()
    page.clock.run_for(1000)
    page.get_by_role("button", name="Pause", exact=True).click()
    assert float(page.locator("#fuel-time").inner_text()) >= float(time) + 1 - 1e-6
    page.get_by_label("Engine speed (rpm)", exact=True).fill("0")
    expect(page.locator("#fuel-validation")).to_be_visible()
    expect(page.get_by_role("button",name="Run new simulation",exact=True)).to_be_disabled()
    expect(page.get_by_role("button",name="Export JSON",exact=True)).to_be_disabled()
    expect(page.locator("#fuel-mode")).to_have_text("Input error · paused")
    page.get_by_label("Engine speed (rpm)", exact=True).fill("2500")
    page.get_by_label("Brake torque (N m)", exact=True).fill("0")
    expect(output(page,"bsfcGPerKWh")).to_have_text("Not meaningful at near-zero power")
    page.get_by_role("button",name="Reset",exact=True).click()
    page.get_by_label("Measured lambda (ratio)", exact=True).fill("0.95")
    page.get_by_role("button",name="Apply recommended scale",exact=True).click()
    expect(page.get_by_label("Fuel optimisation scale (ratio)",exact=True)).to_have_value("0.95")
    page.get_by_label("Air flow (g/s)", exact=True).fill("200")
    expect(page.locator("#fuel-warnings")).to_contain_text("saturation")
    page.get_by_role("button",name="Injector",exact=True).click()
    expect(page.locator("#fuel-component-explanation")).to_contain_text("dead time")
    page.get_by_role("link",name="Back to ICE models",exact=True).click()
    expect(page.locator(".lab-model-grid article")).to_have_count(1)
    expect(page.get_by_role("link",name="Open Engine Live Data Demonstration",exact=True)).to_have_count(0)
    page.get_by_role("link",name="Open Fuel Delivery Optimisation",exact=True).click()
    expect(page.locator("#fuel-mode")).to_have_text("Paused")
    expect(page.locator("#fuel-time")).to_have_text("0.00")
    expect(output(page,"cumulativeFuelG")).to_have_text("0.000")


@pytest.mark.parametrize("width", [1280, 768, 390])
def test_fuel_accessible_responsive_reduced_motion(page, demo_records, live_server, width):
    page.set_viewport_size({"width":width,"height":900})
    page.emulate_media(reduced_motion="reduce")
    open_fuel(page,demo_records,live_server)
    expect(page.get_by_label("Animate illustrative flow",exact=True)).not_to_be_checked()
    expect(page.locator("#fuel-input-fields input[type=number]")).to_have_count(16)
    page.get_by_role("button",name="Increase Engine speed",exact=True).click()
    expect(page.get_by_label("Engine speed (rpm)",exact=True)).to_have_value("2550")
    page.get_by_role("button",name="Compare baseline and adjusted",exact=True).click()
    if width == 390:
        page.get_by_role("button",name="Hide inputs",exact=True).click()
        expect(page.locator("#fuel-input-fields")).not_to_be_visible()
    page.clock.install()
    page.get_by_role("button",name="Run new simulation",exact=True).click()
    page.clock.run_for(1000)
    expect(page.locator("#fuel-schematic")).to_have_attribute("data-phase","0.0000")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.add_script_tag(path="node_modules/axe-core/axe.min.js")
    results=page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
    assert not results["violations"],json.dumps(results["violations"],indent=2)
    destination=Path("test-results/fuel-delivery")
    destination.mkdir(parents=True,exist_ok=True)
    page.locator(".fuel-visual").scroll_into_view_if_needed()
    page.screenshot(path=str(destination/f"visual-{width}.png"))
    page.get_by_role("button",name="Pause",exact=True).click()
    page.screenshot(path=str(destination/f"page-{width}.png"),full_page=True)


def test_fuel_every_preset_and_subsecond_settings(page,demo_records,live_server):
    open_fuel(page,demo_records,live_server)
    for scenario in ["Warm cruise","Idle","Acceleration","High load","Cold operation","Lean feedback demonstration","Rich feedback demonstration"]:
        page.get_by_label("Scenario",exact=True).select_option(label=scenario)
        page.get_by_role("button",name="Load scenario",exact=True).click()
        expect(page.locator("#fuel-validation")).not_to_be_visible()
        expect(page.locator("#fuel-time")).to_have_text("0.00")
    page.get_by_label("Simulation duration (s)",exact=True).fill("5")
    page.get_by_label("Calculation step (s)",exact=True).fill("0.3")
    page.clock.install()
    page.get_by_role("button",name="Run new simulation",exact=True).click()
    page.clock.run_for(5100)
    expect(page.locator("#fuel-mode")).to_have_text("Complete")
    expect(page.locator("#fuel-time")).to_have_text("5.00")
    expect(page.locator("#fuel-record-status")).to_contain_text("17 recorded")


@pytest.mark.parametrize("width", [1280, 390])
def test_fuel_audit_input_help_nudges_and_duty_states(page, demo_records, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    open_fuel(page, demo_records, live_server)
    expect(page.locator(".fuel-toolbar #fuel-compare")).to_be_visible()
    expect(page.locator(".fuel-toolbar #fuel-recommend")).to_be_visible()
    expect(page.locator(".fuel-toolbar #fuel-json")).to_be_visible()
    for field in page.locator("#fuel-input-fields input[type=number]").all():
        key = field.get_attribute("id").replace("fuel-input-", "")
        purpose = page.locator(f"#fuel-purpose-{key}")
        assert len(purpose.text_content()) > 40
        assert purpose.get_attribute("id") in field.get_attribute("aria-describedby")
    page.get_by_text("About ltft learning gain", exact=True).click()
    expect(page.locator("#fuel-purpose-ltftLearningGainPerS")).to_be_visible()
    expect(page.locator("#fuel-purpose-ltftLearningGainPerS")).to_contain_text("Zero freezes")
    rpm = page.get_by_label("Engine speed (rpm)", exact=True)
    slider = page.get_by_label("Engine speed slider", exact=True)
    rpm.fill("6500")
    expect(slider).to_have_value("6500")
    page.get_by_role("button", name="Decrease Engine speed", exact=True).click()
    expect(rpm).to_have_value("6450")
    expect(slider).to_have_value("6450")
    page.get_by_role("button", name="Increase Engine speed", exact=True).click()
    expect(rpm).to_have_value("6500")
    page.get_by_label("Target lambda (ratio)", exact=True).fill("1.025")
    expect(page.get_by_label("Target lambda slider", exact=True)).to_have_value("1.025")
    page.get_by_role("button", name="Reset", exact=True).click()
    duty = page.locator("#fuel-duty")
    expect(duty).to_have_attribute("data-state", "normal")
    normal_accent = duty.evaluate("e=>getComputedStyle(e).accentColor")
    page.get_by_label("Air flow (g/s)", exact=True).fill("140")
    expect(duty).to_have_attribute("data-state", "high")
    expect(duty).to_have_attribute("aria-valuetext", re.compile("above 85%"))
    high_accent = duty.evaluate("e=>getComputedStyle(e).accentColor")
    page.get_by_label("Air flow (g/s)", exact=True).fill("200")
    expect(duty).to_have_attribute("data-state", "saturated")
    expect(page.locator("#fuel-duty-status")).to_contain_text("delivery is theoretical")
    expect(duty).to_have_attribute("aria-valuetext", re.compile("Saturated"))
    assert len({normal_accent, high_accent, duty.evaluate("e=>getComputedStyle(e).accentColor")}) == 3
    page.add_script_tag(path="node_modules/axe-core/axe.min.js")
    results = page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
    assert not results["violations"], json.dumps(results["violations"], indent=2)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    destination = Path("test-results/fuel-delivery")
    destination.mkdir(parents=True, exist_ok=True)
    page.locator(".fuel-visual").scroll_into_view_if_needed()
    page.screenshot(path=str(destination / f"audit-duty-{width}.png"))


def test_fuel_duration_edit_preserves_export_settings_and_requires_reset(page, demo_records, live_server):
    open_fuel(page, demo_records, live_server)
    page.clock.install()
    page.get_by_role("button", name="Run new simulation", exact=True).click()
    page.clock.run_for(30000)
    duration = page.get_by_label("Simulation duration (s)", exact=True)
    duration.fill("5")
    expect(page.locator("#fuel-validation")).to_contain_text("already recorded")
    expect(duration).to_have_attribute("aria-invalid", "true")
    expect(page.locator("#fuel-mode")).to_have_text("Input error · paused")
    expect(page.locator("#fuel-duration")).to_have_text("30")
    expect(page.locator("#fuel-time")).to_have_text("30.00")
    expect(page.locator("#fuel-record-status")).to_contain_text("300 recorded")
    expect(page.get_by_role("button", name="Export JSON", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Export CSV", exact=True)).to_be_disabled()
    duration.fill("30")
    with page.expect_download() as download:
        page.get_by_role("button", name="Export JSON", exact=True).click()
    payload = json.loads(Path(download.value.path()).read_text())
    assert payload["simulationTimeS"] == payload["simulationSettings"]["durationS"] == 30
    assert len(payload["history"]) == 300
    page.get_by_role("button", name="Reset", exact=True).click()
    duration.fill("5")
    page.get_by_role("button", name="Run new simulation", exact=True).click()
    page.clock.run_for(5000)
    expect(page.locator("#fuel-mode")).to_have_text("Complete")
    expect(page.locator("#fuel-time")).to_have_text("5.00")
    expect(page.locator("#fuel-duration")).to_have_text("5")


def test_fuel_calculation_errors_stop_time_block_exports_and_recover(page, demo_records, live_server):
    open_fuel(page, demo_records, live_server)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.clock.install()

    def set_extreme():
        for label, value in [("Injector rated flow (cc/min)", "500"),
                             ("Fuel-rail pressure (kPa)", "400"),
                             ("LTFT learning gain (1/s)", "0.01"),
                             ("Simulation duration (s)", "120"),
                             ("Target lambda (ratio)", "5e-305")]:
            page.get_by_label(label, exact=True).fill(value)

    set_extreme()
    page.get_by_role("button", name="Run new simulation", exact=True).click()
    page.clock.run_for(6000)
    expect(page.locator("#fuel-mode")).to_have_text("Calculation error · paused")
    expect(page.locator("#fuel-validation")).to_contain_text("non-finite")
    expect(page.locator("#fuel-time")).to_have_text("4.10")
    expect(page.get_by_role("button", name="Resume", exact=True)).to_be_disabled()
    for name in ["Export JSON", "Export CSV", "Compare baseline and adjusted"]:
        expect(page.get_by_role("button", name=name, exact=True)).to_be_disabled()
    page.clock.run_for(2000)
    expect(page.locator("#fuel-time")).to_have_text("4.10")
    page.get_by_label("Target lambda (ratio)", exact=True).fill("1")
    expect(page.locator("#fuel-validation")).not_to_be_visible()
    expect(page.get_by_role("button", name="Resume", exact=True)).to_be_enabled()
    page.get_by_role("button", name="Resume", exact=True).click()
    page.clock.run_for(1000)
    page.get_by_role("button", name="Pause", exact=True).click()
    assert float(page.locator("#fuel-time").inner_text()) > 4.1
    page.get_by_role("button", name="Reset", exact=True).click()
    set_extreme()
    page.get_by_role("button", name="Compare baseline and adjusted", exact=True).click()
    expect(page.locator("#fuel-mode")).to_have_text("Calculation error · paused")
    expect(page.locator("#fuel-validation")).to_contain_text("Comparison failed")
    expect(page.locator("#fuel-comparison")).not_to_be_visible()
    expect(page.get_by_role("button", name="Export JSON", exact=True)).to_be_disabled()
    page.get_by_role("button", name="Reset", exact=True).click()
    page.get_by_label("Air flow (g/s)", exact=True).fill("1e-312")
    page.get_by_label("Injector flow bias (%)", exact=True).fill("-99.9999999999")
    expect(page.locator("#fuel-validation")).to_contain_text("non-positive")
    expect(page.get_by_role("button", name="Run new simulation", exact=True)).to_be_disabled()
    page.get_by_role("button", name="Reset", exact=True).click()
    expect(page.locator("#fuel-validation")).not_to_be_visible()
    page.get_by_role("button", name="Compare baseline and adjusted", exact=True).click()
    expect(page.locator("#fuel-comparison")).to_be_visible()
    assert errors == []


def test_fuel_cylinder_highlight_tracks_events_and_honours_motion_preferences(page, demo_records, live_server):
    page.emulate_media(reduced_motion="no-preference")
    open_fuel(page, demo_records, live_server)
    page.clock.install()
    cylinder = page.locator("#fuel-cylinder-fill")
    page.get_by_role("button", name="Run new simulation", exact=True).click()
    page.clock.run_for(400)
    first = cylinder.get_attribute("opacity")
    page.clock.run_for(400)
    assert cylinder.get_attribute("opacity") != first
    page.get_by_role("button", name="Pause", exact=True).click()
    expect(cylinder).to_have_attribute("opacity", ".22")
    page.clock.run_for(400)
    expect(cylinder).to_have_attribute("opacity", ".22")
    page.get_by_role("button", name="Resume", exact=True).click()
    page.clock.run_for(400)
    assert float(cylinder.get_attribute("opacity")) > .22
    page.get_by_label("Animate illustrative flow", exact=True).uncheck()
    page.clock.run_for(400)
    expect(cylinder).to_have_attribute("opacity", ".22")
    page.get_by_label("Animate illustrative flow", exact=True).check()
    page.clock.run_for(400)
    assert float(cylinder.get_attribute("opacity")) > .22
    page.emulate_media(reduced_motion="reduce")
    expect(page.get_by_label("Animate illustrative flow", exact=True)).not_to_be_checked()
    page.clock.run_for(400)
    expect(cylinder).to_have_attribute("opacity", ".22")
