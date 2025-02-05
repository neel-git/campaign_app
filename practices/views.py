# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .services import PracticeService
from .serializers import (
    PracticeSerializer,
    PracticeDetailSerializer,
    PracticeUserAssignmentSerializer,
)
from utils.db_session import get_db_session
from authentication.models import UserRoles
from rest_framework.exceptions import ValidationError


class PracticeViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action == "list":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request):
        """
        List practices based on user role:
        - Super admin: sees all practices (active and inactive)
        - Authenticated users: see all active practices
        - Unauthenticated users: see all active practices
        """
        with get_db_session() as session:
            service = PracticeService(session)

            # Determine if we should include inactive practices
            if (
                request.user.is_authenticated
                and request.user.role == UserRoles.SUPER_ADMIN
            ):
                # Super admin sees everything
                practices = service.get_all_practices(include_inactive=True)
            else:
                # Everyone else only sees active practices
                practices = service.get_all_practices(include_inactive=False)

            return Response(PracticeSerializer(practices, many=True).data)

    permission_classes = [IsAuthenticated]

    def create(self, request):
        if request.user.role != UserRoles.SUPER_ADMIN:
            return Response(
                {"error": "Only super admins can create practices"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PracticeSerializer(data=request.data)
        if serializer.is_valid():
            with get_db_session() as session:
                service = PracticeService(session)
                try:
                    practice = service.create_practice(
                        name=serializer.validated_data["name"],
                        description=serializer.validated_data.get("description"),
                    )
                    return Response(
                        PracticeSerializer(practice).data,
                        status=status.HTTP_201_CREATED,
                    )
                except ValidationError as e:
                    return Response(
                        {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
                    )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        with get_db_session() as session:
            service = PracticeService(session)
            practice = service.get_practice(int(pk))
            if not practice:
                return Response(
                    {"error": "Practice not found"}, status=status.HTTP_404_NOT_FOUND
                )
            return Response(PracticeDetailSerializer(practice).data)

    @action(detail=True, methods=["post"])
    def approve_user_assignment(self, request, pk=None):
        user_id = request.data.get("user_id")
        role = request.data.get("role")

        if not user_id or not role:
            return Response(
                {"error": "User ID and role are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check permissions
        if (request.user.role != UserRoles.SUPER_ADMIN and role == UserRoles.ADMIN) or (
            request.user.role != UserRoles.ADMIN and role == UserRoles.PRACTICE_USER
        ):
            return Response(
                {"error": "Insufficient permissions"}, status=status.HTTP_403_FORBIDDEN
            )

        with get_db_session() as session:
            service = PracticeService(session)
            try:
                assignment = service.assign_user_to_practice(
                    practice_id=int(pk), user_id=user_id, user_role=role
                )
                return Response(
                    PracticeUserAssignmentSerializer(assignment).data,
                    status=status.HTTP_201_CREATED,
                )
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        if request.user.role != UserRoles.SUPER_ADMIN:
            return Response(
                {"error": "Only super admins can update practices"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PracticeSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            try:
                with get_db_session() as session:
                    service = PracticeService(session)
                    practice = service.update_practice(
                        practice_id=int(pk), **serializer.validated_data
                    )
                    return Response(PracticeSerializer(practice).data)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {"error": "Failed to update practice"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        if request.user.role != UserRoles.SUPER_ADMIN:
            return Response(
                {"error": "Only super admins can delete practices"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            with get_db_session() as session:
                service = PracticeService(session)
                practice = service.get_practice(int(pk))
                if not practice:
                    return Response(
                        {"error": "Practice not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Delete practicea
                session.delete(practice)
                session.commit()
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_practice(self, request):
        try:
            with get_db_session() as session:
                service = PracticeService(session)
                practice = service.get_user_practice(request.user.id)
                
                if not practice:
                    return Response(
                        {"error": "No practice assignment found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
                return Response(PracticeSerializer(practice).data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )