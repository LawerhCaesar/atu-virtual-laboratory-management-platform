from pathlib import Path
import pytest
from playwright.sync_api import expect
from apps.accounts.models import User
pytestmark=[pytest.mark.e2e,pytest.mark.django_db(transaction=True)]

@pytest.mark.parametrize('course,suffix',[('HND','D'),('BTECH','B'),('MTECH','M')])
def test_course_index_registration_and_sign_in(page,live_server,course,suffix):
    page.emulate_media(reduced_motion='reduce');page.goto(live_server.url+'/accounts/register/')
    expect(page).to_have_title('Register | ATU Virtual Laboratory')
    page.get_by_label('Full name',exact=True).fill('New Student')
    page.get_by_label('Course',exact=True).select_option(course)
    index=page.get_by_label('Username (index number)',exact=True)
    expect(index).to_have_attribute('maxlength','9');expect(index).to_have_attribute('pattern','[0-9]{8}'+suffix)
    index.fill('01181429'+suffix.lower());expect(index).to_have_value('01181429'+suffix)
    page.get_by_label('Email',exact=True).fill('new-student@example.edu')
    page.get_by_label('Password',exact=True).fill('GoodSecure!742')
    page.get_by_label('Password confirmation',exact=True).fill('GoodSecure!742')
    page.get_by_role('button',name='Submit registration',exact=True).click()
    expect(page.get_by_role('heading',name='Registration received',exact=True)).to_be_visible()
    user=User.objects.get(email='new-student@example.edu');assert user.index_number=='01181429'+suffix
    assert user.approval_status=='PENDING'
    user.approval_status='ACTIVE';user.save()
    page.goto(live_server.url+'/accounts/login/')
    page.get_by_label('Email address or index number',exact=True).fill(user.index_number.lower())
    page.get_by_label('Password',exact=True).fill('GoodSecure!742');page.get_by_role('button',name='Sign in',exact=True).click()
    expect(page).to_have_url(live_server.url+'/dashboard/')

@pytest.mark.parametrize('width',[1440,390])
def test_format_feedback_course_correction_and_accessibility(page,live_server,width):
    page.set_viewport_size({'width':width,'height':1000});page.goto(live_server.url+'/accounts/register/')
    page.get_by_label('Course',exact=True).select_option('HND');index=page.get_by_label('Username (index number)',exact=True)
    index.fill('01181429D');page.get_by_label('Course',exact=True).select_option('MTECH')
    expect(index).to_have_value('01181429M');expect(page.locator('#registration-index-status')).to_contain_text('9/9')
    index.fill('Z1181429M');assert not index.evaluate('e=>e.checkValidity()')
    index.fill('01181429');assert not index.evaluate('e=>e.checkValidity()')
    index.fill('01181429M');assert index.evaluate('e=>e.checkValidity()')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.add_script_tag(path='node_modules/axe-core/axe.min.js')
    issues=page.evaluate("async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations")
    assert not issues,issues
    folder=Path('test-results/registration-index');folder.mkdir(parents=True,exist_ok=True);page.locator('.form-shell').screenshot(path=str(folder/f'course-index-{width}.png'))
    page.get_by_label('Role',exact=True).select_option('LECTURER')
    expect(index).not_to_be_visible();expect(index).to_be_disabled()
    page.get_by_label('Full name',exact=True).fill('New Lecturer');page.get_by_label('Email',exact=True).fill('lecturer-new@example.edu')
    page.get_by_label('Password',exact=True).fill('GoodSecure!742');page.get_by_label('Password confirmation',exact=True).fill('GoodSecure!742')
    page.get_by_role('button',name='Submit registration',exact=True).click()
    expect(page.get_by_role('heading',name='Registration received',exact=True)).to_be_visible()
    lecturer=User.objects.get(email='lecturer-new@example.edu');assert lecturer.index_number is None
