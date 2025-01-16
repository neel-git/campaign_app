# Create your views here.
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import PracticeService
from .serializers import (
    PracticeSerializer,
    PracticeDetailSerializer,
    PracticeUserAssignmentSerializer
)
from utils.db_session import get_db_session
from authentication.models import UserRoleType
from rest_framework.exceptions import ValidationError

class PracticeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        with get_db_session() as session:
            service = PracticeService(session)
            # Super admins can see all practices, others see only active ones
            include_inactive = request.user.role == UserRoleType.super_admin
            practices = service.get_all_practices(include_inactive=include_inactive)
            return Response(PracticeSerializer(practices, many=True).data)

    def create(self, request):
        if request.user.role != UserRoleType.super_admin:
            return Response(
                {"error": "Only super admins can create practices"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PracticeSerializer(data=request.data)
        if serializer.is_valid():
            with get_db_session() as session:
                service = PracticeService(session)
                try:
                    practice = service.create_practice(
                        name=serializer.validated_data['name'],
                        description=serializer.validated_data.get('description')
                    )
                    return Response(
                        PracticeSerializer(practice).data,
                        status=status.HTTP_201_CREATED
                    )
                except ValidationError as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        with get_db_session() as session:
            service = PracticeService(session)
            practice = service.get_practice(int(pk))
            if not practice:
                return Response(
                    {"error": "Practice not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(PracticeDetailSerializer(practice).data)

    @action(detail=True, methods=['post'])
    def assign_user(self, request, pk=None):
        if request.user.role != UserRoleType.super_admin:
            return Response(
                {"error": "Only super admins can assign users"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = PracticeUserAssignmentSerializer(data={
            'practice_id': pk,
            'user_id': request.data.get('user_id')
        })

        if serializer.is_valid():
            with get_db_session() as session:
                service = PracticeService(session)
                try:
                    assignment = service.assign_user_to_practice(
                        practice_id=int(pk),
                        user_id=serializer.validated_data['user_id']
                    )
                    return Response(
                        PracticeUserAssignmentSerializer(assignment).data,
                        status=status.HTTP_201_CREATED
                    )
                except ValidationError as e:
                    return Response(
                        {"error": str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
