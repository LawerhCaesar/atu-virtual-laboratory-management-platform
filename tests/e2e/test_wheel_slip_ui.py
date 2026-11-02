import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def open_module(page, demo_records, live_server):
    page.goto(live_server.url + "/accounts/login/")
    page.get_by_label("Email address or index number", exact=True).fill(demo_records["student"].email)
    page.get_by_label("Password", exact=True).fill("DemoPass!742")
    page.get_by_role("button", name="Sign in", exact=True).click()
    page.get_by_role("link", name="Virtual laboratory", exact=True).click()
    page.get_by_role("link", name="Enter VD environment", exact=True).click()
    page.get_by_role("link", name="Open Wheel-Slip Control Using ABS and TCS", exact=True).click()
    expect(page.locator("#ws-fields input[type=number]")).to_have_count(14)


def run(page):
    page.get_by_role("button", name="Run simulation", exact=True).click()
    expect(page.locator("#ws-status")).to_contain_text("Calculation complete", timeout=20000)


def test_controls_worker_playback_comparison_and_exports(page, demo_records, live_server):
    open_module(page, demo_records, live_server)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    run(page)
    expect(page.locator("#ws-result-note")).to_contain_text("12,001 full-resolution samples")
    assert float(page.locator('[data-ws-metric="absActiveTimeS"]').inner_text()) > 0
    assert page.locator("#ws-charts svg polyline").count() == 11
    with page.expect_download() as download:
        page.get_by_role("button", name="Export JSON", exact=True).click()
    payload = json.loads(Path(download.value.path()).read_text())
    assert payload["config"]["timeStepS"] == .001
    assert len(payload["samples"]) == 12001
    page.locator("#ws-scrub").fill("2")
    expect(page.locator("#ws-controller")).to_contain_text("ABS")
    page.select_option("#ws-zoom", "4")
    with page.expect_download() as chart_download:
        page.get_by_role("button", name="Download Vehicle and wheel speed chart SVG", exact=True).click()
    assert "<svg" in Path(chart_download.value.path()).read_text()
    with page.expect_download() as csv_download:
        page.get_by_role("button", name="Export CSV", exact=True).click()
    assert "# config.timeStepS,0.001" in Path(csv_download.value.path()).read_text()
    page.get_by_role("button", name="Play", exact=True).click()
    expect(page.get_by_role("button", name="Pause", exact=True)).to_be_enabled()
    page.get_by_role("button", name="Pause", exact=True).click()
    page.select_option("#ws-preset", label="Launch without TCS")
    page.get_by_role("button", name="Load preset", exact=True).click()
    expect(page.get_by_label("TCS enabled", exact=True)).not_to_be_checked()
    expect(page.get_by_role("button", name="Export JSON", exact=True)).to_be_disabled()
    run(page)
    assert float(page.locator('[data-ws-metric="peakDriveSlip"]').inner_text()) > .9
    expect(page.locator('[data-ws-metric="tcsActiveTimeS"]')).to_have_text("0.00")
    page.get_by_role("button", name="Reset", exact=True).click()
    page.get_by_label("Road friction coefficient (ratio)", exact=True).fill("0")
    expect(page.locator("#ws-error-roadMu")).to_contain_text("between")
    expect(page.get_by_role("button", name="Run simulation", exact=True)).to_be_disabled()
    assert errors == []


def test_maximum_duration_retains_full_resolution(page, demo_records, live_server):
    open_module(page, demo_records, live_server)
    page.get_by_label("Simulation duration (s)", exact=True).fill("60")
    run(page)
    expect(page.locator("#ws-result-note")).to_contain_text("60,001 full-resolution samples")
    expect(page.get_by_role("button", name="Export CSV", exact=True)).to_be_enabled()


@pytest.mark.parametrize("width", [1280, 390])
def test_visuals_and_responsive_layout(page, demo_records, live_server, width):
    page.set_viewport_size({"width": width, "height": 900})
    open_module(page, demo_records, live_server)
    run(page)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.add_script_tag(path="node_modules/axe-core/axe.min.js")
    result = page.evaluate("async () => await axe.run(document.querySelector('main'), {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})")
    assert not result["violations"], json.dumps(result["violations"], indent=2)
    page.locator("#ws-scrub").fill("2")
    expect(page.locator("#ws-controller")).to_contain_text("ABS active")
    dest = Path("test-results/wheel-slip")
    dest.mkdir(parents=True, exist_ok=True)
    page.locator("#ws-scene").screenshot(path=str(dest / f"scene-{width}.png"))
    page.locator(".ws-visual").screenshot(path=str(dest / f"visual-{width}.png"))
    page.locator("#ws-plots").screenshot(path=str(dest / f"plots-{width}.png"))
    page.locator("#ws-fields").screenshot(path=str(dest / f"inputs-{width}.png"))
    page.screenshot(path=str(dest / f"page-{width}.png"), full_page=True)

def test_mechanical_corner_feedback_and_pump_cue(page,demo_records,live_server):
    open_module(page,demo_records,live_server)
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    run(page)
    expect(page.locator('#ws-corner canvas')).to_be_visible(timeout=30000)
    assert page.locator('#ws-car').count()==0
    sample=page.evaluate("WheelSlipLab.result.samples.find(s=>s.controllerMode===3)")
    page.locator('#ws-scrub').fill(str(sample['timeS']))
    expect(page.locator('#ws-scene')).to_have_attribute('data-pump','true')
    expect(page.locator('#ws-corner')).to_have_attribute('data-mode','3')
    expect(page.locator('#ws-corner')).to_have_attribute('data-pump','true')
    assert float(page.locator('#ws-scene').get_attribute('data-output-time'))-float(page.locator('#ws-scene').get_attribute('data-sensor-time'))==pytest.approx(.001)
    expect(page.locator('#ws-loop-readings')).to_contain_text('illustrative return-pump motion ON')
    page.get_by_role('button',name='ABS modulator',exact=True).click()
    expect(page.locator('#ws-corner')).to_have_attribute('data-camera','modulator')
    page.locator('#ws-scene').screenshot(path='test-results/wheel-slip/modulator-release.png')
    page.get_by_role('button',name='Complete corner',exact=True).click()
    page.locator('#ws-scene').screenshot(path='test-results/wheel-slip/corner-release.png')
    page.get_by_role('button',name='Explain Brake step time',exact=True).click()
    button=page.get_by_role('button',name='Explain Brake step time',exact=True)
    expect(button).to_have_attribute('aria-expanded','true');button.click();expect(button).to_have_attribute('aria-expanded','false')
    page.select_option('#ws-preset',label='TCS low-friction launch');page.locator('#ws-load').click();run(page)
    sample=page.evaluate("WheelSlipLab.result.samples.find(s=>s.controllerMode===-3)")
    page.locator('#ws-scrub').fill(str(sample['timeS']))
    expect(page.locator('#ws-scene')).to_have_attribute('data-mode','-3');expect(page.locator('#ws-scene')).to_have_attribute('data-pump','false')
    expect(page.locator('#ws-loop-readings')).to_contain_text('TCS reduces drive torque here')
    page.locator('#ws-learning-guide > summary').click()
    link=page.get_by_role('link',name='Download complete learning guide (PDF)')
    response=page.request.get(live_server.url+link.get_attribute('href'));assert response.status==200;assert response.body().startswith(b'%PDF')
    page.locator('#ws-reset').click();expect(page.locator('#ws-scene')).to_have_attribute('data-valid','false')
    expect(page.locator('#ws-loop-readings')).to_contain_text('—')
    assert not errors,errors


def test_numerical_feedback_survives_webgl_unavailable(page,demo_records,live_server):
    page.add_init_script("const old=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return /webgl/.test(kind)?null:old.call(this,kind,...args)}")
    open_module(page,demo_records,live_server);run(page)
    expect(page.locator('#ws-corner')).to_have_attribute('data-fallback','true',timeout=30000)
    page.locator('#ws-scrub').fill('2')
    expect(page.locator('#ws-scene')).to_have_attribute('data-valid','true')
    expect(page.locator('#ws-loop-readings')).to_contain_text('rad/s')
    expect(page.locator('#ws-signal-loop')).to_contain_text('ABS')
