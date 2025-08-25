from django.shortcuts import redirect
from django.contrib.auth import get_user_model, login
from django.conf import settings
import msal, requests

from django.http import JsonResponse
import logging

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from accounts.models import User, Organisation
from accounts.utils import create_sso_user, get_user_permissions

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)



logger = logging.getLogger(__name__)

User = get_user_model()

def azure_login(request):
    try:
        # Validate configuration before creating MSAL app
        if not all([settings.AZURE_CLIENT_ID, settings.AZURE_CLIENT_SECRET, settings.AZURE_TENANT_ID]):
            return JsonResponse({
                'error': 'Azure configuration incomplete',
                'details': 'Missing required Azure settings'
            }, status=500)
        
        # Create MSAL application
        msal_app = msal.ConfidentialClientApplication(
            client_id=settings.AZURE_CLIENT_ID,
            client_credential=settings.AZURE_CLIENT_SECRET,
            authority=settings.AZURE_AUTHORITY,
        )
        
        # Get authorization URL
        auth_url = msal_app.get_authorization_request_url(
            scopes=["https://graph.microsoft.com/.default"],
            redirect_uri=settings.AZURE_REDIRECT_URI,
        )
        
        return redirect(auth_url)
        
    except ValueError as e:
        logger.error(f"Azure configuration error: {str(e)}")
        return JsonResponse({
            'error': 'Configuration Error',
            'details': str(e)
        }, status=500)
    
    except Exception as e:
        logger.error(f"Unexpected error in azure_login: {str(e)}")
        return JsonResponse({
            'error': 'Internal Server Error',
            'details': 'Please check your Azure configuration'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def azure_callback(request):
    """Simplified Azure OAuth callback using utility functions"""
    try:
        # Basic validation
        code = request.GET.get("code")
        error = request.GET.get("error")
        
        if error:
            logger.error(f"Azure OAuth error: {error}")
            return JsonResponse({'error': error}, status=400)
        
        if not code:
            return JsonResponse({'error': 'No authorization code'}, status=400)
        
        # Get access token
        msal_app = msal.ConfidentialClientApplication(
            client_id=settings.AZURE_CLIENT_ID,
            authority=settings.AZURE_AUTHORITY,
            client_credential=settings.AZURE_CLIENT_SECRET,
        )
        
        token_result = msal_app.acquire_token_by_authorization_code(
            code=code,
            scopes=["https://graph.microsoft.com/.default"],
            redirect_uri=settings.AZURE_REDIRECT_URI,
        )
        
        if "error" in token_result:
            logger.error(f"Token error: {token_result['error_description']}")
            return JsonResponse({
                'error': 'Token acquisition failed',
                'details': token_result['error_description']
            }, status=400)
        
        # Get user info from Graph API
        user_response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {token_result['access_token']}"},
            timeout=10
        )
        user_response.raise_for_status()
        user_info = user_response.json()
        

        print("User Info:----------------", user_info)

        # Extract user data
        email = user_info.get("mail") or user_info.get("userPrincipalName")
        if not email:
            return JsonResponse({'error': 'No email in user profile'}, status=400)
        
        # Create/update user using utility function
        user, created = create_sso_user(
            email=email,
            first_name=user_info.get("givenName", ""),
            last_name=user_info.get("surname", ""),
            company_name=user_info.get("companyName"),
            auth_provider="azure"
        )
        
        # Log the user in
        login(request, user)
        
        # Store session data
        request.session['auth_provider'] = 'azure'
        request.session['user_permissions'] = get_user_permissions(user)
        
        logger.info(f"User {email} logged in successfully via Azure")
        
        # Redirect
        next_url = request.GET.get('next', '/')
        return redirect(next_url)
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return JsonResponse({
            'error': 'Failed to fetch user data',
            'details': str(e)
        }, status=500)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({
            'error': 'Authentication failed',
            'details': 'An unexpected error occurred'
        }, status=500)