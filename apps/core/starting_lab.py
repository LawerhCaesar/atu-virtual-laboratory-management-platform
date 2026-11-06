"""Same-origin verified device ceremonies and lecturer-authored lab exercises."""
import base64
import json
import time
from urllib.parse import urlsplit
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from apps.accounts.decorators import roles_required
from apps.accounts.models import User
from .models import LabDeviceCredential, StartingExercise
from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response, options_to_json
from webauthn.helpers.structs import AuthenticatorSelectionCriteria, AuthenticatorAttachment, UserVerificationRequirement, PublicKeyCredentialDescriptor

active = roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)
def encode(value): return base64.urlsafe_b64encode(value).decode().rstrip('=')
def decode(value): return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
def context(request):
    origin = request.build_absolute_uri('/').rstrip('/')
    parts = urlsplit(origin)
    if parts.scheme != 'https' and parts.hostname not in ['localhost', '127.0.0.1', '[::1]', '::1']:
        raise ValueError('Device verification requires HTTPS.')
    return parts.hostname, origin

def body(request):
    if len(request.body) > 40000: raise ValueError('Request too large.')
    return json.loads(request.body)

@never_cache
@active
@require_POST
def device_options(request, operation):
    if operation not in ['register', 'verify']: return JsonResponse({'error':'Unknown operation.'}, status=400)
    try:
        rp, origin = context(request)
        credentials = LabDeviceCredential.objects.filter(user=request.user)
        descriptors = [PublicKeyCredentialDescriptor(id=decode(c.credential_id)) for c in credentials]
        if operation == 'register':
            if len(descriptors) >= 5: raise ValueError('Five lab devices are already registered.')
            options = generate_registration_options(rp_id=rp, rp_name='ATU Starting Laboratory', user_id=str(request.user.pk).encode(), user_name=request.user.email, exclude_credentials=descriptors, authenticator_selection=AuthenticatorSelectionCriteria(authenticator_attachment=AuthenticatorAttachment.PLATFORM, user_verification=UserVerificationRequirement.REQUIRED))
        else:
            if not descriptors: raise ValueError('Register this device for the lab first.')
            options = generate_authentication_options(rp_id=rp, allow_credentials=descriptors, user_verification=UserVerificationRequirement.REQUIRED)
        # One outstanding, expiring, user/session-bound ceremony; a later request replaces it.
        request.session['starting_ceremony'] = {'operation':operation, 'challenge':encode(options.challenge), 'created':time.time(), 'origin':origin, 'rp':rp}
        return JsonResponse(json.loads(options_to_json(options)))
    except (ValueError, TypeError) as exc: return JsonResponse({'error':str(exc)}, status=400)

@never_cache
@active
@require_POST
def device_complete(request, operation):
    ceremony = request.session.pop('starting_ceremony', None)
    if not ceremony or ceremony['operation'] != operation or time.time()-ceremony['created'] > 120:
        return JsonResponse({'error':'Verification expired or already used. Try again.'},status=400)
    try:
        rp, origin = context(request)
        if origin != ceremony['origin'] or rp != ceremony['rp']: raise ValueError('Origin changed.')
        credential = body(request)
        if operation == 'register':
            result = verify_registration_response(credential=credential, expected_challenge=decode(ceremony['challenge']), expected_rp_id=rp, expected_origin=origin, require_user_verification=True)
            LabDeviceCredential.objects.create(user=request.user,credential_id=encode(result.credential_id),public_key=result.credential_public_key,sign_count=result.sign_count)
            return JsonResponse({'registered':True,'message':'Device registered. Verify it to authorize this experiment.'})
        if operation != 'verify': raise ValueError('Unknown operation.')
        with transaction.atomic():
            saved = LabDeviceCredential.objects.select_for_update().get(user=request.user,credential_id=credential.get('id'))
            result = verify_authentication_response(credential=credential, expected_challenge=decode(ceremony['challenge']), expected_rp_id=rp, expected_origin=origin, credential_public_key=bytes(saved.public_key),credential_current_sign_count=saved.sign_count,require_user_verification=True)
            saved.sign_count=result.new_sign_count;saved.save(update_fields=['sign_count'])
        return JsonResponse({'verified':True,'validForSeconds':60,'method':'platform user verification; biometric modality not disclosed'})
    except Exception:
        # Never echo credential material or verifier internals.
        return JsonResponse({'error':'Device response could not be verified. No permission granted.'},status=400)

# JSON exercises are bounded data only; no expressions, scripts, or account permissions.
ELECTRICAL_BOUNDS={'batteryV':(0,16),'wireOhm':(0,2),'starterOhm':(.005,2),'fuseA':(1,1000),'canHighV':(0,5),'canLowV':(0,5),'terminationOhm':(0,1000),'coilOhm':(1,1000)}
def validate_exercise(c):
    import math
    if not isinstance(c,dict) or set(c) != {'electrical','parameters','wires','faults','operating'}: raise ValueError('Invalid exercise format.')
    electrical=c['electrical']
    if not isinstance(electrical,dict) or set(electrical) != set(ELECTRICAL_BOUNDS): raise ValueError('Incomplete electrical settings.')
    for key,(lo,hi) in ELECTRICAL_BOUNDS.items():
        value=electrical[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi: raise ValueError('Invalid electrical value: '+key)
    operating=c['operating']
    if not isinstance(operating,dict) or set(operating)!={'extraLoadNm','overrideRPM'}:raise ValueError('Invalid operating settings.')
    for key,hi in [('extraLoadNm',100),('overrideRPM',10000)]:
        v=operating[key]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=hi:raise ValueError('Invalid '+key)
    p=c['parameters']
    if not isinstance(p,list) or len(p)!=22 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or (not math.isfinite(v) or abs(v)>1000000) for v in p): raise ValueError('22 finite parameters required.')
    if not (p[0]==.01 and p[1]>0 and p[2]>p[1] and p[3]>0 and p[4]>0 and p[5]>p[11] and p[6]>=p[0] and p[7]>=p[8]>=p[0] and p[9]>0 and p[12]>p[5] and p[13]>0 and p[16]>0 and p[20]>0): raise ValueError('Invalid controller thresholds.')
    expected_wires={'power','reference','interlock','match','contact','voice','canh','canl','transceiver','starter','run'}
    expected_faults={'powerGood','interlockOK','monitorConnected','ignitionAllowed','CANdrop','badID','badDLC','badRange','useRPMoverride'}
    for key,expected in [('wires',expected_wires),('faults',expected_faults)]:
        if not isinstance(c[key],dict) or set(c[key])!=expected or any(type(v)!=bool for v in c[key].values()):raise ValueError('Invalid '+key)
    return c

@never_cache
@active
@require_GET
def exercises(request):
    items=StartingExercise.objects.all() if request.user.role in [User.Role.ADMINISTRATOR,User.Role.LECTURER] else StartingExercise.objects.none()
    # Students may open an explicitly shared ID; lists expose only staff-owned material to staff.
    return JsonResponse({'items':[{'id':e.pk,'title':e.title} for e in items.filter(owner=request.user)[:100]]})

@never_cache
@active
@require_POST
def save_exercise(request):
    if request.user.role not in [User.Role.ADMINISTRATOR,User.Role.LECTURER]:return JsonResponse({'error':'Lecturer or administrator required.'},status=403)
    try:
        data=body(request)
        if not isinstance(data,dict) or not isinstance(data.get('title'),str):raise ValueError('A text exercise title is required.')
        title=data['title'].strip();instructions=data.get('instructions','')
        if not title or len(title)>120 or not isinstance(instructions,str) or len(instructions)>3000:raise ValueError('Use a title up to 120 characters and instructions up to 3000 characters.')
        config=validate_exercise(data['configuration'])
        entry=StartingExercise.objects.create(owner=request.user,title=title,instructions=instructions,configuration=config)
        return JsonResponse({'id':entry.pk,'title':entry.title},status=201)
    except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:return JsonResponse({'error':str(exc)},status=400)

@never_cache
@active
@require_GET
def exercise_detail(request,pk):
    try:e=StartingExercise.objects.get(pk=pk)
    except StartingExercise.DoesNotExist:return JsonResponse({'error':'Exercise not found.'},status=404)
    return JsonResponse({'id':e.pk,'title':e.title,'instructions':e.instructions,'configuration':e.configuration})
