from django.shortcuts import redirect
from django.contrib.auth import get_user_model, login
from django.conf import settings
from django.http import JsonResponse
import logging
import requests
import urllib.parse

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from accounts.models import User, Organisation
from accounts.utils import create_sso_user, get_user_permissions

logger = logging.getLogger(__name__)
User = get_user_model()

def google_login(request):
    """Initiate Google OAuth login"""
    try:
        # Validate configuration
        if not all([settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET]):
            return JsonResponse({
                'error': 'Google configuration incomplete',
                'details': 'Missing required Google OAuth settings'
            }, status=500)
        
        # Build authorization URL
        auth_params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'response_type': 'code',
            'scope': 'openid email profile',
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,  # Ensure this matches Google Console
            'state': request.GET.get('next', '/'),  # Store next URL in state
            'access_type': 'offline',
            'prompt': 'select_account'
        }

        # Make sure redirect_uri is exactly as registered in Google Console
        logger.info(f"Google OAuth redirect_uri: {settings.GOOGLE_REDIRECT_URI}")

        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(auth_params)}"

        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Unexpected error in google_login: {str(e)}")
        return JsonResponse({
            'error': 'Internal Server Error',
            'details': 'Please check your Google configuration'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def google_callback(request):
    """Handle Google OAuth callback"""
    try:
        # Basic validation
        code = request.GET.get("code")
        error = request.GET.get("error")
        state = request.GET.get("state", "/")
        
        if error:
            logger.error(f"Google OAuth error: {error}")
            return JsonResponse({'error': error}, status=400)
        
        if not code:
            return JsonResponse({'error': 'No authorization code'}, status=400)
        
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        }
        print("Token request data:----------------", token_data)
        token_response = requests.post(token_url, data=token_data, timeout=10)
        print("Token response:----------------", token_response.text)
        token_response.raise_for_status()
        token_result = token_response.json()
        
        if "error" in token_result:
            logger.error(f"Token error: {token_result.get('error_description', token_result['error'])}")
            return JsonResponse({
                'error': 'Token acquisition failed',
                'details': token_result.get('error_description', token_result['error'])
            }, status=400)
        
        access_token = token_result.get('access_token')
        if not access_token:
            return JsonResponse({'error': 'No access token received'}, status=400)
        
        # Get user info from Google API
        user_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        user_response.raise_for_status()
        user_info = user_response.json()
        
        print("Google User Info:----------------", user_info)
        
        # Extract user data
        email = user_info.get("email")
        if not email:
            return JsonResponse({'error': 'No email in user profile'}, status=400)
        
        # Verify email is verified
        if not user_info.get("verified_email", False):
            return JsonResponse({'error': 'Email not verified with Google'}, status=400)
        
        # Create/update user using utility function
        user, created = create_sso_user(
            email=email,
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            company_name=user_info.get("hd"),  # Hosted domain for Google Workspace
            auth_provider="google"
        )
        
        print("User created/updated:-----------------", user)
        
        # Log the user in
        login(request, user)
        
        # Store session data
        # request.session['auth_provider'] = 'google'
        # request.session['user_permissions'] = get_user_permissions(user)
        
        logger.info(f"User {email} logged in successfully via Google")
        
        # Redirect to next URL or default
        next_url = state if state != '/' else request.GET.get('next', '/')
        return redirect(next_url)
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return JsonResponse({
            'error': 'Failed to fetch user data from Google',
            'details': str(e)
        }, status=500)
        
    except Exception as e:
        logger.error(f"Unexpected error in google_callback: {str(e)}")
        return JsonResponse({
            'error': 'Google authentication failed',
            'details': 'An unexpected error occurred'
        }, status=500)
# Optional: Google logout view
def google_logout(request):
    """Optional: Handle Google-specific logout"""
    try:
        # Clear session
        if 'auth_provider' in request.session:
            del request.session['auth_provider']
        if 'user_permissions' in request.session:
            del request.session['user_permissions']
            
        # You can also revoke the Google token if you store it
        # This is optional and depends on your security requirements
        
        logger.info("User logged out from Google session")
        return JsonResponse({'message': 'Logged out successfully'})
        
    except Exception as e:
        logger.error(f"Error during Google logout: {str(e)}")
        return JsonResponse({
            'error': 'Logout failed',
            'details': str(e)
        }, status=500)