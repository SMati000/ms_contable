from django.contrib import admin
from django.contrib.auth import get_user_model, login
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render

from .forms import FirstAdminAccountForm


def first_run(request):
    user_model = get_user_model()

    if user_model.objects.filter(is_superuser=True).exists():
        return redirect("admin:index")

    form_data = request.POST if request.method == "POST" else None
    form = FirstAdminAccountForm(form_data)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if user_model.objects.filter(is_superuser=True).exists():
                    return redirect("admin:index")

                user = form.save(commit=False)
                user.is_staff = True
                user.is_superuser = True
                user.save()
        except IntegrityError:
            form.add_error(None, "No se pudo crear la cuenta. Probá con otro usuario.")
        else:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            request.session.set_expiry(
                None if form.cleaned_data["remember_session"] else 0
            )
            return redirect("admin:index")

    context = admin.site.each_context(request)
    context.update({"form": form, "title": "Crear primera cuenta"})
    return render(request, "admin/first_run.html", context)


def admin_login(request):
    user_model = get_user_model()

    if not user_model.objects.filter(is_superuser=True).exists():
        return redirect("first-run")

    response = admin.site.login(request)
    if request.method == "POST" and response.status_code == 302:
        request.session.set_expiry(
            None if request.POST.get("remember_session") else 0
        )
    return response
