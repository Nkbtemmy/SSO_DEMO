from saml2 import saml, BINDING_HTTP_REDIRECT, BINDING_HTTP_POST

def build_saml_config_for_org(cfg, sp_entity_id: str, acs_url: str, slo_url: str | None = None):
    return {
        "entityid": sp_entity_id,
        "service": {
            "sp": {
                "endpoints": {
                    "assertion_consumer_service": [(acs_url, BINDING_HTTP_POST)],
                    "single_logout_service": [(slo_url or acs_url, BINDING_HTTP_REDIRECT)],
                },
                "allow_unsolicited": True,
                "authn_requests_signed": False,
                "logout_requests_signed": False,
                "want_assertions_signed": True,
                "name_id_format": [cfg.saml_nameid_format or saml.NAMEID_FORMAT_EMAILADDRESS],
            }
        },
        "security": {
            "wantAttributeStatement": True,
        },
        "debug": False,
        # Inline IdP metadata
        "idp_configs": [{
            "entity_id": cfg.saml_entity_id,
            "single_sign_on_service": [{"binding": BINDING_HTTP_REDIRECT, "location": cfg.saml_idp_sso_url}],
            "x509cert": cfg.saml_idp_x509cert,
        }],
    }
