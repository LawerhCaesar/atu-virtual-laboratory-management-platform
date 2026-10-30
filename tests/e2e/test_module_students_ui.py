from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('path,name',[
 ('/virtual-lab/brakelab/','Ebenezer Wilson'),
 ('/virtual-lab/ice/authenticated-engine-starting/','Emmanuel Yankson Sackey'),
 ('/virtual-lab/hev/p2-full-parallel-hybrid/','Lawrence Andoh'),
])
@pytest.mark.parametrize('width',[1440,390])
def test_student_profile_layout(page,demo_records,live_server,width,path,name):
 page.set_viewport_size({'width':width,'height':1000})
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click()
 page.goto(live_server.url+path)
 page.locator('#tour-close').click()
 card=page.locator('.module-student');expect(card).to_contain_text(name);card.scroll_into_view_if_needed()
 if name.startswith('Emmanuel'):
  expect(card.locator('.module-student-portrait')).to_have_count(0)
  expect(card.get_by_role('heading',name='About the student')).to_have_count(0)
 if name.startswith('Lawrence'):expect(card).to_contain_text('torque-split dynamics')
 Path('test-results/module-students').mkdir(parents=True,exist_ok=True)
 page.screenshot(path=f'test-results/module-students/profile-{name.split()[0]}-{width}.png')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js')
 issues=page.evaluate("async()=> (await axe.run(document.querySelector('.module-student'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
 assert not issues,issues
