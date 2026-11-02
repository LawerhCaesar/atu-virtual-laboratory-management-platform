import json,time,subprocess
from pathlib import Path
from unittest.mock import patch
import pytest
from django.test import Client
from apps.accounts.models import User
from apps.core.models import LabDeviceCredential,StartingExercise
pytestmark=pytest.mark.django_db
@pytest.fixture
def staff():return User.objects.create_user(email='labstaff@example.test',password='TestOnly!392',role=User.Role.LECTURER,approval_status=User.ApprovalStatus.ACTIVE)
@pytest.fixture
def student():return User.objects.create_user(email='labstudent@example.test',password='TestOnly!392',approval_status=User.ApprovalStatus.ACTIVE)
def config():return {'electrical':{'batteryV':12.6,'wireOhm':.01,'starterOhm':.06,'fuseA':250,'canHighV':3.5,'canLowV':1.5,'terminationOhm':60,'coilOhm':80},'operating':{'extraLoadNm':0,'overrideRPM':0},'parameters':[.01,.15,1.5,10,3,600,.2,.1,.02,1,0,50,8000,.25,8,25,.28,3,.35,100,.5,256],'wires':dict.fromkeys(['power','reference','interlock','match','contact','voice','canh','canl','transceiver','starter','run'],True),'faults':{k:k in ['powerGood','interlockOK','monitorConnected','ignitionAllowed'] for k in ['powerGood','interlockOK','monitorConnected','ignitionAllowed','CANdrop','badID','badDLC','badRange','useRPMoverride']}}
BASE='/virtual-lab/ice/starting/'
def post(client,path,data={}):return client.post(BASE+path,data=json.dumps(data),content_type='application/json',secure=True)
def test_csrf_role_and_bounded_exercises(staff,student):
 strict=Client(enforce_csrf_checks=True);strict.force_login(staff);assert post(strict,'exercises/save/').status_code==403
 c=Client();c.force_login(student);assert post(c,'exercises/save/',{'title':'x','configuration':config()}).status_code==403
 c.force_login(staff)
 for bad in [[],{'title':8},{'title':'bad','configuration':dict(config(),electrical=8)},{'title':'bad','configuration':dict(config(),operating={'extraLoadNm':-1,'overrideRPM':0})},{'title':'bad','configuration':dict(config(),parameters=[1]*22)}]:assert post(c,'exercises/save/',bad).status_code==400
 r=post(c,'exercises/save/',{'title':'CAN fault','instructions':'Repair termination','configuration':config()});assert r.status_code==201
 exercise=StartingExercise.objects.get(pk=r.json()['id']);assert exercise.owner==staff
 c.force_login(student);assert c.get(BASE+'exercises/').json()=={'items':[]};assert c.get(BASE+f'exercises/{exercise.pk}/').json()['configuration']==config()
 student.approval_status=User.ApprovalStatus.SUSPENDED;student.save();assert c.get(BASE+f'exercises/{exercise.pk}/').status_code==403

def test_device_challenge_expiry_replay_and_untrusted_payload(staff):
 c=Client();c.force_login(staff)
 assert post(c,'device/verify/options/').status_code==400
 assert post(c,'device/register/options/').status_code==200
 response=post(c,'device/register/complete/',{'id':'fake','rawId':'fake','type':'public-key','response':{}});assert response.status_code==400;assert not LabDeviceCredential.objects.exists()
 assert post(c,'device/register/complete/').status_code==400
 assert post(c,'device/register/options/').status_code==200
 session=c.session;session['starting_ceremony']['created']=time.time()-121;session.save();assert post(c,'device/register/complete/').status_code==400
 assert post(c,'device/register/options/').status_code==200
 with patch('apps.core.starting_lab.verify_registration_response') as verifier:
  assert c.post(BASE+'device/register/complete/',data='{}',content_type='application/json',HTTP_HOST='localhost').status_code==400
  verifier.assert_not_called()
 assert post(c,'device/register/options/').status_code==200
 with patch('apps.core.starting_lab.verify_registration_response',side_effect=ValueError('unverified')) as verifier:
  assert post(c,'device/register/complete/',{}).status_code==400
  assert verifier.call_args.kwargs['require_user_verification'] is True
 assert post(c,'device/register/options/',{}).status_code==200
 assert not LabDeviceCredential.objects.exists()

def test_electrical_boundary_equations():
 script="""import assert from 'node:assert/strict';import {evaluateElectrical as e,DEFAULT_ELECTRICAL as d} from './static/js/yankson/electrical.mjs';let h=e(d);assert.ok(h.ready);assert.ok(Math.abs(h.current-180)<1e-8);assert.ok(Math.abs(h.drop-1.8)<1e-8);assert.ok(Math.abs(h.starterV-10.8)<1e-8);assert.equal(h.differential,2);assert.equal(e({...d,terminationOhm:120}).canOK,false);assert.equal(e({...d,canHighV:1.5}).canOK,false);assert.equal(e({...d,wireOhm:.08}).powerOK,false);assert.equal(e({...d,coilOhm:1}).powerOK,false);assert.equal(e({...d,fuseA:100}).blows,false);assert.equal(e({...d,fuseA:100},{starter:true}).blows,true);assert.equal(e(d,{fuseOpen:true}).powerOK,false);assert.throws(()=>e({...d,batteryV:NaN}));"""
 r=subprocess.run(['node','--input-type=module','-e',script],capture_output=True,text=True);assert r.returncode==0,r.stderr
