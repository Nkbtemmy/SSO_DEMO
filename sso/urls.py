from django.urls import path
from sso import views, views_google

urlpatterns = [
    path("login/azure/", views.azure_login, name="azure_login"),
    path("callback/", views.azure_callback, name="azure_callback"),

    # Google OAuth (new)
    path('google/login/', views_google.google_login, name='google_login'),
    path('google/callback/', views_google.google_callback, name='google_callback'),
    path('google/logout/', views_google.google_logout, name='google_logout'),  # Optional
]
