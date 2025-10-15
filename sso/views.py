from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework import permissions
import msal
import requests
import logging
from accounts.utils import create_sso_user, get_user_permissions

# from rest_framework_simplejwt.tokens import RefreshToken
# from mozilla_django_oidc.auth import OIDCAuthenticationCallbackView

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


logger = logging.getLogger(__name__)

User = get_user_model()

class AzureLoginView(APIView):
    """Handles the Azure OAuth login process"""

    def get(self, request):
        """Initiate Azure OAuth login"""
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

class AzureCallbackView(APIView):
    """Handles the Azure OAuth callback"""

    def get(self, request):
        """Handle the callback from Azure OAuth"""
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
            
            logger.info(f"User Info: {user_info}")

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
            logger.error(f"Unexpected error in azure_callback: {str(e)}")
            return JsonResponse({
                'error': 'Authentication failed',
                'details': 'An unexpected error occurred'
            }, status=500)

class AzureLogoutView(APIView):
    """Optional: Handles Azure-specific logout"""

    def get(self, request):
        """Handles Azure logout"""
        try:
            # Clear session data related to Azure login
            if 'auth_provider' in request.session:
                del request.session['auth_provider']
            if 'user_permissions' in request.session:
                del request.session['user_permissions']
            
            logger.info("User logged out from Azure session")
            return JsonResponse({'message': 'Logged out successfully'})
        
        except Exception as e:
            logger.error(f"Error during Azure logout: {str(e)}")
            return JsonResponse({
                'error': 'Logout failed',
                'details': str(e)
            }, status=500)


# class OIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
#     def login_success(self):
#         user = self.request.user
#         # Issue JWT after successful OIDC login
#         refresh = RefreshToken.for_user(user)
#         tokens = {'access': str(refresh.access_token), 'refresh': str(refresh)}
#         return JsonResponse(tokens)


@swagger_auto_schema(
    operation_summary="LDAP Login",
    operation_description="Authenticate a user via LDAP and return JWT tokens.",
    tags=["LDAP Authentication"],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["username", "password"],
        properties={
            "username": openapi.Schema(type=openapi.TYPE_STRING, example="johndoe"),
            "password": openapi.Schema(type=openapi.TYPE_STRING, example="secret123"),
        },
    ),
    responses={
        200: openapi.Response(
            description="Success",
            examples={
                "application/json": {"access": "jwt-access-token", "refresh": "jwt-refresh-token"}
            }
        ),
        400: openapi.Response(
            description="Invalid credentials",
            examples={
                "application/json": {"detail": "Invalid credentials"}
            }
        ),
    }
)
class LDAPLoginAPIView(APIView):
    """
    Custom login view for supporting LDAP authentication.
    """
    permission_classes = [permissions.AllowAny]  # Allow any user (authenticated or not) to access this view
    def post(self, request, *args, **kwargs):
        # Extract username and password from request data
        username = request.data.get('username')
        password = request.data.get('password')

        # Authenticate using Django's authenticate function
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # User authenticated successfully, create JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            return Response({
                'access': access_token,
                'refresh': refresh_token
            }, status=status.HTTP_200_OK)

        # If authentication fails, return an error message
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
