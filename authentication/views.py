# authentication/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from datetime import datetime
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
)
from .models import User, UserRoleType
from django.middleware.csrf import get_token
from django.http import JsonResponse
from utils.db_session import get_db_session


class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def get_csrf_token(self, request):
        return JsonResponse({"csrfToken": get_token(request)})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with get_db_session() as session:
                    # user = User(
                    #     username=serializer.validated_data["username"],
                    #     email=serializer.validated_data["email"],
                    #     role=serializer.validated_data["role"],
                    # )
                    user = serializer.create(serializer.validated_data)
                    user.set_password(serializer.validated_data["password"])
                    session.add(user)
                    session.commit()
                    session.refresh(user)

                    return Response(
                        UserSerializer(user).data, status=status.HTTP_201_CREATED
                    )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with get_db_session() as session:
                    user = (
                        session.query(User)
                        .filter(User.username == serializer.validated_data["username"])
                        .first()
                    )

                    if not user or not user.check_password(
                        serializer.validated_data["password"]
                    ):
                        return Response(
                            {"error": "Invalid credentials"},
                            status=status.HTTP_401_UNAUTHORIZED,
                        )

                    if not user.is_active:
                        return Response(
                            {"error": "Account is disabled"},
                            status=status.HTTP_401_UNAUTHORIZED,
                        )

                    # Update session data
                    user.last_login = datetime.utcnow()
                    user.update_session_expiry()
                    session.commit()

                    # Set session data
                    request.session["user_id"] = user.id
                    request.session.set_expiry(86400)  # 24 hours in seconds

                    return Response(UserSerializer(user).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            with get_db_session() as session:
                user = (
                    session.query(User)
                    .filter(User.id == request.session["user_id"])
                    .first()
                )
                if user:
                    user.session_expires_at = None
                    session.commit()
            request.session.flush()
            return Response({"message": "Logged out successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with get_db_session() as session:
                    user = (
                        session.query(User)
                        .filter(User.id == request.session["user_id"])
                        .first()
                    )

                    if not user.check_password(
                        serializer.validated_data["old_password"]
                    ):
                        return Response(
                            {"error": "Current password is incorrect"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    user.set_password(serializer.validated_data["new_password"])
                    session.commit()

                    return Response({"message": "Password updated successfully"})
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        try:
            with get_db_session() as session:
                user = (
                    session.query(User)
                    .filter(User.id == request.session["user_id"])
                    .first()
                )
                return Response(UserSerializer(user).data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
