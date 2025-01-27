# campaigns/serializers.py
from rest_framework import serializers
from utils.db_session import get_db_session
from .models import Campaign, CampaignPracticeAssociation
from practices.models import PracticeUserAssignment
from authentication.serializers import UserSerializer
from practices.serializers import PracticeSerializer
from datetime import datetime, timezone


class CampaignPracticeAssociationSerializer(serializers.Serializer):
    """
    Serializer for displaying practice associations with basic practice details
    """

    practice_id = serializers.IntegerField()
    practice = serializers.SerializerMethodField()

    def get_practice(self, obj):
        return {
            "id": obj.practice.id,
            "name": obj.practice.name,
            "description": obj.practice.description,
        }


class CampaignSerializer(serializers.Serializer):
    """
    Main campaign serializer with full validation and relationship handling
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    content = serializers.CharField()
    description = serializers.CharField(required=False, allow_null=True)
    campaign_type = serializers.CharField()  # DEFAULT/CUSTOM
    delivery_type = serializers.CharField()  # IMMEDIATE/SCHEDULED
    status = serializers.CharField(read_only=True)
    target_roles = serializers.ListField(child=serializers.CharField())
    target_practices = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )
    practice_associations = CampaignPracticeAssociationSerializer(
        many=True, read_only=True
    )
    scheduled_date = serializers.DateTimeField(required=False)
    creator = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_creator(self, obj):
        """Returns basic information about campaign creator"""
        return {
            "id": obj.creator.id,
            "full_name": obj.creator.full_name,
            "role": obj.creator.role,
        }

    def validate(self, data):
        """
        Custom validation to enforce business rules around campaign creation and handle role format conversion
        """
        request = self.context.get("request")
        db_session = self.context.get("db_session") 

        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        if not db_session:
            raise serializers.ValidationError("Database session required")
        
        # First, convert the target roles from frontend format to backend format
        # Frontend sends: 'ADMIN', 'PRACTICE USER'
        # Backend expects: 'Admin', 'Practice User'
        if "target_roles" in data:
            data["target_roles"] = [
                (
                    "Admin"
                    if role == "Admin"
                    else "Practice User" if role == "Practice User" else role
                )
                for role in data["target_roles"]
            ]

        # Validate campaign type based on user role
        if (
            request.user.role != "Practice by Numbers Support"
            and data.get("campaign_type") == "DEFAULT"
        ):
            raise serializers.ValidationError(
                "Only super admins can create DEFAULT campaigns"
            )

        # Validate target roles based on user role
        if request.user.role == "Admin":
            # Admins can only target practice users
            # Note: We're now checking against 'Practice User' (backend format)
            invalid_roles = [
                role for role in data.get("target_roles", []) if role != "Practice User"
            ]
            if invalid_roles:
                raise serializers.ValidationError(
                    "Admins can only target Practice Users"
                )

            # Get admin's practice ID from practice_user_assignments
            practice_assignment = (
            db_session.query(PracticeUserAssignment)  # Use db_session from context
            .filter(PracticeUserAssignment.user_id == request.user.id)
            .first()
            )

            if not practice_assignment:
                raise serializers.ValidationError("Admin not assigned to any practice")

            # Admins must target their own practice
            practice_id = practice_assignment.practice_id
            if data.get("target_practices") and (
                len(data["target_practices"]) != 1
                or data["target_practices"][0] != practice_id
            ):
                raise serializers.ValidationError(
                    "Admins can only target their own practice"
                )
            # # Admins must target their own practice
            # practice_id = request.user.practice_id
            # if data.get("target_practices") and (
            #     len(data["target_practices"]) != 1
            #     or data["target_practices"][0] != practice_id
            # ):
            #     raise serializers.ValidationError(
            #         "Admins can only target their own practice"
            #     )

        if data.get("delivery_type") == "SCHEDULED" and not data.get("scheduled_date"):
            raise serializers.ValidationError(
                {"scheduled_date": "Scheduled date is required for SCHEDULED campaigns"}
            )

        if data.get("scheduled_date") and data.get("delivery_type") != "SCHEDULED":
            raise serializers.ValidationError(
                {
                    "scheduled_date": "Scheduled date should only be provided for SCHEDULED campaigns"
                }
            )

        # Validate that scheduled date is in the future
        if data.get("scheduled_date"):
            if data["scheduled_date"] <= datetime.now(timezone.utc):
                raise serializers.ValidationError(
                    {"scheduled_date": "Scheduled date must be in the future"}
                )

        return data


class CampaignListSerializer(serializers.Serializer):
    """
    Simplified serializer for list views with essential fields
    """

    id = serializers.IntegerField()
    name = serializers.CharField()
    campaign_type = serializers.CharField()
    delivery_type = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    target_practices = serializers.SerializerMethodField()

    def get_target_practices(self, obj):
        return [
            {"id": assoc.practice_id, "name": assoc.practice.name}
            for assoc in obj.practice_associations
        ]


class CampaignHistorySerializer(serializers.Serializer):
    """
    Serializer for campaign history entries
    """

    action = serializers.CharField()
    details = serializers.CharField()
    performed_by = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_performed_by(self, obj):
        return {
            "id": obj.performed_by,
            "full_name": obj.performer.full_name,
            "role": obj.performer.role,
        }
