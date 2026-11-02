import re
from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
ROUTES=[('/virtual-lab/ice/coolant-temperature/','.ect-help'),('/virtual-lab/engine-live-data/','.engine-info'),('/virtual-lab/bev/electric-motor-drive/','.motor-info'),('/virtual-lab/bev/battery-energy-management/','.battery-info'),('/virtual-lab/ice/authenticated-engine-starting/','.ya-help')]
@pytest.mark.parametrize('path,wrap',ROUTES)
@pytest.mark.parametrize('width',[1440,390])
def test_click_again_dismisses_even_while_hovered_and_focused(page,demo_records,live_server,path,wrap,width):
 errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
 page.set_viewport_size({'width':width,'height':1000});page.emulate_media(reduced_motion='reduce')
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click();page.goto(live_server.url+path);page.locator('#tour-close').click()
 button=page.locator(wrap+' > button:visible').first;expect(button).to_be_visible();button.scroll_into_view_if_needed();button.hover();button.focus();expect(button).to_have_attribute('aria-expanded','false')
 button.click();expect(button).to_have_attribute('aria-expanded','true');tip=button.evaluate('b=>b.getAttribute("aria-controls")');popup=page.locator('[id="'+tip+'"]');expect(popup).to_be_visible()
 button.click();expect(button).to_have_attribute('aria-expanded','false');expect(popup).to_be_hidden();button.hover();button.focus();expect(popup).to_be_hidden()
 button.press('Enter');expect(popup).to_be_visible();page.keyboard.press('Escape');expect(popup).to_be_hidden();expect(button).to_be_focused()
 button.press('Space');expect(popup).to_be_visible();page.locator('h1').first.click();expect(popup).to_be_hidden()
 buttons=page.locator(wrap+' > button:visible');second=buttons.nth(1);button.click();second.click();expect(button).to_have_attribute('aria-expanded','false');expect(second).to_have_attribute('aria-expanded','true');second.click();expect(second).to_have_attribute('aria-expanded','false')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors

def test_real_touch_tap_twice(page,demo_records,live_server):
 session=page.context.new_cdp_session(page);session.send('Emulation.setTouchEmulationEnabled',{'enabled':True,'maxTouchPoints':5})
 page.set_viewport_size({'width':390,'height':900});page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click();page.goto(live_server.url+'/virtual-lab/ice/coolant-temperature/');page.locator('#tour-close').click()
 button=page.locator('.ect-help > button:visible').first;button.scroll_into_view_if_needed()
 def tap():
  box=button.bounding_box();point={'x':box['x']+box['width']/2,'y':box['y']+box['height']/2};session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 tap();expect(button).to_have_attribute('aria-expanded','true');tap();expect(button).to_have_attribute('aria-expanded','false')

def test_future_module_late_shadow_root_uses_same_behavior(page,demo_records,live_server):
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click();page.goto(live_server.url+'/virtual-lab/');page.evaluate("""()=>{const h=document.createElement('section');document.querySelector('main').prepend(h);window.futureHost=h;}""")
 page.evaluate("""()=>{const s=futureHost.attachShadow({mode:'open'});s.innerHTML='<style>.help span{display:none}.help:hover span,.help:focus-within span{display:block}</style><div class="help"><button id="future-help-button" aria-describedby="future-help-tip">i</button><span id="future-help-tip" role="tooltip">A future learning module definition.</span></div>';}""")
 button=page.locator('#future-help-button');button.hover();expect(button).to_have_attribute('aria-expanded','false');tip=page.locator('#future-help-tip');expect(tip).to_be_hidden();button.click();expect(tip).to_be_visible();button.click();expect(tip).to_be_hidden()
