from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.auditlog.services import record_event

from .decorators import administrator_required
from .forms import AccountAvailabilityForm, ApprovedAuthenticationForm, RegistrationForm, UserManagementFilterForm
from .models import User
from .services import approve_for_academic_setup, reject_registration, reset_account_password
from .services import change_account_availability


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            record_event(actor=user, action="ACCOUNT_REGISTERED", target=user, request=request)
        return render(request, "accounts/registration_complete.html", {"registered_user": user})
    return render(request, "accounts/register.html", {"form": form})


class PlatformLoginView(LoginView):
    authentication_form = ApprovedAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        record_event(actor=self.request.user, action="LOGIN", request=self.request)
        return response


class PlatformPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["must_change_password"])
        record_event(actor=self.request.user, action="PASSWORD_CHANGED", request=self.request)
        messages.success(self.request, "Your password has been changed.")
        return response

    def get_success_url(self):
        return reverse("core:dashboard")


def platform_logout(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if request.user.is_authenticated:
        record_event(actor=request.user, action="LOGOUT", request=request)
    logout(request)
    return redirect("core:home")


@administrator_required
def pending_approvals(request):
    users = User.objects.filter(approval_status=User.ApprovalStatus.PENDING).order_by("date_joined")
    return render(request, "accounts/pending_approvals.html", {"pending_users": users})


@administrator_required
def approve_account(request, user_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    user = get_object_or_404(User, pk=user_id)
    try:
        approve_for_academic_setup(user=user, reviewer=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("accounts:pending_approvals")
    messages.success(request, f"{user.full_name} is ready for academic setup.")
    return redirect("academics:setup", user_id=user.pk)


@administrator_required
def reject_account(request, user_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    user = get_object_or_404(User, pk=user_id)
    try:
        reject_registration(user=user, reviewer=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"{user.full_name}'s registration was rejected.")
    return redirect("accounts:pending_approvals")


@administrator_required
def user_management(request):
    form = UserManagementFilterForm(request.GET or None)
    users = User.objects.exclude(role=User.Role.ADMINISTRATOR).select_related("academic_profile")
    if form.is_valid():
        if form.cleaned_data.get("q"):
            query = form.cleaned_data["q"]
            users = users.filter(
                Q(full_name__icontains=query)
                | Q(email__icontains=query)
                | Q(academic_profile__student_or_staff_id__icontains=query)
            )
        if form.cleaned_data.get("role"):
            users = users.filter(role=form.cleaned_data["role"])
        if form.cleaned_data.get("status"):
            users = users.filter(approval_status=form.cleaned_data["status"])
    return render(request, "accounts/user_management.html", {"form": form, "managed_users": users})


@administrator_required
def account_availability(request, user_id, action):
    account = get_object_or_404(User.objects.filter(is_staff=False, is_superuser=False).exclude(role=User.Role.ADMINISTRATOR), pk=user_id)
    if action not in ["suspend", "reactivate"]:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = AccountAvailabilityForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            change_account_availability(user=account, administrator=request.user, action=action, reason=form.cleaned_data["reason"])
        except ValueError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Account access updated. Existing sessions revoked; academic records retained.")
            return redirect("accounts:user_management")
    return render(request, "accounts/account_availability.html", {"account": account, "action": action, "form": form})


@administrator_required
def admin_password_reset(request, user_id):
    account = get_object_or_404(User.objects.exclude(role=User.Role.ADMINISTRATOR), pk=user_id)
    if request.method == "GET":
        return render(request, "accounts/password_reset_confirm.html", {"account": account})
    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])
    try:
        temporary_password = reset_account_password(user=account, administrator=request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("accounts:user_management")
    return render(
        request,
        "accounts/password_reset_complete.html",
        {"account": account, "temporary_password": temporary_password},
    )
