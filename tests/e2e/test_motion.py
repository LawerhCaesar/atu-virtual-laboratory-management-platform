import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.mark.parametrize("preference", ["reduce", "no-preference"])
def test_interface_motion_is_progressive_and_respects_preferences(page, live_server, preference):
    page.emulate_media(reduced_motion=preference)
    page.goto(live_server.url + "/")
    title = page.locator("#welcome-title")
    expect(title).to_be_visible()
    name = title.evaluate("element => getComputedStyle(element).animationName")
    assert name == ("none" if preference == "reduce" else "atu-rise")
    page.get_by_role("link", name="Sign in", exact=True).click()
    expect(page.get_by_role("heading", name="Sign in", exact=True)).to_be_visible()
    email = page.get_by_label("Email address", exact=True)
    email.fill("motion-test@example.test")
    page.get_by_label("Password", exact=True).focus()
    expect(email).to_have_value("motion-test@example.test")
    if preference == "reduce":
        assert page.locator(".access-layout").evaluate("e => getComputedStyle(e).animationName") == "none"
        assert page.get_by_role("button", name="Sign in", exact=True).evaluate("e => getComputedStyle(e).transitionDuration") == "0s"
