from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Hook LDAP user population function
        from django.conf import settings
        from .utils import ldap_user_populate
        settings.AUTH_LDAP_USER_POPULATE = ldap_user_populate
