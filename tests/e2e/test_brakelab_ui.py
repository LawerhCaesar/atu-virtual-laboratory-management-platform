import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def open_brake(page, demo_records, live_server):
    page.goto(live_server.url + "/accounts/login/")
    page.get_by_label("Email address", exact=True).fill(demo_records["student"].email)
    page.get_by_label("Password", exact=True).fill("DemoPass!742")
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.get_by_role("link", name="Virtual laboratory", exact=True).click()
    page.get_by_role("link", name="Enter BEV environment", exact=True).click()
    expect(page.locator(".lab-model-grid article")).to_have_count(3)
    page.get_by_role("link", name="Open Regenerative and Friction Brake-Force Allocation", exact=True).click()
    expect(page.locator("#brake-input-fields input")).to_have_count(21)
    expect(page.locator("#brakelab [data-brake-output]")).to_have_count(24)
    expect(page.locator("#brake-mode")).to_have_text("Preview")


def output(page, key):
    return page.locator(f'[data-brake-output="{key}"]')


def test_brake_baseline_charts_scaled_animation_and_export(page, demo_records, live_server):
    open_brake(page, demo_records, live_server)
    page.emulate_media(reduced_motion="no-preference")
    page.get_by_label("Animate illustrative braking", exact=True).check()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.clock.install()
    for key, value in {"requestedForceN": "2100.0", "regenerativeForceN": "2100.0", "frictionForceN": "0.0",
                       "batteryChargePowerKw": "30.80", "regenerativeCurrentA": "88.00", "motorSpeedRpm": "4620.6"}.items():
        expect(output(page, key)).to_have_text(value)
    expect(page.locator("#brake-balance")).to_contain_text("Verified (<0.001 N)")
    expect(page.locator("#brake-limit")).to_have_attribute("data-code", "DRIVER_DEMAND")
    expect(page.locator("#brake-analysis progress")).to_have_count(10)
    expect(page.locator('#brake-force-chart [data-minimum="true"]')).to_have_attribute("data-brake-chart", "requestedForceN")
    expect(page.locator("#brake-stop-estimate")).to_contain_text("11.90 s")
    expect(page.locator("#brake-stop-estimate")).to_contain_text("99.21 m")
    page.get_by_role("button", name="Run Model", exact=True).click()
    page.clock.run_for(4000)
    assert 29 <= float(page.locator("#brake-speed").inner_text()) <= 31
    assert float(page.locator("#brake-wheel-flow").get_attribute("opacity")) > 0
    page.get_by_role("button", name="Pause", exact=True).click()
    progress = page.locator("#brake-scene").get_attribute("data-progress")
    page.clock.run_for(1000)
    expect(page.locator("#brake-scene")).to_have_attribute("data-progress", progress)
    page.get_by_role("button", name="Resume", exact=True).click()
    page.clock.run_for(4200)
    expect(page.locator("#brake-mode")).to_have_text("Illustration complete")
    expect(page.locator("#brake-speed")).to_have_text("0.0")
    expect(page.locator("#brake-wheel-flow")).to_have_attribute("opacity", "0")
    expect(page.locator("#brake-charge-flow")).to_have_attribute("opacity", "0")
    expect(output(page, "regenerativeForceN")).to_have_text("2100.0")
    with page.expect_download() as download:
        page.get_by_role("button", name="Export JSON", exact=True).click()
    payload = json.loads(Path(download.value.path()).read_text())
    assert payload["moduleId"] == "brakelab"
    assert payload["inputs"]["vehicleSpeedKph"] == 60
    assert payload["result"]["batteryChargePowerKw"] == pytest.approx(30.8)
    assert payload["result"]["visual"]["stopTimeEstimateS"] == pytest.approx(11.9047619048)
    assert payload["playback"]["illustrative"] and payload["status"]["forceBalanceValid"]
    assert "no SLX" in payload["sourceBasis"]
    assert errors == []


def test_brake_limits_preview_nudges_validation_and_zero_demand(page, demo_records, live_server):
    open_brake(page, demo_records, live_server)
    for label, value, code in [("Battery SOC (%)", "95", "BATTERY_SOC"), ("Battery temperature (°C)", "55", "BATTERY_TEMPERATURE"),
                               ("Vehicle speed (km/h)", "7.2", "LOW_SPEED")]:
        page.get_by_role("button", name="Reset to Baseline", exact=True).click()
        page.get_by_label(label, exact=True).fill(value)
        expect(page.locator("#brake-limit")).to_have_attribute("data-code", code)
        expect(output(page, "regenerativeForceN")).to_have_text("0.0")
        expect(output(page, "frictionForceN")).to_have_text("2100.0")
        expect(page.locator("#brake-wheel-flow")).to_have_attribute("opacity", "0")
    page.get_by_role("button", name="Reset to Baseline", exact=True).click()
    page.get_by_label("Regeneration Enabled", exact=True).uncheck()
    expect(page.locator("#brake-limit")).to_have_attribute("data-code", "REGEN_DISABLED")
    assert float(page.locator("#brake-friction-glow").get_attribute("opacity")) > 0
    page.get_by_role("button", name="Reset to Baseline", exact=True).click()
    mass = page.get_by_label("Vehicle mass (kg)", exact=True)
    mass.fill("4500")
    page.get_by_role("button", name="Decrease Vehicle mass", exact=True).click()
    expect(mass).to_have_value("4450")
    expect(page.get_by_label("Vehicle mass slider", exact=True)).to_have_value("4450")
    expect(page.locator("#brake-warnings")).to_contain_text("suggested educational range")
    page.get_by_role("button", name="Reset to Baseline", exact=True).click()
    page.get_by_label("Live Update previews", exact=True).uncheck()
    mass.fill("2000")
    expect(page.locator("#brake-mode")).to_contain_text("Run Model required")
    expect(output(page, "requestedForceN")).to_have_text("2100.0")
    expect(page.get_by_role("button", name="Export JSON", exact=True)).to_be_disabled()
    page.get_by_role("button", name="Run Model", exact=True).click()
    expect(output(page, "requestedForceN")).to_have_text("2800.0")
    page.get_by_role("button", name="Reset to Baseline", exact=True).click()
    expect(page.locator("#brake-mode")).to_have_text("Preview")
    page.get_by_label("Live Update previews", exact=True).check()
    page.get_by_label("Battery voltage (V)", exact=True).fill("0")
    expect(page.locator("#brake-validation")).to_be_visible()
    expect(page.get_by_role("button", name="Run Model", exact=True)).to_be_disabled()
    expect(page.get_by_role("button", name="Export JSON", exact=True)).to_be_disabled()
    page.get_by_label("Battery voltage (V)", exact=True).fill("350")
    page.get_by_label("Brake demand (ratio)", exact=True).fill("0")
    expect(page.locator("#brake-stop-estimate")).to_contain_text("no finite stopping estimate")
    page.get_by_role("button", name="Run Model", exact=True).click()
    expect(page.locator("#brake-speed")).to_have_text("60.0")
    expect(page.locator("#brake-mode")).to_contain_text("No braking")
    page.get_by_label("Brake demand (ratio)", exact=True).fill(str(.5 / (1500 * 3.5)))
    expect(output(page, "regenerativePercent")).to_have_text("50.0")
    expect(page.locator("#brake-share-note")).to_contain_text("Below 1 N")
    page.get_by_label("Brake demand (ratio)", exact=True).fill("1")
    mass.fill("1e308")
    expect(page.locator("#brake-validation")).to_contain_text("non-finite")
    expect(page.get_by_role("button", name="Export JSON", exact=True)).to_be_disabled()
    page.get_by_role("button", name="Reset to Baseline", exact=True).click()
    expect(page.locator("#brake-validation")).not_to_be_visible()


@pytest.mark.parametrize("width", [1280, 768, 390])
def test_brake_accessibility_responsiveness_reduced_motion_and_fresh_navigation(page, demo_records, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.emulate_media(reduced_motion="reduce")
    open_brake(page, demo_records, live_server)
    expect(page.get_by_label("Animate illustrative braking", exact=True)).not_to_be_checked()
    expect(page.locator("#brake-calibration dd")).to_have_count(15)
    for field in page.locator("#brake-input-fields input[type=number]").all():
        key = field.get_attribute("id").replace("brake-input-", "")
        assert "brake-purpose-" + key in field.get_attribute("aria-describedby")
    page.get_by_text("About battery soc", exact=True).click()
    expect(page.locator("#brake-purpose-batterySocPct")).to_be_visible()
    page.get_by_role("button", name="Run Model", exact=True).click()
    expect(page.locator("#brake-mode")).to_have_text("Static result · motion off")
    expect(page.locator("#brake-speed")).to_have_text("60.0")
    page.add_script_tag(path="node_modules/axe-core/axe.min.js")
    result = page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
    assert not result["violations"], json.dumps(result["violations"], indent=2)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    destination = Path("test-results/brakelab")
    destination.mkdir(parents=True, exist_ok=True)
    page.locator(".brake-visual").scroll_into_view_if_needed()
    page.screenshot(path=str(destination / f"visual-{width}.png"))
    page.screenshot(path=str(destination / f"page-{width}.png"), full_page=True)
    page.locator("#brake-analysis").screenshot(path=str(destination / f"analysis-{width}.png"))
    page.get_by_role("link", name="Back to BEV models", exact=True).click()
    page.get_by_role("link", name="Open Regenerative and Friction Brake-Force Allocation", exact=True).click()
    expect(page.locator("#brake-mode")).to_have_text("Preview")
    expect(output(page, "requestedForceN")).to_have_text("2100.0")


def test_brake_motion_preference_changes_pause_the_playback(page, demo_records, live_server):
    page.emulate_media(reduced_motion="no-preference")
    open_brake(page, demo_records, live_server)
    page.clock.install()
    page.get_by_role("button", name="Run Model", exact=True).click()
    page.clock.run_for(1000)
    assert float(page.locator("#brake-speed").inner_text()) < 60
    page.emulate_media(reduced_motion="reduce")
    expect(page.get_by_label("Animate illustrative braking", exact=True)).not_to_be_checked()
    expect(page.locator("#brake-mode")).to_have_text("Paused")
    progress = page.locator("#brake-scene").get_attribute("data-progress")
    page.clock.run_for(1000)
    expect(page.locator("#brake-scene")).to_have_attribute("data-progress", progress)
