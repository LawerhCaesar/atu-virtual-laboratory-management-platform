import json
import math
import pytest
from django.urls import reverse
from django.test import Client
from apps.accounts.models import User
from apps.core.simulations import p2_hybrid as m


@pytest.mark.parametrize('torque,motor,engine,wheel,power,current,voltage,loss,energy,loss_energy,efficiency,delta',[
 (60,60,0,212.76,18472.50,53.142,347.609,127.082,153.937,1.059,99.317,1.292),
 (140,70,70,496.44,21467.91,61.828,347.218,172.024,178.899,1.434,99.205,1.503),
 (240,120,120,851.04,36445.,105.561,345.250,501.443,303.708,4.179,98.643,2.566),
])
def test_p2_supplied_reference_targets(torque,motor,engine,wheel,power,current,voltage,loss,energy,loss_energy,efficiency,delta):
    request={'requested_torque_nm':torque}
    r=m.simulate(request);s=r['summary']
    for key,expected,tol in [('motor_torque_nm',motor,.02),('engine_torque_nm',engine,.02),('requested_wheel_torque_nm',wheel,.02),('actual_wheel_torque_nm',wheel,.02),('battery_terminal_power_w',power,2),('battery_current_a',current,.02),('battery_terminal_voltage_v',voltage,.02),('battery_internal_loss_power_w',loss,2),('battery_energy_used_wh',energy,.03),('battery_loss_energy_wh',loss_energy,.03),('battery_efficiency_percent',efficiency,.02),('delta_soc_percent',delta,.02)]:
        assert s[key]==pytest.approx(expected,abs=tol),key
    assert s['torque_rmse_nm']==pytest.approx(0,abs=1e-10)
    assert s['battery_current_rms_a']==pytest.approx(current,abs=.02)
    assert len(r['time_series'])==3001
    assert len(s)==23 and set(s)=={s['key'] for s in m.model_info()['signals']}
    assert r==m.simulate(request)


def test_p2_equations_and_boundaries():
    p=m.Parameters()
    for torque,regime,share in [(0,1,1),(79.99,1,1),(80,2,.5),(199.99,2,.5),(200,3,.5)]:
        assert m.classify_regime(torque,p)==(regime,share)
    inputs,_,_=m.validate_inputs({})
    s,limits=m.calculate_state(inputs,p,.7)
    assert not limits
    assert s['motor_speed_rad_s']==pytest.approx(2500*2*math.pi/60)
    assert s['motor_mechanical_power_w']==pytest.approx(70*2500*2*math.pi/60)
    assert s['battery_terminal_power_w']==pytest.approx(s['motor_mechanical_power_w']/(.92*.95)+500)
    assert s['battery_terminal_voltage_v']*s['battery_current_a']==pytest.approx(s['battery_terminal_power_w'])
    assert s['battery_internal_loss_power_w']==pytest.approx(s['battery_current_a']**2*.045)
    r=m.simulate({'duration_s':.025,'time_step_s':.01})
    assert [s['time_s'] for s in r['time_series']]==[0,.01,.02,.025]
    assert r['summary']['battery_energy_used_wh']==pytest.approx(r['summary']['battery_terminal_power_w']*.025/3600)
    assert r['time_series'][0]['battery_current_rms_a']==0
    assert r['time_series'][0]['battery_efficiency_percent']==0


def test_p2_protection_and_limits():
    low=m.simulate({'requested_torque_nm':60,'initial_soc':.25})
    s=low['summary'];assert s['motor_torque_nm']==0 and s['engine_torque_nm']==60 and s['clutch_state']==1
    assert s['battery_terminal_power_w']==500 and low['active_limits']
    high=m.simulate({'requested_torque_nm':400,'motor_speed_rpm':6000})
    s=high['summary'];assert s['motor_torque_nm']==pytest.approx(35000/(6000*math.pi/30+.001))
    assert s['engine_torque_nm']==142 and s['torque_rmse_nm']>0
    assert s['motor_mechanical_power_w']<35000
    at=m.simulate({'requested_torque_nm':60,'initial_soc':.3,'duration_s':.02})
    assert at['time_series'][0]['clutch_state']==0 and at['time_series'][0]['motor_torque_nm']==60
    assert at['time_series'][1]['motor_torque_nm']==0 and at['time_series'][1]['clutch_state']==1
    extreme=m.simulate({'initial_soc':.01,'parameter_overrides':{'battery_nominal_energy_wh':.01,'battery_open_circuit_voltage_v':1,'battery_internal_resistance_ohm':1}})
    assert extreme['summary']['soc_percent']==0
    assert all(0<=r['soc_percent']<=100 for r in extreme['time_series'])
    assert any('discriminant' in w for w in extreme['warnings'])
    assert any('depleted' in w for w in extreme['warnings'])
    assert all(math.isfinite(v) for r in extreme['time_series'] for v in r.values())


@pytest.mark.parametrize('payload',[
 {'requested_torque_nm':-1},{'motor_speed_rpm':-1},{'initial_soc':1.1},{'initial_soc':True},
 {'requested_torque_nm':float('nan')},{'duration_s':0},{'time_step_s':0},
 {'requested_torque_nm':10**400},{'parameter_overrides':{'motor_efficiency':0}},
 {'parameter_overrides':{'battery_internal_resistance_ohm':0}},
 {'parameter_overrides':{'low_torque_threshold_nm':200,'high_torque_threshold_nm':100}},
 {'duration_s':600,'time_step_s':.001},{'typo':1},{'parameter_overrides':{'typo':1}},
 {'parameter_overrides':[]},{'case_name':' '},[],None,
])
def test_p2_invalid_requests(payload):
    with pytest.raises(m.ValidationError):m.simulate(payload)


def test_p2_comparison_reuses_core_and_bounds_work():
    cases=[{'requested_torque_nm':t,'case_name':name} for t,name in [(60,'Low'),(140,'Medium'),(240,'High')]]
    result=m.compare({'cases':cases})
    assert result['cases']==[m.simulate(c) for c in cases]
    assert result['summary_rows'][2]['battery_energy_used_wh']>result['summary_rows'][0]['battery_energy_used_wh']
    for invalid in [{},{'cases':[{}]},{'cases':[{},{}]},{'cases':cases*2}, {'cases':cases,'extra':1}, {'cases':[dict(c,duration_s=600) for c in cases]}]:
        with pytest.raises(m.ValidationError):m.compare(invalid)


@pytest.fixture
def p2_user(db):
    return User.objects.create_user(email='p2-qa@example.test',full_name='P2 QA',password='SyntheticPass!742',role='STUDENT',approval_status='ACTIVE')


@pytest.mark.django_db
def test_p2_routes_schema_errors_and_csrf(client,p2_user):
    for name in ['p2_hybrid','p2_info','p2_simulate','p2_compare']:
        assert client.get(reverse('core:'+name)).status_code==302
    client.force_login(p2_user)
    page=client.get(reverse('core:p2_hybrid'));assert page.status_code==200
    assert b'core:p2_hybrid' in page.content and b'Genesis GV70' in page.content
    info=client.get(reverse('core:p2_info')).json();assert len(info['scope_groups'])==7
    url=reverse('core:p2_simulate')
    assert client.get(url).status_code==405
    result=client.post(url,data=json.dumps({'duration_s':.02}),content_type='application/json')
    assert result.status_code==200 and len(result.json()['time_series'])==3
    for data in ['{','[]','{"initial_soc":NaN}','{"requested_torque_nm":-1}']:
        response=client.post(url,data=data,content_type='application/json')
        assert response.status_code==400 and response.json()['errors']
    assert client.post(url,data=' '*65537,content_type='application/json').status_code==413
    result=client.post(reverse('core:p2_compare'),data=json.dumps({'cases':[{'case_name':'A','duration_s':.01},{'case_name':'B','requested_torque_nm':60,'duration_s':.01}]}),content_type='application/json')
    assert result.status_code==200 and len(result.json()['summary_rows'])==2
    secure=Client(enforce_csrf_checks=True);secure.force_login(p2_user)
    assert secure.post(url,data='{}',content_type='application/json').status_code==403
    secure.get(reverse('core:p2_hybrid'))
    assert secure.post(url,data='{"duration_s":0.01}',content_type='application/json',HTTP_X_CSRFTOKEN=secure.cookies['csrftoken'].value).status_code==200
    p2_user.approval_status='PENDING';p2_user.save()
    assert client.get(reverse('core:p2_info')).status_code==403


@pytest.mark.parametrize('role',['ADMIN','LECTURER'])
@pytest.mark.django_db
def test_p2_other_active_roles(client,p2_user,role):
    p2_user.role=role;p2_user.save();client.force_login(p2_user)
    assert client.get(reverse('core:p2_hybrid')).status_code==200
    assert client.get(reverse('core:p2_info')).status_code==200
