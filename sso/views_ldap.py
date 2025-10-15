from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
import ldap
import json

from core.sso.tenant import get_org_and_config

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()

class LDAPLoginView(APIView):
    @swagger_auto_schema(
        operation_summary="LDAP Login",
        operation_description="Authenticate a user against LDAP and return JWT tokens.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username", "password"],
            properties={
                "org_id": openapi.Schema(type=openapi.TYPE_STRING, description="Organisation ID"),
                "username": openapi.Schema(type=openapi.TYPE_STRING, description="LDAP username or email"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="LDAP password"),
            },
            example={
                "org_id": "123",
                "username": "user@example.com",
                "password": "secret"
            }
        ),
        responses={
            200: openapi.Response(
                description="Successful LDAP authentication",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(type=openapi.TYPE_STRING, description="JWT access token"),
                        "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="JWT refresh token"),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request or authentication failure",
                schema=openapi.Schema(type=openapi.TYPE_STRING)
            ),
        },
        tags=["LDAP"]
    )
    def post(self, request):
        data = request.data if hasattr(request, "data") else json.loads(request.body.decode("utf-8"))
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

        try:
            conn = ldap.initialize(cfg.ldap_server_uri)
            conn.protocol_version = 3
            if cfg.ldap_start_tls:
                conn.start_tls_s()
            if cfg.ldap_bind_dn:
                conn.simple_bind_s(cfg.ldap_bind_dn, cfg.ldap_bind_password or "")

            search_filter = (cfg.ldap_user_filter or "(mail=%(user)s)") % {"user": username}
            results = conn.search_s(cfg.ldap_user_search_base, ldap.SCOPE_SUBTREE, search_filter, ["mail", "givenName", "sn"])
            if not results:
                return HttpResponseBadRequest("User not found in LDAP.")

            user_dn, attrs = results[0]

            test_conn = ldap.initialize(cfg.ldap_server_uri)
            if cfg.ldap_start_tls:
                test_conn.start_tls_s()
            test_conn.simple_bind_s(user_dn, password)

        except ldap.INVALID_CREDENTIALS:
            return HttpResponseBadRequest("Invalid LDAP credentials.")
        except ldap.SERVER_DOWN:
            return HttpResponseBadRequest("LDAP server unreachable.")

        email = attrs.get("mail", [b""])[0].decode() if attrs.get("mail") else None
        given = attrs.get("givenName", [b""])[0].decode()
        family = attrs.get("sn", [b""])[0].decode()

        if not email:
            email = username if "@" in username else None
        if not email:
            return HttpResponseBadRequest("No email attribute in LDAP entry.")

        user, created = User.objects.get_or_create(
            email=email,
            defaults=dict(
                first_name=given,
                last_name=family,
                organisation=org,
                type_account="ldap",
                is_active=True,
            ),
        )

        if not created and not user.organisation:
            user.organisation = org
            user.save()

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["org_id"] = str(getattr(user.organisation, "id", "")) if getattr(user, "organisation", None) else ""

        return JsonResponse({"access": str(refresh.access_token), "refresh": str(refresh)})
