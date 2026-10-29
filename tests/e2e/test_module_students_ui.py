from pathlib import Path
import pytest
from playwright.sync_api import expect
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]
@pytest.mark.parametrize('width',[1440,390])
def test_student_profile_layout(page,demo_records,live_server,width):
 page.set_viewport_size({'width':width,'height':1000})
 page.goto(live_server.url+'/accounts/login/');page.get_by_label('Email address',exact=True).fill(demo_records['student'].email);page.get_by_label('Password',exact=True).fill('DemoPass!742');page.get_by_role('button',name='Sign in',exact=True).click()
 page.goto(live_server.url+'/virtual-lab/ice/coolant-temperature/')
 page.locator('#tour-close').click()
 card=page.locator('.module-student');expect(card).to_contain_text('David Amachie');card.scroll_into_view_if_needed()
 Path('test-results/module-students').mkdir(parents=True,exist_ok=True)
 page.screenshot(path=f'test-results/module-students/profile-{width}.png')
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.add_script_tag(path='node_modules/axe-core/axe.min.js')
 issues=page.evaluate("async()=> (await axe.run(document.querySelector('.module-student'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations")
 assert not issues,issues
