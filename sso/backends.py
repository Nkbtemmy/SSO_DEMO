from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

User = get_user_model()

class MultiTenantOIDCBackend(OIDCAuthenticationBackend):
    """Loads OIDC config per-organisation and does JIT user provisioning."""
    def get_settings(self, request=None):
        if not request:
            return super().get_settings(request)
        org_id = request.session.get("sso_org_id")
        if not org_id:
            return super().get_settings(request)

        key = f"oidc_settings_{org_id}"
        cached = cache.get(key)
        if cached:
            return cached

        from core.models.sso import SSOConfiguration
        from core.models import Organisation
        org = Organisation.objects.get(pk=org_id)
        cfg = SSOConfiguration.objects.get(organisation=org, enabled=True, provider_type="oidc")

        s = {
            "OIDC_RP_CLIENT_ID": cfg.oidc_client_id,
            "OIDC_RP_CLIENT_SECRET": cfg.oidc_client_secret,
            "OIDC_OP_DISCOVERY_ENDPOINT": f"{cfg.oidc_issuer}/.well-known/openid-configuration",
            "OIDC_RP_SCOPES": cfg.oidc_scopes or "openid profile email",
            "OIDC_STORE_ID_TOKEN": True,
            "OIDC_VERIFY_SSL": True,
        }
        cache.set(key, s, 300)
        return s

    def filter_users_by_claims(self, claims):
        email = claims.get("email") or claims.get("upn") or claims.get("preferred_username")
        if not email:
            return User.objects.none()
        return User.objects.filter(email__iexact=email)

    def create_user(self, claims):
        from core.models import Organisation
        request = getattr(self, "request", None)
        org = None
        if request:
            org_id = request.session.get("sso_org_id")
            if org_id:
                org = Organisation.objects.filter(pk=org_id).first()

        email = claims.get("email") or claims.get("upn") or claims.get("preferred_username")
        given = claims.get("given_name") or (claims.get("name", "").split(" ")[:1] or [""])[0]
        family = claims.get("family_name") or ""

        return User.objects.create(
            email=email,
            firstname=given,
            lastname=family,
            organisation=org,
            type_account="sso",
            is_active=True,
            created_at=timezone.now(),
        )
