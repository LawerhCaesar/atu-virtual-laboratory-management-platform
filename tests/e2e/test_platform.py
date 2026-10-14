import json
from pathlib import Path

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.accounts.models import User
from apps.core.models import AdministratorNotice, SupportRequest
from apps.practicals.models import Assessment


pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def sign_in(page, base_url, email, password="DemoPass!742"):
    page.goto(f"{base_url}/accounts/login/")
    page.get_by_label("Email address", exact=True).fill(email)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page).to_have_url(f"{base_url}/dashboard/")


def sign_out(page):
    page.get_by_role("button", name="Sign out", exact=True).click()


def test_registration_is_pending_and_administrator_is_not_public(page, demo_records, live_server):
    base = live_server.url
    page.goto(f"{base}/accounts/register/")
    assert page.get_by_label("Role", exact=True).locator("option").all_text_contents() == ["Student", "Lecturer"]
    page.get_by_label("Full name", exact=True).fill("E2E Pending Student")
    page.get_by_label("Email", exact=True).fill("e2e-pending@example.edu")
    page.get_by_label("Password", exact=True).fill("E2EPassword!842")
    page.get_by_label("Password confirmation", exact=True).fill("E2EPassword!842")
    page.get_by_role("button", name="Submit registration").click()
    user = User.objects.get(email="e2e-pending@example.edu")
    assert user.approval_status == User.ApprovalStatus.PENDING
    assert not user.is_staff
    page.goto(f"{base}/accounts/login/")
    page.get_by_label("Email address").fill(user.email)
    page.get_by_label("Password", exact=True).fill("E2EPassword!842")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.get_by_text("Your account is awaiting administrator approval.", exact=True)).to_be_visible()


def test_student_submission_and_private_grade_release(page, demo_records, live_server):
    base = live_server.url
    submission = demo_records["draft"]
    sign_in(page, base, demo_records["student"].email)
    page.goto(base + reverse("practicals:submission_workspace", args=[submission.pk]))
    page.get_by_label("Response text", exact=True).fill("Synthetic E2E diagnostic interpretation; not a research result.")
    page.get_by_role("button", name="Save draft", exact=True).click()
    page.get_by_label("File", exact=True).set_input_files({"name": "parameters.csv", "mimeType": "text/csv", "buffer": b"parameter,value\nspeed,30\n"})
    page.get_by_role("button", name="Add evidence file").click()
    expect(page.get_by_role("link", name="parameters.csv")).to_be_visible()
    page.get_by_role("button", name="Submit attempt", exact=True).click()
    submission.refresh_from_db()
    assert submission.status == submission.Status.SUBMITTED
    assert page.goto(base + reverse("practicals:submission_workspace", args=[submission.pk])).url.endswith(f"/assigned/{submission.task_id}/")
    sign_out(page)

    sign_in(page, base, demo_records["lecturer"].email)
    page.goto(base + reverse("practicals:submission_review", args=[submission.pk]))
    page.get_by_label("Score", exact=True).fill("78.50")
    page.get_by_label("Feedback", exact=True).fill("Synthetic E2E feedback.")
    page.get_by_role("button", name="Save assessment", exact=True).click()
    assessment = Assessment.objects.get(submission=submission)
    assert assessment.status == Assessment.Status.DRAFT
    sign_out(page)

    sign_in(page, base, demo_records["student"].email)
    assert page.goto(base + reverse("practicals:result_detail", args=[assessment.pk])).status == 404
    page.goto(f"{base}/dashboard/")
    sign_out(page)
    sign_in(page, base, demo_records["lecturer"].email)
    page.goto(base + reverse("practicals:submission_review", args=[submission.pk]))
    page.get_by_role("button", name="Release to student", exact=True).click()
    sign_out(page)
    sign_in(page, base, demo_records["student"].email)
    page.goto(base + reverse("practicals:result_detail", args=[assessment.pk]))
    expect(page.get_by_text("78.50", exact=False)).to_be_visible()


def test_admin_reports_and_one_time_password_reset(page, demo_records, live_server):
    base = live_server.url
    sign_in(page, base, demo_records["administrator"].email)
    page.goto(f"{base}/reports/")
    expect(page.get_by_role("heading", name="Reports and exports", exact=True)).to_be_visible()
    with page.expect_download() as download:
        page.get_by_role("link", name="Export users CSV").click()
    assert download.value.suggested_filename == "atu-users.csv"
    page.goto(base + reverse("accounts:admin_password_reset", args=[demo_records["student"].pk]))
    expect(page.get_by_role("heading", name="Reset account password?", exact=True)).to_be_visible()
    page.get_by_role("button", name="Confirm password reset").click()
    temporary = page.locator("#temporary-password").input_value().strip()
    assert temporary
    sign_out(page)
    page.goto(f"{base}/accounts/login/")
    page.get_by_label("Email address").fill(demo_records["student"].email)
    page.get_by_label("Password", exact=True).fill(temporary)
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page).to_have_url(f"{base}/accounts/password/change/")
    demo_records["student"].refresh_from_db()
    assert demo_records["student"].must_change_password


@pytest.mark.parametrize("role,path", [
    (None, "/"), (None, "/accounts/login/"), (None, "/accounts/register/"),
    ("administrator", "/dashboard/"), ("administrator", "/reports/"),
    ("administrator", "/reports/audit/"), ("administrator", "/accounts/manage/"),
    ("lecturer", "/dashboard/"), ("lecturer", "/practicals/tasks/new/"),
    ("lecturer", "review"),
    ("student", "/dashboard/"), ("student", "draft"),
    (None, "/help/"), ("student", "/help/"),
    ("administrator", "/management/settings/"),
    ("administrator", "/management/notices/"),
    ("administrator", "/management/notices/new/"),
    ("administrator", "notice-preview"),
    ("administrator", "/management/support/"),
    ("administrator", "support-review"),
    ("administrator", "/practicals/resources/"),
    ("administrator", "resource-edit"),
    ("administrator", "resource-revision"),
    ("administrator", "resource-disable"),
    ("administrator", "account-suspend"),
])
@pytest.mark.parametrize("width", [1280, 390])
def test_accessibility_and_responsive_layout(page, demo_records, live_server, role, path, width, request):
    base = live_server.url
    if role:
        sign_in(page, base, demo_records[role].email)
    if path == "draft":
        path = reverse("practicals:submission_workspace", args=[demo_records["draft"].pk])
    elif path == "review":
        path = reverse("practicals:submission_review", args=[demo_records["review"].pk])
    elif path == "notice-preview":
        path = reverse("core:notice_detail", args=[demo_records["notice"].pk])
    elif path == "support-review":
        path = reverse("core:support_review", args=[demo_records["support"].pk])
    elif path == "resource-edit":
        path = reverse("practicals:resource_edit", args=[demo_records["resource"].pk])
    elif path == "resource-revision":
        path = reverse("practicals:resource_revision", args=[demo_records["resource"].pk])
    elif path == "resource-disable":
        path = reverse("practicals:resource_availability", args=[demo_records["resource"].pk, "disable"])
    elif path == "account-suspend":
        path = reverse("accounts:account_availability", args=[demo_records["student"].pk, "suspend"])
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(base + path)
    expect(page.locator("main h1")).to_be_visible()
    if path == "/":
        page.keyboard.press("Tab")
        expect(page.get_by_role("link", name="Skip to main content")).to_be_focused()
        page.keyboard.press("Enter")
        expect(page.locator("main")).to_be_focused()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Page overflows the viewport."
    assert page.evaluate(r"""() => [...document.querySelectorAll('[aria-describedby]')].every(field => field.getAttribute('aria-describedby').split(/\s+/).every(id => document.getElementById(id)))"""), "A form description points to a missing element."
    assert page.evaluate("""() => [...document.querySelectorAll('.atu-form-field input, .atu-form-field select, .atu-form-field textarea')].every(field => field.getBoundingClientRect().right <= field.parentElement.getBoundingClientRect().right + 1)"""), "A form field overflows its container."
    page.add_script_tag(path=str(Path("node_modules/axe-core/axe.min.js").resolve()))
    result = page.evaluate("""async () => await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']}})""")
    artifact = Path("test-results/accessibility") / f"{request.node.name}.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(result, indent=2), encoding="utf-8")
    page.screenshot(path=str(artifact.with_suffix(".png")), full_page=True)
    assert not result["violations"], json.dumps(result["violations"], indent=2)


def test_administrator_resource_lifecycle(page, demo_records, live_server):
    base = live_server.url
    resource = demo_records["resource"]
    sign_in(page, base, demo_records["administrator"].email)
    page.goto(base + reverse("practicals:resource_edit", args=[resource.pk]))
    page.get_by_label("Title", exact=True).fill("Updated synthetic resource")
    page.get_by_role("button", name="Save draft resource", exact=True).click()
    resource.refresh_from_db()
    assert resource.title == "Updated synthetic resource" and resource.status == "DRAFT"
    page.get_by_role("row").filter(has_text=resource.title).get_by_role("button", name="Approve", exact=False).click()
    resource.refresh_from_db()
    assert resource.status == "APPROVED"
    page.goto(base + reverse("practicals:resource_availability", args=[resource.pk, "disable"]))
    page.get_by_label("Reason", exact=True).fill("Synthetic maintenance check")
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Confirm disable", exact=True).click()
    resource.refresh_from_db()
    assert resource.status == "ARCHIVED"
    page.goto(base + reverse("practicals:resource_availability", args=[resource.pk, "restore"]))
    page.get_by_label("Reason", exact=True).fill("Synthetic check completed")
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Confirm restore", exact=True).click()
    resource.refresh_from_db()
    assert resource.status == "DRAFT" and resource.approved_by is None


def test_administrator_notice_preview_and_delivery(page, demo_records, live_server):
    base = live_server.url
    sign_in(page, base, demo_records["administrator"].email)
    page.goto(base + reverse("core:notice_create"))
    page.get_by_label("Title", exact=True).fill("Synthetic browser notice")
    page.get_by_label("Message", exact=True).fill("Example platform guidance.")
    page.get_by_label("Audience", exact=True).select_option("STUDENT")
    page.get_by_label("Link", exact=True).fill("/help/")
    page.get_by_role("button", name="Save and preview notice", exact=True).click()
    notice = AdministratorNotice.objects.get(title="Synthetic browser notice")
    assert not notice.deliveries.exists()
    page.get_by_role("button", name="Confirm and send notice", exact=True).click()
    assert notice.deliveries.filter(recipient=demo_records["student"]).exists()
    sign_out(page)
    sign_in(page, base, demo_records["student"].email)
    page.goto(base + reverse("core:notification_list"))
    page.get_by_role("link").filter(has_text="Synthetic browser notice").click()
    expect(page).to_have_url(base + "/help/")
    assert notice.deliveries.get(recipient=demo_records["student"]).read_at is not None


def test_support_response_is_visible_to_request_owner(page, demo_records, live_server):
    base = live_server.url
    sign_in(page, base, demo_records["student"].email)
    page.goto(base + "/help/")
    page.get_by_label("Subject", exact=True).fill("Synthetic browser support")
    page.get_by_label("Message", exact=True).fill("Example practical question.")
    page.get_by_role("button", name="Submit support request", exact=True).click()
    ticket = SupportRequest.objects.get(subject="Synthetic browser support")
    sign_out(page)
    sign_in(page, base, demo_records["administrator"].email)
    page.goto(base + reverse("core:support_review", args=[ticket.pk]))
    page.get_by_label("Status", exact=True).select_option("RESOLVED")
    page.get_by_label("Response", exact=True).fill("Synthetic answer: open the assigned task.")
    page.get_by_role("button", name="Save response and notify account", exact=True).click()
    sign_out(page)
    sign_in(page, base, demo_records["student"].email)
    page.goto(base + "/help/")
    expect(page.get_by_text("Synthetic answer: open the assigned task.", exact=True)).to_be_visible()
