import csv
import io
import json
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


@pytest.mark.parametrize("width", [1280, 390])
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
