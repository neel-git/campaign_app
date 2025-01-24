# campaigns/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import CampaignService
from .models import CampaignHistory
from .serializers import (
    CampaignSerializer,
    CampaignListSerializer,
    CampaignHistorySerializer,
)
from utils.db_session import get_db_session


class CampaignViewSet(viewsets.ViewSet):
    """
    ViewSet for managing campaign operations with proper access control
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        List campaigns based on user role and permissions
        Super admins see all campaigns
        Admins see their own campaigns and DEFAULT campaigns
        """
        with get_db_session() as session:
            service = CampaignService(session)
            try:
                campaigns = service.list_campaigns(request.user)
                return Response(CampaignListSerializer(campaigns, many=True).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        """
        Create a new campaign with proper validation and practice associations
        """
        serializer = CampaignSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                with get_db_session() as session:
                    service = CampaignService(session)
                    campaign = service.create_campaign(
                        serializer.validated_data, request.user
                    )
                    return Response(
                        CampaignSerializer(campaign).data,
                        status=status.HTTP_201_CREATED,
                    )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """
        Get detailed campaign information if user has access
        """
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

    def update(self, request, pk=None):
        """
        Update campaign details with proper validation
        """
        serializer = CampaignSerializer(
            data=request.data, context={"request": request}, partial=True
        )
        if serializer.is_valid():
            try:
                with get_db_session() as session:
                    service = CampaignService(session)
                    campaign = service.update_campaign(
                        int(pk), serializer.validated_data, request.user
                    )
                    return Response(CampaignSerializer(campaign).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        Delete a campaign if user has proper permissions
        """
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

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """
        Get campaign history entries
        """
        with get_db_session() as session:
            service = CampaignService(session)
            try:
                campaign = service._get_campaign(int(pk))
                if not campaign:
                    return Response(
                        {"error": "Campaign not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Get campaign history
                history = (
                    session.query(CampaignHistory)
                    .filter(CampaignHistory.campaign_id == pk)
                    .order_by(CampaignHistory.created_at.desc())
                    .all()
                )

                return Response(CampaignHistorySerializer(history, many=True).data)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
