# messages/views.py 
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.db_session import get_db_session
from .services import MessageService
from .serializers import MessageSerializer

class MessageViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        with get_db_session() as session:
            service = MessageService(session)
            messages = service.list_messages(request.user.id)
            return Response(MessageSerializer(messages, many=True).data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        try:
            with get_db_session() as session:
                service = MessageService(session)
                service.mark_as_read(int(pk), request.user.id)
                return Response({"message": "Marked as read"})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def delete(self, request, pk=None):
        try:
            with get_db_session() as session:
                service = MessageService(session)
                service.delete_message(int(pk), request.user.id)
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )