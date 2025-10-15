from django.urls import path
from sso import views, views_google, views_ldap

urlpatterns = [
    path('api/login/', views.LDAPLoginAPIView.as_view(), name='login'),
    path('azure/login/', views.AzureLoginView.as_view(), name='azure_login'),
    path('azure/callback/', views.AzureCallbackView.as_view(), name='azure_callback'),
    path('azure/logout/', views.AzureLogoutView.as_view(), name='azure_logout'),

    # Google OAuth (new)
    path('google/login/', views_google.GoogleLoginView.as_view(), name='google_login'),
    path('google/callback/', views_google.GoogleCallbackView.as_view(), name='google_callback'),
    path('google/logout/', views_google.GoogleLogoutView.as_view(), name='google_logout'),
    path("ldap/login/", views_ldap.LDAPLoginView.as_view(), name="ldap_login"),
]
