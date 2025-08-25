def azure_callback(request):
    code = request.GET.get("code")
    msal_app = msal.ConfidentialClientApplication(
        client_id=settings.AZURE_CLIENT_ID,
        authority=settings.AZURE_AUTHORITY,
        client_credential=settings.AZURE_CLIENT_SECRET,
    )
    token_result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=settings.AZURE_SCOPE,
        redirect_uri=settings.AZURE_REDIRECT_URI,
    )
    user_info = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {token_result['access_token']}"}
    ).json()

    email = user_info["mail"]
    domain = email.split("@")[-1]

    # find or create organisation by domain
    org, _ = Organisation.objects.get_or_create(domain=domain, defaults={"name": domain})

    user, _ = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": user_info.get("givenName", ""),
            "last_name": user_info.get("surname", ""),
            "organisation": org
        }
    )
    login(request, user)
    return redirect("/")
