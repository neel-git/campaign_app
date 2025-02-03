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
    UserRegistrationRequestSerializer,
    RoleChangeRequestSerializer,
)
from .models import User, UserRegistrationRequest, RoleChangeRequest, UserRoles
from practices.models import PracticeUserAssignment
from rest_framework.exceptions import ValidationError
from django.middleware.csrf import get_token
from django.http import JsonResponse
from utils.db_session import get_db_session
from .services import UserRegistrationRequestService


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
                    # Create user without role
                    user = serializer.create(serializer.validated_data)
                    session.add(user)
                    session.commit()
                    session.refresh(user)

                    # Create registration request
                    request_service = UserRegistrationRequestService(session)
                    registration_request = request_service.create_request(
                        user_id=user.id,
                        practice_id=serializer.validated_data["desired_practice_id"],
                        requested_role=serializer.validated_data["requested_role"],
                    )

                    return Response(
                        {
                            "message": "Registration successful. Waiting for admin approval.",
                            "user": UserSerializer(user).data,
                        },
                        status=status.HTTP_201_CREATED,
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

                    if not user.is_approved:
                        return Response(
                            {"error": "Account is pending approval"},
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

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def pending_request(self, request):
        """Get pending requests based on user role"""
        try:
            with get_db_session() as session:
                service = UserRegistrationRequestService(session)

                # Handle super admin requests
                if request.user.role == UserRoles.SUPER_ADMIN:
                    requests = service.get_super_admin_pending_requests()

                # Handle practice admin requests
                elif request.user.role == UserRoles.ADMIN:
                    practice_assignment = (
                        session.query(PracticeUserAssignment)
                        .filter(PracticeUserAssignment.user_id == request.user.id)
                        .first()
                    )

                    if not practice_assignment:
                        return Response(
                            {"error": "Admin not assigned to any practice"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    requests = service.get_admin_pending_requests(
                        practice_assignment.practice_id
                    )
                else:
                    return Response(
                        {"error": "Insufficient permissions"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # Serialize response
                return Response(
                    {
                        "registration_requests": UserRegistrationRequestSerializer(
                            requests["registration_requests"], many=True
                        ).data,
                        "role_change_requests": RoleChangeRequestSerializer(
                            requests["role_change_requests"], many=True
                        ).data,
                    }
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def request_role_change(self, request):
        """Request a role change for current user"""
        serializer = RoleChangeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with get_db_session() as session:
                # Get user's practice
                practice_assignment = (
                    session.query(PracticeUserAssignment)
                    .filter(PracticeUserAssignment.user_id == request.user.id)
                    .first()
                )

                if not practice_assignment:
                    return Response(
                        {"error": "User not assigned to any practice"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                service = UserRegistrationRequestService(session)
                role_request = service.create_role_change_request(
                    user_id=request.user.id,
                    practice_id=practice_assignment.practice_id,
                    requested_role=serializer.validated_data["requested_role"],
                )

                return Response(
                    RoleChangeRequestSerializer(role_request).data,
                    status=status.HTTP_201_CREATED,
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def approve_request(self, request, pk=None):
        """Approve registration or role change request"""
        request_type = request.data.get("request_type")
        if not request_type:
            return Response(
                {"error": "Request type is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with get_db_session() as session:
                # Validate permissions
                if request.user.role == UserRoles.ADMIN:
                    # Get admin's practice
                    practice_assignment = (
                        session.query(PracticeUserAssignment)
                        .filter(PracticeUserAssignment.user_id == request.user.id)
                        .first()
                    )

                    if not practice_assignment:
                        return Response(
                            {"error": "Admin not assigned to any practice"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Verify request belongs to admin's practice
                    if request_type == "role_change":
                        req = session.query(RoleChangeRequest).get(int(pk))
                    else:
                        req = session.query(UserRegistrationRequest).get(int(pk))
                        practice_id = req.desired_practice_id if req else None

                    if not req or practice_id != practice_assignment.practice_id:
                        return Response(
                            {"error": "Request not found"},
                            status=status.HTTP_404_NOT_FOUND,
                        )

                service = UserRegistrationRequestService(session)
                result = service.handle_request_approval(
                    request_id=int(pk),
                    request_type=request_type,
                    reviewer_id=request.user.id,
                )

                serializer = (
                    UserRegistrationRequestSerializer
                    if request_type == "registration"
                    else RoleChangeRequestSerializer
                )
                return Response(serializer(result).data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reject_request(self, request, pk=None):
        """Reject registration or role change request"""
        request_type = request.data.get("request_type")
        reason = request.data.get("reason")

        if not all([request_type, reason]):
            return Response(
                {"error": "Request type and reason are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with get_db_session() as session:
                # Similar permission validation as approve_request
                if request.user.role == UserRoles.ADMIN:
                    practice_assignment = (
                        session.query(PracticeUserAssignment)
                        .filter(PracticeUserAssignment.user_id == request.user.id)
                        .first()
                    )

                    if not practice_assignment:
                        return Response(
                            {"error": "Admin not assigned to any practice"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Verify request belongs to admin's practice
                    if request_type == "role_change":
                        req = session.query(RoleChangeRequest).get(int(pk))
                    else:
                        req = session.query(UserRegistrationRequest).get(int(pk))

                    if not req or req.desired_practice_id != practice_assignment.practice_id:
                        return Response(
                            {"error": "Request not found"},
                            status=status.HTTP_404_NOT_FOUND,
                        )

                    # Verify admin can only reject practice user requests
                    if req.requested_role != UserRoles.PRACTICE_USER:
                        return Response(
                            {"error": "Admins can only handle practice user requests"},
                            status=status.HTTP_403_FORBIDDEN,
                        )

                elif request.user.role != UserRoles.SUPER_ADMIN:
                    return Response(
                        {"error": "Insufficient permissions"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

                service = UserRegistrationRequestService(session)
                result = service.handle_request_rejection(
                    request_id=int(pk),
                    request_type=request_type,
                    reviewer_id=request.user.id,
                    reason=reason,
                )

                serializer = (
                    UserRegistrationRequestSerializer
                    if request_type == "registration"
                    else RoleChangeRequestSerializer
                )
                return Response(serializer(result).data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
