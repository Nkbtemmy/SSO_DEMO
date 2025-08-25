from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from mozilla_django_oidc.views import OIDCAuthenticationRequestView, OIDCAuthenticationCallbackView
from core.sso.tenant import get_org_and_config

class OIDCStartView(OIDCAuthenticationRequestView):
    def get(self, request, *args, **kwargs):
        org_id = request.GET.get("org_id")
        email = request.GET.get("email")
        try:
            org, cfg = get_org_and_config(org_id=org_id, email=email)
            if cfg.provider_type != "oidc":
                return HttpResponseBadRequest("Organisation not configured for OIDC.")
        except Exception as e:
            return HttpResponseBadRequest(str(e))
        request.session["sso_org_id"] = str(org.id)
        return super().get(request, *args, **kwargs)

class OIDCCallbackView(OIDCAuthenticationCallbackView):
    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)  # logs in / creates the user
        return redirect(reverse("sso-post-login"))
