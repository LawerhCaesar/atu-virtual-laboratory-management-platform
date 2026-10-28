"""Authenticated, CSRF-protected P2 simulation services; no persisted learner data."""
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from apps.accounts.decorators import roles_required
from apps.accounts.models import User
from .simulations import p2_hybrid as model

allowed = roles_required(User.Role.ADMINISTRATOR, User.Role.LECTURER, User.Role.STUDENT)


@allowed
@require_GET
def page(request):
    return render(request,'core/p2_hybrid.html',{'p2_info':model.model_info()})


@allowed
@require_GET
def info(request):
    return JsonResponse(model.model_info())


def calculate(request, operation):
    try:
        if len(request.body)>65536:
            return JsonResponse({'errors':{'request':'Request exceeds 64 KiB.'}},status=413)
        payload=json.loads(request.body, parse_int=float)
        return JsonResponse(operation(payload),json_dumps_params={'allow_nan':False})
    except (json.JSONDecodeError,UnicodeDecodeError):
        return JsonResponse({'errors':{'request':'Supply valid JSON.'}},status=400)
    except model.ValidationError as exc:
        return JsonResponse({'errors':exc.errors},status=400)


@allowed
@require_POST
def simulate(request):
    return calculate(request,model.simulate)


@allowed
@require_POST
def compare(request):
    return calculate(request,model.compare)
