from django.conf import settings
from django.http import JsonResponse
from django.test import TestCase

# Create your tests here.
# Add this to your views.py for testing
def test_azure_config(request):
    """Test endpoint to verify Azure configuration"""
    config_status = {
        'AZURE_TENANT_ID': bool(getattr(settings, 'AZURE_TENANT_ID', None)),
        'AZURE_CLIENT_ID': bool(getattr(settings, 'AZURE_CLIENT_ID', None)),
        'AZURE_CLIENT_SECRET': bool(getattr(settings, 'AZURE_CLIENT_SECRET', None)),
        'AZURE_AUTHORITY': getattr(settings, 'AZURE_AUTHORITY', 'Not set'),
        'AZURE_REDIRECT_URI': getattr(settings, 'AZURE_REDIRECT_URI', 'Not set'),
    }
    
    # Test OIDC discovery endpoint
    import requests
    try:
        discovery_url = f"{settings.AZURE_AUTHORITY}/v2.0/.well-known/openid-configuration"
        response = requests.get(discovery_url, timeout=10)
        config_status['oidc_discovery'] = response.status_code == 200
        config_status['discovery_url'] = discovery_url
    except Exception as e:
        config_status['oidc_discovery'] = False
        config_status['discovery_error'] = str(e)
    
    return JsonResponse(config_status)