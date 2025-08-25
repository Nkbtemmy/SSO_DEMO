from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class PostLoginJWTView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({"detail": "Not authenticated"}, status=401)
        refresh = RefreshToken.for_user(request.user)
        refresh["email"] = request.user.email
        refresh["org_id"] = str(getattr(request.user.organisation, "id", "")) if getattr(request.user, "organisation", None) else ""
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})
