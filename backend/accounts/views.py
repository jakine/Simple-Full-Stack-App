from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import LoginSerializer, RegisterSerializer
from .services import login_user, logout_user, register_user, user_payload


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    user = login_user(request, email, password)
    if user is None:
        return Response(
            {"detail": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response(user_payload(user, request))


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = register_user(
        request,
        serializer.validated_data["email"],
        serializer.validated_data["password"],
    )
    return Response(user_payload(user, request), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout_user(request)
    return Response({"detail": "Logged out successfully."})


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(user_payload(request.user, request))