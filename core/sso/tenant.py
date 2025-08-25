from django.shortcuts import get_object_or_404
from accounts.models import Organisation
from core.models import SSOConfiguration

def get_org_and_config(org_id: str | None = None, email: str | None = None):
    if org_id:
        org = get_object_or_404(Organisation, pk=org_id)
        cfg = get_object_or_404(SSOConfiguration, organisation=org, enabled=True)
        return org, cfg
    if email and "@" in email:
        domain = email.split("@")[-1].lower()
        cfg = SSOConfiguration.objects.filter(enabled=True).select_related("organisation")
        for c in cfg:
            if domain in c.domains():
                return c.organisation, c
    raise ValueError("Unable to resolve organisation/SSO configuration.")
