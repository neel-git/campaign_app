# campaigns/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import CampaignService
from .models import CampaignHistory,Campaign
from .serializers import (
    CampaignSerializer,
    CampaignListSerializer,
    CampaignHistorySerializer,
)
from utils.db_session import get_db_session


class CampaignViewSet(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]

    def list(self, request):
        with get_db_session() as session:
            service = CampaignService(session)
            try:
                campaigns = service.list_campaigns(request.user)
                return Response(CampaignListSerializer(campaigns, many=True).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        with get_db_session() as session:
            serializer = CampaignSerializer(
                data=request.data,
                context={
                    "request": request,
                    "db_session": session,
                },  # Pass session in context
            )
            if serializer.is_valid():
                try:
                    service = CampaignService(session)
                    campaign = service.create_campaign(
                        serializer.validated_data, request.user
                    )
                    return Response(
                        CampaignSerializer(campaign).data,
                        status=status.HTTP_201_CREATED,
                    )
                except Exception as e:
                    return Response(
                        {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):

        with get_db_session() as session:
            service = CampaignService(session)
            try:
                campaigns = service.list_campaigns(request.user)
                campaign = next((c for c in campaigns if str(c.id) == pk), None)
                if not campaign:
                    return Response(
                        {"error": "Campaign not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                return Response(CampaignSerializer(campaign).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def partial_update(self, request, pk=None):
        
        with get_db_session() as session:
            serializer = CampaignSerializer(
                data=request.data,
                context={
                    "request": request,
                    "db_session": session
                },
                partial=True
            )
            
            if not serializer.is_valid():
                print(f"Serializer errors: {serializer.errors}")
                return Response(
                    {
                        "error": "Validation failed",
                        "details": serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                service = CampaignService(session)
                campaign = service.update_campaign(
                    int(pk),
                    serializer.validated_data,
                    request.user
                )
                return Response(CampaignSerializer(campaign).data)
            except Exception as e:
                print(f"Update error: {str(e)}")
                return Response(
                    {
                        "error": str(e),
                        "details": getattr(e, "detail", str(e))
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

    def destroy(self, request, pk=None):
        
        try:
            with get_db_session() as session:
                service = CampaignService(session)
                service.delete_campaign(int(pk), request.user)
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """
        Send an immediate campaign to target users
        """
        try:
            with get_db_session() as session:
                service = CampaignService(session)
                messages = service.send_immediate_campaign(int(pk), request.user)
                return Response(
                    {
                        "message": f"Campaign sent successfully to {len(messages)} users",
                        "recipients_count": len(messages),
                    }
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=["GET"])
    def my_campaign(self, request):
        with get_db_session() as session:
            try:
                service = CampaignService(session, request.user)
                campaigns = service.get_user_campaigns(request.user.id)
                return Response(CampaignListSerializer(campaigns, many=True).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):

        with get_db_session() as session:
            try:
                # Get campaign
                campaign = session.query(Campaign).get(int(pk))
                if not campaign:
                    return Response(
                        {"error": "Campaign not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Get campaign history with user data
                history = (
                    session.query(CampaignHistory)
                    .filter(CampaignHistory.campaign_id == pk)
                    .order_by(CampaignHistory.created_at.desc())
                    .all()
                )

                return Response(CampaignHistorySerializer(history, many=True).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
