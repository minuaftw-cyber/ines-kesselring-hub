import logging

from django.contrib.auth.models import update_last_login
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class AuthThrottleMixin:
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


def token_response(user, http_status=status.HTTP_200_OK) -> Response:
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data}, status=http_status)


class RegisterView(AuthThrottleMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("New member registered: user_id=%s", user.pk)
        return token_response(user, status.HTTP_201_CREATED)


class LoginView(AuthThrottleMixin, APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            logger.warning("Failed login attempt")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data["user"]
        update_last_login(None, user)
        return token_response(user)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
