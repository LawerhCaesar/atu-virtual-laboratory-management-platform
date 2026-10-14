import io
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from django.core.management import call_command
from playwright.sync_api import sync_playwright

from apps.accounts.models import User
from apps.core.models import AdministratorNotice, SupportRequest
from apps.practicals.models import ApprovedResource, PracticalSubmission


@pytest.fixture
def demo_records(settings, tmp_path, transactional_db):
    settings.DEBUG = True
    settings.MEDIA_ROOT = tmp_path / "private-media"
    # Django's live_server helper otherwise exposes media for convenience.
    # Disable that helper URL so /media/ exercises the real application routing.
    settings.MEDIA_URL = "/__disabled_test_media_helper__/"
    call_command("seed_demo_data", stdout=io.StringIO())
    administrator = User.objects.get(email="admin@atu-demo.local")
    student = User.objects.get(email="student@atu-demo.local")
    return {
        "administrator": administrator,
        "lecturer": User.objects.get(email="lecturer@atu-demo.local"),
        "student": student,
        "resource": ApprovedResource.objects.create(title="Unused synthetic resource", version_label="v1", url="https://example.edu/resource", created_by=administrator),
        "notice": AdministratorNotice.objects.create(title="Synthetic draft notice", message="Example platform support notice.", audience="STUDENT", link="/help/", created_by=administrator),
        "support": SupportRequest.objects.create(submitted_by=student, subject="Synthetic support request", message="Example task-access question."),
        "draft": PracticalSubmission.objects.get(student__email="student@atu-demo.local"),
        "review": PracticalSubmission.objects.get(student__email="review-student@atu-demo.local"),
    }


@pytest.fixture(scope="session")
def browser(django_db_setup):
    # Playwright's sync driver owns an event loop in the runner thread.
    # These serial tests access only the isolated test DB, after requests finish.
    # Never set this exception in application/deployment configuration.
    previous = os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE")
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    try:
        with sync_playwright() as playwright:
            options = {"headless": True}
            if os.getenv("ATU_BROWSER_CHANNEL"):
                options["channel"] = os.environ["ATU_BROWSER_CHANNEL"]
            instance = playwright.chromium.launch(**options)
            yield instance
            instance.close()
    finally:
        if previous is None:
            os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
        else:
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = previous


@pytest.fixture
def browser_context(browser, request):
    context = browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    context.route("**/*", lambda route: route.continue_() if urlsplit(route.request.url).hostname in {"localhost", "127.0.0.1"} else route.abort())
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context
    failed = getattr(request.node, "rep_call", None)
    if failed and failed.failed:
        destination = Path("test-results/e2e") / re.sub(r"[^a-zA-Z0-9_-]", "_", request.node.name)
        destination.mkdir(parents=True, exist_ok=True)
        for number, page in enumerate(context.pages):
            page.screenshot(path=str(destination / f"page-{number}.png"), full_page=True)
        context.tracing.stop(path=str(destination / "trace.zip"))
    else:
        context.tracing.stop()
    context.close()


@pytest.fixture
def page(browser_context):
    return browser_context.new_page()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    setattr(item, f"rep_{report.when}", report)
