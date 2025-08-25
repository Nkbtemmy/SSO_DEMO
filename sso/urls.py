from django.urls import path
from sso import views

urlpatterns = [
    path("login/azure/", views.azure_login, name="azure_login"),
    path("callback/", views.azure_callback, name="azure_callback"),
]
