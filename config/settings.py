"""
Django settings for config project.
"""

from pathlib import Path
import os
from datetime import timedelta

from config.settings_utils import get_env_variable

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", 'django-insecure-x8a^6-7m#)t#s26kghpnabrotfhv(an$#ngfq3s4edt60ih2-6')
DEBUG = os.getenv("DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "drf_yasg",

    # SSO libs
    "mozilla_django_oidc",
    "djangosaml2",

    # Local apps
    "accounts",
    "sso",
    "api",
    "core",  # Placeholder for core functionality, if needed
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# DB: default to Postgres for quick start
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_variable("DB_NAME", "sso_db"),
        'USER': get_env_variable("DB_USER", "postgres"),
        'PASSWORD': get_env_variable("DB_PASSWORD", "admin123!"),
        'HOST': get_env_variable("DB_HOST", "localhost"),
        'PORT': get_env_variable("DB_PORT", 5432),
        'CONN_MAX_AGE': 0,
    }
}

AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend", 
    "sso.backends.MultiTenantOIDCBackend",  # OIDC (Azure Entra ID, etc.)
    "core.backends.MultiTenantOIDCBackend",  # OIDC (Azure Entra ID, etc.)
    "django.contrib.auth.backends.ModelBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# LOGIN_REDIRECT_URL = "/auth/sso/post-login/"
LOGIN_REDIRECT_URL = '/sso/post-login/'
LOGOUT_REDIRECT_URL = "/"

# Djangosaml2 placeholder (per-org configs dynamically later)
SAML_CONFIG = {}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_DIRS = [os.path.join(BASE_DIR, "static")]

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter your Bearer token in the format `Bearer <token>`',
        }
    },
    'SECURITY_REQUIREMENTS': [{
        'Bearer': [],
    }],
    "SUPPORTED_SCHEMES": ["http", "https"],
}

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

# LDAP mapping (no direct model access here)
AUTH_LDAP_USER_FLAGS_BY_GROUP = {}
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

# Azure OIDC settings
AZURE_TENANT_ID = get_env_variable("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID = get_env_variable("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = get_env_variable("AZURE_CLIENT_SECRET", "")
AZURE_REDIRECT_URI = get_env_variable("AZURE_REDIRECT_URI", "http://localhost:8000/auth/sso/azure/callback/")

# Build the authority URL with the actual tenant ID
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"

# # OIDC settings
OIDC_RP_CLIENT_ID = AZURE_CLIENT_ID
OIDC_RP_CLIENT_SECRET = AZURE_CLIENT_SECRET
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_OP_AUTHORIZATION_ENDPOINT = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/authorize"
OIDC_OP_TOKEN_ENDPOINT = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
OIDC_OP_USER_ENDPOINT = "https://graph.microsoft.com/oidc/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys"

# Add validation to ensure required settings are present
if not AZURE_TENANT_ID:
    raise ValueError("AZURE_TENANT_ID environment variable is required")
if not AZURE_CLIENT_ID:
    raise ValueError("AZURE_CLIENT_ID environment variable is required")
if not AZURE_CLIENT_SECRET:
    raise ValueError("AZURE_CLIENT_SECRET environment variable is required")


# SAML settings
SAML_CONFIG = {
    "xmlsec_binary": "/usr/bin/xmlsec1",
    "entityid": get_env_variable("SAML_ENTITY_ID", "http://localhost:8000/saml/metadata/"),
    "attribute_map_dir": os.path.join(BASE_DIR, "saml", "attribute-maps"),
    "service": {
        "sp": {
            "name": "SSO Service Provider",
            "endpoints": {
                "assertion_consumer_service": [
                    (get_env_variable("SAML_ACS_URL", "http://localhost:8000/saml/acs/"), "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"),
                ],
                "single_logout_service": [
                    (get_env_variable("SAML_SLS_URL", "http://localhost:8000/saml/sls/"), "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"),
                ],
            },
            "required_attributes": ["uid", "email"],
            "optional_attributes": ["first_name", "last_name"],
            "name_id_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
    },
    "metadata": {
        "local": [os.path.join(BASE_DIR, "saml", "metadata", "idp.xml")],
        "remote": [],
    },
    "debug": DEBUG,
    "valid_for": 24 * 60 * 60,  # 24 hours
    "logout_requests": True,
    "logout_responses": True,
    "force_authn": False,
    "allow_unknown_attributes": True,
    "encryption": {
        "sp": {
            "key_file": os.path.join(BASE_DIR, "saml", "keys", "sp-key.pem"),
            "cert_file": os.path.join(BASE_DIR, "saml", "keys", "sp-cert.pem"),
        },
        "idp": {
            "key_file": os.path.join(BASE_DIR, "saml", "keys", "idp-key.pem"),
            "cert_file": os.path.join(BASE_DIR, "saml", "keys", "idp-cert.pem"),
        },
    },
}

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_env_variable("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = int(get_env_variable("EMAIL_PORT", 587))
EMAIL_USE_TLS = get_env_variable("EMAIL_USE_TLS", "1") == "1"
EMAIL_HOST_USER = get_env_variable("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_env_variable("EMAIL_HOST_PASSWORD", "")

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-production-domain.com",
]

# Static file serving.
# https://whitenoise.readthedocs.io/en/stable/django.html#add-compression-and-caching-support
STORAGES = {
    # ...
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}