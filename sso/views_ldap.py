import ldap
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from core.sso.tenant import get_org_and_config

User = get_user_model()

class LDAPLoginView(View):
    def post(self, request):
        import json
        data = json.loads(request.body.decode("utf-8"))
        org_id = data.get("org_id")
        username = data.get("username")
        password = data.get("password")
        if not (username and password):
            return HttpResponseBadRequest("Missing credentials.")
        try:
            org, cfg = get_org_and_config(org_id=org_id, email=None)
        except Exception as e:
            return HttpResponseBadRequest(str(e))
        if not cfg.ldap_server_uri or not cfg.ldap_user_search_base:
            return HttpResponseBadRequest("LDAP not configured for this organisation.")

        # Connect / bind with service account if provided
        conn = ldap.initialize(cfg.ldap_server_uri)
        conn.protocol_version = 3
        if cfg.ldap_start_tls:
            conn.start_tls_s()

        if cfg.ldap_bind_dn:
            conn.simple_bind_s(cfg.ldap_bind_dn, cfg.ldap_bind_password or "")

        # Find the user DN by filter (search on mail or sAMAccountName per your cfg)
        search_filter = (cfg.ldap_user_filter or "(mail=%(user)s)") % {"user": username}
        results = conn.search_s(cfg.ldap_user_search_base, ldap.SCOPE_SUBTREE, search_filter, ["mail", "givenName", "sn"])
        if not results:
            return HttpResponseBadRequest("User not found in LDAP.")
        user_dn, attrs = results[0]

        # Verify password by binding as the user
        try:
            test = ldap.initialize(cfg.ldap_server_uri)
            if cfg.ldap_start_tls:
                test.start_tls_s()
            test.simple_bind_s(user_dn, password)
        except ldap.INVALID_CREDENTIALS:
            return HttpResponseBadRequest("Invalid LDAP credentials.")

        email = (attrs.get("mail") or [None])[0].decode() if attrs.get("mail") else None
        given = (attrs.get("givenName") or [b""])[0].decode()
        family = (attrs.get("sn") or [b""])[0].decode()
        if not email:
            # fall back to username-as-email if it is an email
            email = username if "@" in username else None
        if not email:
            return HttpResponseBadRequest("No email attribute in LDAP entry.")

        user, created = User.objects.get_or_create(
            email=email,
            defaults=dict(firstname=given, lastname=family, organisation=org, type_account="ldap", is_active=True),
        )
        if not created and not user.organisation:
            user.organisation = org; user.save()

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["org_id"] = str(getattr(user.organisation, "id", "")) if getattr(user, "organisation", None) else ""
        return JsonResponse({"access": str(refresh.access_token), "refresh": str(refresh)})
