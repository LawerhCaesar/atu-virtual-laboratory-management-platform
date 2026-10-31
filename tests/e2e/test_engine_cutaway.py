"""Regression: section-specific engine processes replace the removed whole-engine cutaway."""
import pytest
from playwright.sync_api import expect
from test_engine_demo import open_engine
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]

def test_engine_sections_do_not_load_whole_engine_cutaway(page,demo_records,live_server):
 page.emulate_media(reduced_motion='reduce')
 requests=[];page.on('request',lambda request:requests.append(request.url))
 open_engine(page,demo_records,live_server)
 expect(page.locator('#engine-cutaway')).to_have_count(0)
 expect(page.locator('#engine-demo canvas')).to_have_count(0)
 for title in ['Fuel and injection','Idle and ignition','Cooling','Start and run']:
  page.get_by_role('button',name=title,exact=True).click()
  expect(page.locator('#engine-system-title')).to_have_text(title)
  expect(page.locator('#engine-schematic svg')).to_be_visible()
 page.get_by_role('button',name='Step 0.05 s',exact=True).click()
 expect(page.locator('#engine-time')).to_have_text('0.05')
 assert not any('cutaway.bundle' in url for url in requests)
