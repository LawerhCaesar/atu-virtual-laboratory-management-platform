import json
import re
from pathlib import Path

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def sign_in(page, demo_records, live_server):
    page.goto(live_server.url + "/accounts/login/")
    page.get_by_label("Email address", exact=True).fill(demo_records["student"].email)
    page.get_by_label("Password", exact=True).fill("DemoPass!742")
    page.get_by_role("button", name="Sign in", exact=True).click()


@pytest.mark.parametrize("path,field,baseline,guide_name", [
    ("/virtual-lab/fuel-delivery-optimisation/", "Air flow (g/s)", "25", "Fuel Delivery Optimisation"),
    ("/virtual-lab/brakelab/", "Battery SOC (%)", "50", "Ebenezer Wilson’s Braking Laboratory"),
    ("/virtual-lab/vehicle-dynamics/wheel-slip-abs-tcs/", "Road friction coefficient (ratio)", "0.35", "Wheel-Slip Control Using ABS and TCS"),
])
def test_first_visit_reopen_navigation_and_no_mutation(page, demo_records, live_server, path, field, baseline, guide_name):
    sign_in(page, demo_records, live_server)
    page.goto(live_server.url + path)
    panel = page.locator("#tour-panel")
    expect(panel).to_be_visible()
    expect(panel).to_contain_text(guide_name)
    expect(page.locator("#tour-count")).to_contain_text("Step 1 of")
    expect(page.get_by_label(field, exact=True)).to_have_value(baseline)
    page.get_by_role("button", name="Next", exact=True).click()
    expect(page.locator("#tour-count")).to_contain_text("Step 2 of")
    page.get_by_role("button", name="Show me", exact=True).click()
    expect(page.locator(".tour-target-highlight")).to_have_count(1)
    page.get_by_role("button", name="Open module guide", exact=True).click()
    page.get_by_role("button", name="Finish later", exact=True).click()
    expect(panel).to_be_hidden()
    expect(page.locator(".tour-target-highlight")).to_have_count(0)
    expect(page.get_by_label(field, exact=True)).to_have_value(baseline)
    page.reload()
    expect(panel).to_be_hidden()
    page.get_by_role("button", name="Open module guide", exact=True).click()
    expect(panel).to_be_visible()
    expect(page.locator("#tour-count")).to_contain_text("Step 2 of")
    page.get_by_role("button", name="Back", exact=True).click()
    expect(page.locator("#tour-count")).to_contain_text("Step 1 of")
    expect(page.get_by_label(field, exact=True)).to_have_value(baseline)
    panel.press("Escape")
    expect(panel).to_be_hidden()
    expect(page.locator("#tour-launch")).to_be_focused()


def test_guides_are_per_module_and_walkthrough_test_instructions(page, demo_records, live_server):
    sign_in(page, demo_records, live_server)
    page.goto(live_server.url + "/virtual-lab/brakelab/")
    expect(page.locator("#tour-panel")).to_be_visible()
    for _ in range(2):
        page.get_by_role("button", name="Next", exact=True).click()
    expect(page.locator("#tour-check")).to_contain_text("2,100 N")
    expect(page.locator("#tour-check")).to_contain_text("95%")
    page.get_by_role("button", name="Close module guide").click()
    page.goto(live_server.url + "/virtual-lab/vehicle-dynamics/wheel-slip-abs-tcs/")
    expect(page.locator("#tour-panel")).to_be_visible()
    for _ in range(4):
        page.get_by_role("button", name="Next", exact=True).click()
    expect(page.locator("#tour-check")).to_contain_text("ABS active time")
    expect(page.locator("#tour-check")).to_contain_text("TCS active time")
    while page.get_by_role("button", name="Next", exact=True).is_visible():
        page.get_by_role("button", name="Next", exact=True).click()
    page.get_by_role("button", name="Finish guide", exact=True).click()
    expect(page.locator("#tour-panel")).to_be_hidden()
    page.get_by_role("button", name="Open module guide", exact=True).click()
    expect(page.locator("#tour-count")).to_contain_text("Step 1 of")


def test_storage_blocked_keeps_guide_usable(page, demo_records, live_server):
    sign_in(page, demo_records, live_server)
    page.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('blocked'); }});")
    page.goto(live_server.url + "/virtual-lab/brakelab/")
    expect(page.locator("#tour-panel")).to_be_visible()
    expect(page.locator(".tour-note")).to_contain_text("Browser storage is unavailable")
    page.get_by_role("button", name="Next", exact=True).click()
    page.get_by_role("button", name="Close module guide").click()
    expect(page.locator("#tour-panel")).to_be_hidden()
    page.get_by_role("button", name="Open module guide", exact=True).click()
    expect(page.locator("#tour-count")).to_contain_text("Step 2 of")


def test_seen_status_is_isolated_per_account_on_shared_browser(page, demo_records, live_server):
    sign_in(page, demo_records, live_server)
    page.goto(live_server.url + "/virtual-lab/brakelab/")
    page.get_by_role("button", name="Close module guide").click()
    page.get_by_role("button", name="Sign out", exact=True).click()
    page.goto(live_server.url + "/accounts/login/")
    page.get_by_label("Email address", exact=True).fill(demo_records["lecturer"].email)
    page.get_by_label("Password", exact=True).fill("DemoPass!742")
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.goto(live_server.url + "/virtual-lab/brakelab/")
    expect(page.locator("#tour-panel")).to_be_visible()
    expect(page.locator("#tour-count")).to_contain_text("Step 1 of")


@pytest.mark.parametrize("path,input_id,before,changed,after,expected_text,output_id", [
    ("/virtual-lab/fuel-delivery-optimisation/", "#fuel-input-airFlowGps", "20.408", "50", "40.816", "40.816", '[data-fuel-output="baseFuelMgPerEvent"]'),
    ("/virtual-lab/brakelab/", "#brake-input-batterySocPct", "2100.0", "95", "0.0", "0 N", '[data-brake-output="regenerativeForceN"]'),
])
def test_follow_the_documented_verification_example(page, demo_records, live_server, path, input_id, before, changed, after, expected_text, output_id):
    sign_in(page, demo_records, live_server)
    page.goto(live_server.url + path)
    page.get_by_role("button", name="Next", exact=True).click()
    page.get_by_role("button", name="Next", exact=True).click()
    expect(page.locator("#tour-check")).to_contain_text(expected_text)
    page.get_by_role("button", name="Show me", exact=True).click()
    expect(page.locator(input_id)).to_have_class(re.compile(r"\btour-target-highlight\b"), timeout=5000)
    expect(page.locator(output_id)).to_have_text(before)
    page.locator(input_id).fill(changed)
    expect(page.locator(output_id)).to_have_text(after)


@pytest.mark.parametrize("width", [1280, 390])
def test_walkthrough_accessibility_and_responsive_layout(page, demo_records, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    sign_in(page, demo_records, live_server)
    page.goto(live_server.url + "/virtual-lab/fuel-delivery-optimisation/")
    expect(page.locator("#tour-panel")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.add_script_tag(path="node_modules/axe-core/axe.min.js")
    results = page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})")
    assert not results["violations"], json.dumps(results["violations"], indent=2)
    dest = Path("test-results/walkthrough")
    dest.mkdir(parents=True, exist_ok=True)
    page.locator("#tour-panel").screenshot(path=str(dest / f"guide-{width}.png"))
