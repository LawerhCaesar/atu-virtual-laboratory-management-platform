import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

from apps.auditlog.services import record_event


class SessionIdleTimeoutMiddleware:
    session_key = "platform_last_activity"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = int(time.time())
            last_activity = request.session.get(self.session_key)
            if last_activity and now - int(last_activity) > settings.SESSION_COOKIE_AGE:
                user = request.user
                record_event(actor=user, action="SESSION_TIMEOUT", request=request)
                logout(request)
                messages.warning(request, "Your session ended after five minutes of inactivity.")
                return redirect(settings.LOGIN_URL)
            request.session[self.session_key] = now
        return self.get_response(request)


class ForcePasswordChangeMiddleware:
    allowed_url_names = {"accounts:password_change", "accounts:logout"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.must_change_password:
            allowed_paths = {reverse(name) for name in self.allowed_url_names}
            if request.path not in allowed_paths and not request.path.startswith("/static/"):
                messages.info(request, "Set a new password before continuing.")
                return redirect("accounts:password_change")
        return self.get_response(request)
