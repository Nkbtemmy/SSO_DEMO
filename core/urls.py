from django.urls import path
from core.sso.views_oidc import OIDCStartView, OIDCCallbackView
from core.sso.views_saml import SAMLStartView, SAMLACSView
from core.sso.views_common import PostLoginJWTView
from core.sso.views_ldap import LDAPLoginView

urlpatterns = [
    # OIDC (Azure Entra ID)
    path("oidc/start/", OIDCStartView.as_view(), name="oidc-start"),
    path("oidc/callback/", OIDCCallbackView.as_view(), name="oidc-callback"),

    # SAML (ADFS/Entra SAML)
    path("saml/start/", SAMLStartView.as_view(), name="saml-start"),
    path("saml/acs/", SAMLACSView.as_view(), name="saml-acs"),

    # Common
    path("post-login/", PostLoginJWTView.as_view(), name="sso-post-login"),

    # LDAP (optional)
    path("ldap/login/", LDAPLoginView.as_view(), name="ldap-login"),
]
