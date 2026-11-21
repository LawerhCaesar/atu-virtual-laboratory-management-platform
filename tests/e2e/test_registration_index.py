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
    page.get_by_label('Faculty / school',exact=True).select_option('engineering')
    page.get_by_label('Department',exact=True).select_option('mechanical')
    page.get_by_label('Programme',exact=True).select_option({'HND':'hnd-automobile-engineering','BTECH':'btech-automotive-engineering','MTECH':'mtech-automotive-engineering'}[course])
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
    page.get_by_label('Faculty / school',exact=True).select_option('engineering');page.get_by_label('Department',exact=True).select_option('mechanical')
    page.get_by_label('Full name',exact=True).fill('New Lecturer');page.get_by_label('Email',exact=True).fill('lecturer-new@example.edu')
    page.get_by_label('Password',exact=True).fill('GoodSecure!742');page.get_by_label('Password confirmation',exact=True).fill('GoodSecure!742')
    page.get_by_role('button',name='Submit registration',exact=True).click()
    expect(page.get_by_role('heading',name='Registration received',exact=True)).to_be_visible()
    lecturer=User.objects.get(email='lecturer-new@example.edu');assert lecturer.index_number is None

@pytest.mark.parametrize('width',[1440,390])
def test_academic_choices_filter_and_clear_stale_programmes(page,live_server,width):
    page.set_viewport_size({'width':width,'height':1000})
    page.goto(live_server.url+'/accounts/register/')
    page.get_by_label('Course',exact=True).select_option('MTECH')
    faculty=page.get_by_label('Faculty / school',exact=True)
    department=page.get_by_label('Department',exact=True)
    programme=page.get_by_label('Programme',exact=True)
    faculty.select_option('engineering');department.select_option('mechanical')
    programme.select_option('mtech-food-and-bioprocess-engineering')
    assert not programme.locator('option[value="hnd-automobile-engineering"]').count()
    faculty.select_option('business')
    expect(department).to_have_value('');expect(programme).to_have_value('')
    assert not department.locator('option[value="mechanical"]').count()
    department.select_option('management');programme.select_option('mtech-administration-and-management')
    faculty.select_option('engineering');department.select_option('mechanical')
    page.get_by_label('Course',exact=True).select_option('BTECH')
    programme.select_option('btech-chemical-and-process-engineering')
    expect(page.locator('#registration-programme-status')).to_contain_text('department needs confirmation')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')


def test_academic_registration_without_the_filter_script(page,live_server):
    page.route('**/static/js/registration.js',lambda route:route.abort())
    page.goto(live_server.url+'/accounts/register/')
    page.get_by_label('Full name',exact=True).fill('No Script Student')
    page.get_by_label('Course',exact=True).select_option('MTECH')
    page.get_by_label('Faculty / school',exact=True).select_option('engineering')
    page.get_by_label('Department',exact=True).select_option('mechanical')
    page.get_by_label('Programme',exact=True).select_option('mtech-food-and-bioprocess-engineering')
    page.get_by_label('Username (index number)',exact=True).fill('01181429M')
    page.get_by_label('Email',exact=True).fill('no-script@example.edu')
    page.get_by_label('Password',exact=True).fill('GoodSecure!742')
    page.get_by_label('Password confirmation',exact=True).fill('GoodSecure!742')
    page.get_by_role('button',name='Submit registration',exact=True).click()
    expect(page.get_by_role('heading',name='Registration received',exact=True)).to_be_visible()
    user=User.objects.get(email='no-script@example.edu')
    assert user.registration_academics['programme_id']=='mtech-food-and-bioprocess-engineering'
    assert user.approval_status=='PENDING'
