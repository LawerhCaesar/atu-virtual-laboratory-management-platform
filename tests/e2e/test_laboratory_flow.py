import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

from apps.core.laboratory import SYSTEMS

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.mark.parametrize("width", [1280, 390])
def test_system_selection_branding_catalogues_and_launch(page, demo_records, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(live_server.url)
    expect(page.locator(".engineering-fields dt")).to_have_count(5)
    expect(page.locator(".engineering-fields")).to_contain_text("FCEV")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.goto(live_server.url + "/accounts/login/")
    page.get_by_label("Email address", exact=True).fill(demo_records["student"].email)
    page.get_by_label("Password", exact=True).fill("DemoPass!742")
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.get_by_role("link", name="Choose a system", exact=True).click()
    expect(page.get_by_role("heading", name="Choose your system", exact=True)).to_be_visible()
    destination = Path("test-results/laboratory")
    destination.mkdir(parents=True, exist_ok=True)

    def check_page(label):
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.add_script_tag(path="node_modules/axe-core/axe.min.js")
        result = page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}})")
        assert not result["violations"], json.dumps(result["violations"], indent=2)
        page.screenshot(path=str(destination / f"{label}-{width}.png"), full_page=True)

    check_page("selector")
    colours = set()
    for system in SYSTEMS:
        page.get_by_role("link", name=f'Enter {system["code"]} environment', exact=True).click()
        expect(page.get_by_role("heading", name=system["name"], exact=True)).to_be_visible()
        colours.add(page.locator(".lab-system-hero").evaluate("e => getComputedStyle(e).backgroundColor"))
        if system["slug"] != "ice":
            expect(page.locator('a[href*="engine-live-data"]')).to_have_count(0)
        if system["slug"] != "ice":
            expect(page.get_by_role("heading", name="Engine Live Data Demonstration", exact=True)).to_have_count(0)
        if system["slug"] not in ("ice", "bev", "hybrid", "vehicle-dynamics", "fcev"):
            expect(page.get_by_role("heading", name="No simulations added yet", exact=True)).to_be_visible()
            expect(page.locator(".lab-model-grid article, .lab-launch")).to_have_count(0)
            expect(page.get_by_text("Scope for future models", exact=False)).to_have_count(0)
        elif system["slug"] == "ice":
            expect(page.locator(".lab-model-grid article")).to_have_count(3)
            expect(page.get_by_role("heading", name="Fuel Delivery Optimisation", exact=True)).to_be_visible()
        elif system["slug"] == "bev":
            expect(page.locator(".lab-model-grid article")).to_have_count(3)
            expect(page.get_by_role("link", name="Open Battery Energy Management", exact=True)).to_be_visible()
            expect(page.get_by_role("heading", name="Regenerative and Friction Brake-Force Allocation", exact=True)).to_be_visible()
            expect(page.get_by_role("link", name="Open Fuel Delivery Optimisation", exact=True)).to_have_count(0)
        elif system["slug"] == "hybrid":
            expect(page.locator(".lab-model-grid article")).to_have_count(3)
            expect(page.get_by_role("heading", name="P2 Full-Parallel Hybrid", exact=True)).to_be_visible()
            expect(page.get_by_role("heading", name="12 V Micro-Hybrid Stop-Start", exact=True)).to_be_visible()
        elif system["slug"] == "fcev":
            expect(page.locator(".lab-model-grid article")).to_have_count(1)
            expect(page.get_by_role("link", name="Open Fuel-Cell / Battery and Diesel Comparison", exact=True)).to_be_visible()
        else:
            expect(page.locator(".lab-model-grid article")).to_have_count(2)
            expect(page.get_by_role("heading", name="Wheel-Slip Control Using ABS and TCS", exact=True)).to_be_visible()
            expect(page.get_by_role("heading", name="Vehicle Steering Response", exact=True)).to_be_visible()
        check_page(system["slug"])
        page.get_by_role("link", name="All systems", exact=True).click()
    assert len(colours) == 5
    page.get_by_role("link", name="Enter ICE environment", exact=True).click()
    page.get_by_role("link", name="Open Fuel Delivery Optimisation", exact=True).click()
    expect(page.get_by_role("heading", name="Fuel Delivery Optimisation", exact=True)).to_be_visible()
    expect(page.locator("#fuel-mode")).to_have_text("Paused")
    expect(page.locator("#fuel-time")).to_have_text("0.00")
    expect(page.locator("#fuel-kpis [data-fuel-output]")).to_have_count(14)
    page.get_by_role("link", name="Back to ICE models", exact=True).click()
    expect(page.locator(".lab-model-grid article")).to_have_count(3)
    response = page.goto(live_server.url + "/virtual-lab/engine-live-data/?view=fuel")
    assert response.status == 200
