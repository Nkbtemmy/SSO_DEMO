-- Sample Database Setup for Multi-Tenant SSO

-- 1. Create sample organizations
INSERT INTO accounts_organisation (id, name, domain) VALUES
("b41628d3-98e6-4f49-b659-4d435b38aba5", 'Acme Corp', 'acme.com'),
("b41628d3-98e6-4f49-b659-4d435b38aba6", 'TechStart Inc', 'techstart.io'),
("b41628d3-98e6-4f49-b659-4d435b38aba7", 'Enterprise Solutions', 'enterprise.org');

-- 2. OIDC Configuration (Azure AD example)
INSERT INTO core_ssoconfiguration (
    organisation_id,
    provider_type,
    enabled,
    allowed_email_domains,
    oidc_issuer,
    oidc_client_id,
    oidc_client_secret,
    oidc_scopes,
    created_at,
    updated_at
) VALUES (
    'b41628d3-98e6-4f49-b659-4d435b38aba5', -- Acme Corp
    'oidc',
    TRUE,
    'acme.com;acme.org',
    'https://login.microsoftonline.com/12345678-1234-1234-1234-123456789012/v2.0',
    'your-azure-client-id',
    'your-azure-client-secret',
    'openid profile email',
    NOW(),
    NOW()
);

-- 3. SAML Configuration (ADFS example)
INSERT INTO core_ssoconfiguration (
    organisation_id,
    provider_type,
    enabled,
    allowed_email_domains,
    saml_entity_id,
    saml_idp_sso_url,
    saml_idp_x509cert,
    saml_nameid_format,
    created_at,
    updated_at
) VALUES (
    'b41628d3-98e6-4f49-b659-4d435b38aba6', -- TechStart Inc
    'saml',
    TRUE,
    'techstart.io',
    'https://adfs.techstart.io/adfs/services/trust',
    'https://adfs.techstart.io/adfs/ls/',
    '-----BEGIN CERTIFICATE-----
MIICXjCCAcegAwIBAgIJAKS0yiqVrJHiMA0GCSqGSIb3DQEBCwUAMEYxCzAJBgNV...
-----END CERTIFICATE-----',
    'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
    NOW(),
    NOW()
);

-- 4. LDAP Configuration (Active Directory example)
INSERT INTO core_ssoconfiguration (
    organisation_id,
    provider_type,
    enabled,
    allowed_email_domains,
    ldap_server_uri,
    ldap_bind_dn,
    ldap_bind_password,
    ldap_user_search_base,
    ldap_user_filter,
    ldap_start_tls,
    created_at,
    updated_at
) VALUES (
    'b41628d3-98e6-4f49-b659-4d435b38aba7', -- Enterprise Solutions
    'oidc', -- Can still be oidc but with LDAP for verification
    TRUE,
    'enterprise.org',
    'ldaps://dc.enterprise.org:636',
    'CN=svc_django,OU=Service Accounts,DC=enterprise,DC=org',
    'service-account-password',
    'DC=enterprise,DC=org',
    '(mail=%(user)s)',
    FALSE,
    NOW(),
    NOW()
);

-- 5. Create some sample users (these would be auto-created via JIT provisioning)
INSERT INTO auth_user (id,email, firstname, lastname, organisation_id, type_account, is_active) VALUES
("b41628d3-98e6-4f49-b659-4d435b38aba5", 'john.doe@acme.com', 'John', 'Doe', 1, 'sso', TRUE),
("b41628d3-98e6-4f49-b659-4d435b38aba6", 'jane.smith@techstart.io', 'Jane', 'Smith', 2, 'sso', TRUE),
("b41628d3-98e6-4f49-b659-4d435b38aba7", 'admin@enterprise.org', 'Admin', 'User', 3, 'ldap', TRUE);

-- 6. Indexes for performance
CREATE INDEX idx_sso_config_org ON core_ssoconfiguration(organisation_id);
CREATE INDEX idx_sso_config_enabled ON core_ssoconfiguration(enabled);
CREATE INDEX idx_user_email ON auth_user(email);
CREATE INDEX idx_user_org ON auth_user(organisation_id);

-- 7. Constraints
ALTER TABLE core_ssoconfiguration 
ADD CONSTRAINT unique_org_sso UNIQUE(organisation_id);

-- Ensure email domains are properly formatted
-- You might want a trigger or validation for this