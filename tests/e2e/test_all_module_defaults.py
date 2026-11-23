import json
from pathlib import Path
import pytest
from django.urls import reverse
from playwright.sync_api import expect
from apps.core.laboratory import SYSTEM_MODELS
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
def open_calibration_controls(page,route):
 if route=='core:yankson':
  page.locator('#ye-record').wait_for(state='attached')
  page.locator('#ys-input-advanced').evaluate('e=>e.open=true')
  page.locator('#lab-master-reset').evaluate("e=>e.closest('details').open=true")
 page.locator('details').evaluate_all("nodes=>nodes.forEach(d=>{if(d.querySelector('input[type=number]'))d.open=true;})")
def test_all_modules_have_editable_controls_and_master_defaults(page,demo_records,live_server):
 page.emulate_media(reduced_motion='reduce');page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address or index number',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click();audit=[]
 for models in SYSTEM_MODELS.values():
  for model in models:
   path=reverse(model['route_name']);page.goto(live_server.url+path);page.locator('#tour-close').click();open_calibration_controls(page,model['route_name']);expect(page.locator('#lab-master-reset')).to_be_visible();expect(page.locator('[data-lab-learning] > summary')).to_have_text('Learning guide and reference evidence');expect(page.locator('#lab-guide-print')).to_have_count(1)
   open_calibration_controls(page,model['route_name'])
   fields=page.locator('input[type=number]:visible:not([disabled])');field=fields.first;expect(field).to_be_visible(timeout=20000);baseline=field.input_value();assert not field.get_attribute('readonly');assert page.locator('input[type=number][readonly]').count()==0
   field.fill(str(float(baseline)+1));assert field.input_value()!=baseline
   with page.expect_navigation(wait_until='domcontentloaded'):page.locator('#lab-master-reset').click()
   open_calibration_controls(page,model['route_name'])
   fresh=page.locator('input[type=number]:visible:not([disabled])').first;expect(fresh).to_have_value(baseline,timeout=20000)
   audit.append({'module':model['title'],'route':path,'resetValue':baseline,'numericControls':page.locator('input[type=number]').count(),'readOnlyNumericControls':0})
 assert len(audit)==14
 out=Path('test-results/calibration-audit');out.mkdir(parents=True,exist_ok=True);(out/'all-modules.json').write_text(json.dumps(audit,indent=2))
