import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.mark.parametrize("width", [1280, 390])
def test_public_learning_rotates_every_minute_and_can_pause(page, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.emulate_media(reduced_motion="reduce")
    page.clock.install()
    requests = []
    failure = False

    def respond(route):
        requests.append(route.request.url)
        if failure:
            route.abort()
            return
        number = len(requests)
        route.fulfill(json={"id": f"fact-{number}", "title": f"Automotive lesson {number}",
            "text": "An electric traction motor converts electrical energy into mechanical motion.",
            "source_url": "https://en.wikipedia.org/wiki/Electric_motor", "source_name": "Wikipedia contributors",
            "credit": "Wikipedia excerpt · cached online source", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/", "mode": "online"})

    page.route("**/learning/fact/*", respond)
    page.goto(live_server.url)
    expect(page.locator("#learning-topic")).to_have_text("Automotive lesson 1")
    assert page.locator(".welcome-learning").evaluate("e => Boolean(e.compareDocumentPosition(document.querySelector('#access-title')) & Node.DOCUMENT_POSITION_FOLLOWING)")
    expect(page.locator("#learning-source")).to_have_attribute("href", "https://en.wikipedia.org/wiki/Electric_motor")
    expect(page.locator("#learning-license")).to_be_visible()
    page.clock.run_for(59000)
    expect(page.locator("#learning-topic")).to_have_text("Automotive lesson 1")
    page.clock.run_for(1000)
    expect(page.locator("#learning-topic")).to_have_text("Automotive lesson 2")
    assert "fact-1" in parse_qs(urlsplit(requests[-1]).query)["exclude"]
    page.get_by_role("button", name="Pause rotation", exact=True).click()
    page.clock.run_for(120000)
    expect(page.locator("#learning-topic")).to_have_text("Automotive lesson 2")
    assert len(requests) == 2
    page.get_by_role("button", name="Another fact", exact=True).click()
    expect(page.locator("#learning-topic")).to_have_text("Automotive lesson 3")
    page.get_by_role("button", name="Resume rotation", exact=True).click()
    page.clock.run_for(60000)
    expect(page.locator("#learning-topic")).to_have_text("Automotive lesson 4")
    failure = True
    page.get_by_role("button", name="Another fact", exact=True).click()
    expect(page.locator("#learning-note")).to_contain_text("Unable to refresh")
    expect(page.locator("#learning-topic")).to_have_text("Automotive lesson 4")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.add_script_tag(path="node_modules/axe-core/axe.min.js")
    result = page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']}})")
    assert not result["violations"], json.dumps(result["violations"], indent=2)
    destination = Path("test-results/home-learning")
    destination.mkdir(parents=True, exist_ok=True)
    page.locator(".welcome-learning").scroll_into_view_if_needed()
    page.screenshot(path=str(destination / f"learning-{width}.png"))
    page.get_by_role("link", name="Sign in", exact=True).click()
    expect(page.get_by_role("heading", name="Sign in", exact=True)).to_be_visible()


@pytest.mark.parametrize("bad_link", [True, False])
def test_untrusted_learning_payload_cannot_add_html_or_bad_links(page, live_server, bad_link):
    page.route("**/learning/fact/*", lambda route: route.fulfill(json={
        "id": "unsafe", "title": "<img src=x onerror=alert(1)>", "text": "Bad source URL",
        "source_name": "Untrusted", "source_url": "javascript:alert(1)" if bad_link else "https://en.wikipedia.org/wiki/Electric_motor", "license_url": "", "credit": "", "mode": "online"}))
    page.goto(live_server.url)
    if bad_link:
        expect(page.locator("#learning-note")).to_contain_text("Unable to refresh")
        assert page.locator("#learning-source").get_attribute("href").startswith("https://afdc.energy.gov/")
    else:
        expect(page.locator("#learning-topic")).to_have_text("<img src=x onerror=alert(1)>")
    expect(page.locator("#learning-topic img")).to_have_count(0)


def test_no_javascript_keeps_sourced_fact_and_sign_in(browser, live_server):
    context = browser.new_context(java_script_enabled=False, reduced_motion="reduce")
    try:
        page = context.new_page()
        page.goto(live_server.url)
        expect(page.get_by_role("heading", name="Did you know?", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Another fact", exact=True)).not_to_be_visible()
        page.get_by_role("link", name="Sign in", exact=True).click()
        expect(page.get_by_role("heading", name="Sign in", exact=True)).to_be_visible()
    finally:
        context.close()
