from django.db import models
from django.utils import timezone

class SSOConfiguration(models.Model):
    OIDC = "oidc"
    SAML = "saml"
    PROVIDER_CHOICES = [(OIDC, "OIDC"), (SAML, "SAML")]

    organisation = models.OneToOneField("accounts.Organisation", on_delete=models.CASCADE, related_name="sso_config")
    provider_type = models.CharField(max_length=10, choices=PROVIDER_CHOICES)
    enabled = models.BooleanField(default=True)

    # semicolon-separated domains (optional auto-routing)
    allowed_email_domains = models.TextField(blank=True, default="")

    # OIDC (Azure Entra ID, Okta, Google)
    oidc_issuer = models.URLField(blank=True, null=True)  # e.g. https://login.microsoftonline.com/<tenant>/v2.0
    oidc_client_id = models.CharField(max_length=255, blank=True, null=True)
    oidc_client_secret = models.CharField(max_length=255, blank=True, null=True)
    oidc_scopes = models.CharField(max_length=255, blank=True, null=True, default="openid profile email")

    # SAML (ADFS/others)
    saml_entity_id = models.CharField(max_length=512, blank=True, null=True)
    saml_idp_sso_url = models.URLField(blank=True, null=True)
    saml_idp_x509cert = models.TextField(blank=True, null=True)
    saml_nameid_format = models.CharField(max_length=255, blank=True, null=True,
        default="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress")

    # LDAP (bind login endpoint)
    ldap_server_uri = models.CharField(max_length=255, blank=True, null=True)
    ldap_bind_dn = models.CharField(max_length=255, blank=True, null=True)
    ldap_bind_password = models.CharField(max_length=255, blank=True, null=True)
    ldap_user_search_base = models.CharField(max_length=255, blank=True, null=True)
    ldap_user_filter = models.CharField(max_length=255, blank=True, null=True, default="(mail=%(user)s)")
    ldap_start_tls = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def domains(self):
        domains_str: str = self.allowed_email_domains or ""
        return [d.strip().lower() for d in domains_str.split(";") if d.strip()]

    def __str__(self):
        return f"{self.organisation} | {str(self.provider_type).upper()} | enabled={self.enabled}"