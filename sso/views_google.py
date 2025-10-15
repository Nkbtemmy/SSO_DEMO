from django.shortcuts import redirect
from django.contrib.auth import get_user_model, login
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
import logging
import requests
import urllib.parse

from accounts.models import User
from accounts.utils import create_sso_user

logger = logging.getLogger(__name__)
User = get_user_model()

class GoogleLoginView(APIView):
    """Initiate Google OAuth login"""
    def get(self, request):
        try:
            # Validate configuration
            if not all([settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET]):
                logger.error("Google configuration incomplete: Missing Google OAuth settings.")
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


class GoogleCallbackView(APIView):
    """Handle Google OAuth callback"""
    def get(self, request):
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

            logger.info(f"Token request data: {token_data}")
            token_response = requests.post(token_url, data=token_data, timeout=10)
            
            token_response.raise_for_status()  # Raise error if response status is not 2xx
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
            
            user_response.raise_for_status()  # Raise error if response status is not 2xx
            user_info = user_response.json()
            
            logger.info(f"Google User Info: {user_info}")
            
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
            
            logger.info(f"User created/updated: {user}")
            
            # Log the user in
            login(request, user)
            
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
class GoogleLogoutView(APIView):
    """Handle Google-specific logout"""
    def post(self, request):
        try:
            # Clear session data
            if 'auth_provider' in request.session:
                del request.session['auth_provider']
            if 'user_permissions' in request.session:
                del request.session['user_permissions']
                
            # Optionally, revoke Google token (this is not required but can be added)
            # You can also call Google's token revocation endpoint here if needed
            
            logger.info("User logged out from Google session")
            return JsonResponse({'message': 'Logged out successfully'})
            
        except Exception as e:
            logger.error(f"Error during Google logout: {str(e)}")
            return JsonResponse({
                'error': 'Logout failed',
                'details': str(e)
            }, status=500)
