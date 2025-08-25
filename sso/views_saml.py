from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import login, get_user_model
from django.views import View
from saml2.client import Saml2Client
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2 import entity
from core.sso.tenant import get_org_and_config
from core.sso.saml_conf import build_saml_config_for_org

User = get_user_model()

def _client(request, cfg):
    sp_entity_id = request.build_absolute_uri(reverse("saml-start"))
    acs_url = request.build_absolute_uri(reverse("saml-acs"))
    settings = build_saml_config_for_org(cfg, sp_entity_id, acs_url)
    client = Saml2Client(config=None)
    client.config.load(settings)
    # Inject IdP metadata
    idp = settings["idp_configs"][0]
    client.metadata.identifiers[idp["entity_id"]] = [idp["entity_id"]]
    client.metadata.single_sign_on_service[idp["entity_id"]] = [(idp["single_sign_on_service"][0]["location"], BINDING_HTTP_REDIRECT)]
    client.metadata.certs[idp["entity_id"]] = {"x509cert": [idp["x509cert"]]}
    return client

class SAMLStartView(View):
    def get(self, request):
        try:
            org, cfg = get_org_and_config(org_id=request.GET.get("org_id"), email=request.GET.get("email"))
            if cfg.provider_type != "saml":
                return HttpResponseBadRequest("Organisation not configured for SAML.")
        except Exception as e:
            return HttpResponseBadRequest(str(e))
        request.session["sso_org_id"] = str(org.id)
        client = _client(request, cfg)
        _, info = client.prepare_for_authenticate()
        for k, v in info["headers"]:
            if k == "Location":
                return redirect(v)
        return HttpResponseBadRequest("Unable to initiate SAML login.")

class SAMLACSView(View):
    def post(self, request):
        org_id = request.session.get("sso_org_id")
        if not org_id:
            return HttpResponseBadRequest("Missing organisation session.")
        from core.models import Organisation
        from core.models.sso import SSOConfiguration
        org = Organisation.objects.get(pk=org_id)
        cfg = SSOConfiguration.objects.get(organisation=org, enabled=True, provider_type="saml")

        client = _client(request, cfg)
        response = client.parse_authn_request_response(request.POST.get("SAMLResponse"), entity.BINDING_HTTP_POST)
        if not response or response.ava is None:
            return HttpResponseBadRequest("Invalid SAML response.")

        attrs = response.ava
        email = (attrs.get("email") or attrs.get("mail") or attrs.get("User.email") or [None])[0]
        given = (attrs.get("givenName") or attrs.get("first_name") or [None])[0]
        family = (attrs.get("sn") or attrs.get("last_name") or [None])[0]
        if not email:
            return HttpResponseBadRequest("No email in SAML assertion.")

        user, created = User.objects.get_or_create(
            email=email,
            defaults=dict(firstname=given or "", lastname=family or "", organisation=org, type_account="sso", is_active=True),
        )
        if not created:
            changed = False
            if given and user.firstname != given: user.firstname = given; changed = True
            if family and user.lastname != family: user.lastname = family; changed = True
            if not user.organisation: user.organisation = org; changed = True
            if changed: user.save()

        login(request, user)
        return redirect(reverse("sso-post-login"))
