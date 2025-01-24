# campaigns/services.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from .models import Campaign, CampaignHistory, CampaignPracticeAssociation
from usermessages.models import UserMessage
from authentication.models import User
from practices.models import Practice, PracticeUserAssignment
from rest_framework.exceptions import ValidationError


class CampaignService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_campaign(self, data: Dict[str, Any], user: User) -> Campaign:
        """
        Create a new campaign with proper practice associations based on user role.
        Super admins can target multiple practices while admins are restricted to their own practice.
        """
        # Validate unique campaign name
        if self._campaign_name_exists(data["name"]):
            raise ValidationError("Campaign with this name already exists")

        campaign = Campaign(
            name=data["name"],
            content=data["content"],
            description=data.get("description"),
            campaign_type=(
                "DEFAULT" if user.role == "Practice by Numbers Support" else "CUSTOM"
            ),
            delivery_type=data["delivery_type"],
            status="DRAFT",
            created_by=user.id,
            target_roles=data["target_roles"],
        )

        # Handle practice associations based on user role
        if user.role == "Practice by Numbers Support":
            for practice_id in data["target_practices"]:
                if not self._practice_exists(practice_id):
                    raise ValidationError(
                        f"Practice with id {practice_id} does not exist"
                    )
                association = CampaignPracticeAssociation(practice_id=practice_id)
                campaign.practice_associations.append(association)
        else:
            # Admin users can only target their own practice
            association = CampaignPracticeAssociation(practice_id=user.practice_id)
            campaign.practice_associations.append(association)

        try:
            self.db.add(campaign)
            self.db.commit()
            self.db.refresh(campaign)

            # Record creation in history
            self._record_history(
                campaign.id,
                "CREATED",
                f"Campaign created with delivery type: {data['delivery_type']}",
                user.id,
            )

            return campaign
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create campaign: {str(e)}")

    def send_immediate_campaign(
        self, campaign_id: int, user: User
    ) -> List[UserMessage]:
        """
        Send an immediate campaign to all eligible users based on practice associations
        and target roles.
        """
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        # Verify permissions and campaign state
        self._validate_campaign_send(campaign, user)

        try:
            # Update campaign status to IN_PROGRESS
            campaign.status = "IN_PROGRESS"
            self.db.commit()

            # Get target users and create messages
            target_users = self._get_target_users(campaign)
            if not target_users:
                raise ValidationError("No eligible users found for this campaign")

            messages = []
            for target_user in target_users:
                message = UserMessage(
                    user_id=target_user.id,
                    campaign_id=campaign.id,
                    content=campaign.content,
                    created_at=func.now(),
                )
                messages.append(message)

            # Bulk insert messages
            self.db.bulk_save_objects(messages)

            # Update campaign status to COMPLETED
            campaign.status = "COMPLETED"
            self.db.commit()

            # Record successful send in history
            self._record_history(
                campaign.id,
                "SENT",
                f"Campaign sent successfully to {len(messages)} users",
                user.id,
            )

            return messages

        except Exception as e:
            self.db.rollback()
            campaign.status = "FAILED"
            self.db.commit()
            raise ValidationError(f"Failed to send campaign: {str(e)}")

    def update_campaign(
        self, campaign_id: int, data: Dict[str, Any], user: User
    ) -> Campaign:
        """
        Update an existing campaign while maintaining proper access controls
        and practice associations.
        """
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        # Verify update permissions
        if not self._can_modify_campaign(campaign, user):
            raise ValidationError("Not authorized to modify this campaign")

        # Validate name uniqueness if being updated
        if "name" in data and data["name"] != campaign.name:
            if self._campaign_name_exists(data["name"]):
                raise ValidationError("Campaign with this name already exists")

        try:
            # Update basic fields
            for key in [
                "name",
                "content",
                "description",
                "delivery_type",
                "target_roles",
            ]:
                if key in data:
                    setattr(campaign, key, data[key])

            # Update practice associations for super admin
            if (
                user.role == "Practice by Numbers Support"
                and "target_practices" in data
            ):
                # Clear existing associations
                campaign.practice_associations = []
                # Create new associations
                for practice_id in data["target_practices"]:
                    if self._practice_exists(practice_id):
                        association = CampaignPracticeAssociation(
                            practice_id=practice_id
                        )
                        campaign.practice_associations.append(association)

            campaign.updated_at = func.now()
            self.db.commit()
            self.db.refresh(campaign)

            # Record update in history
            self._record_history(
                campaign.id, "UPDATED", "Campaign details updated", user.id
            )

            return campaign

        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update campaign: {str(e)}")

    def delete_campaign(self, campaign_id: int, user: User) -> bool:
        """Delete a campaign and all its associated data"""
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            raise ValidationError("Campaign not found")

        if not self._can_modify_campaign(campaign, user):
            raise ValidationError("Not authorized to delete this campaign")

        try:
            # Record deletion in history before deleting
            self._record_history(campaign.id, "DELETED", "Campaign deleted", user.id)

            self.db.delete(campaign)
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete campaign: {str(e)}")

    def list_campaigns(self, user: User) -> List[Campaign]:
        """List campaigns based on user role and access rights"""
        try:
            query = self.db.query(Campaign)

            if user.role == "Practice by Numbers Support":
                # Super admins see all campaigns
                return query.all()
            elif user.role == "Admin":
                # Admins see their practice's campaigns and all DEFAULT campaigns
                return query.filter(
                    or_(
                        Campaign.campaign_type == "DEFAULT",
                        and_(
                            Campaign.campaign_type == "CUSTOM",
                            Campaign.created_by == user.id,
                        ),
                    )
                ).all()
            else:
                return []

        except Exception as e:
            raise ValidationError(f"Failed to fetch campaigns: {str(e)}")

    def _get_target_users(self, campaign: Campaign) -> List[User]:
        """Get all eligible users for a campaign based on practices and roles"""
        # Get practice IDs from associations
        practice_ids = [assoc.practice_id for assoc in campaign.practice_associations]

        # Get user IDs assigned to these practices
        practice_user_ids = (
            self.db.query(PracticeUserAssignment.user_id)
            .filter(PracticeUserAssignment.practice_id.in_(practice_ids))
            .distinct()
            .all()
        )
        user_ids = [id[0] for id in practice_user_ids]

        # Filter users by role and active status
        return (
            self.db.query(User)
            .filter(
                User.id.in_(user_ids),
                User.role.in_(campaign.target_roles),
                User.is_active == True,
            )
            .all()
        )

    def _validate_campaign_send(self, campaign: Campaign, user: User):
        """Validate if campaign can be sent"""
        if campaign.status != "DRAFT":
            raise ValidationError("Only DRAFT campaigns can be sent")

        if campaign.delivery_type != "IMMEDIATE":
            raise ValidationError("Only IMMEDIATE campaigns can be sent directly")

        if not self._can_modify_campaign(campaign, user):
            raise ValidationError("Not authorized to send this campaign")

    def _can_modify_campaign(self, campaign: Campaign, user: User) -> bool:
        """Check if user has permission to modify/delete campaign"""
        if user.role == "Practice by Numbers Support":
            return True
        if user.role == "Admin":
            return campaign.created_by == user.id
        return False

    # Helper methods for validation and DB operations
    def _campaign_name_exists(self, name: str) -> bool:
        return self.db.query(Campaign).filter(Campaign.name == name).first() is not None

    def _practice_exists(self, practice_id: int) -> bool:
        return (
            self.db.query(Practice).filter(Practice.id == practice_id).first()
            is not None
        )

    def _get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        return self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

    def _record_history(
        self, campaign_id: int, action: str, details: str, user_id: int
    ):
        """Record campaign action in history"""
        history = CampaignHistory(
            campaign_id=campaign_id,
            action=action,
            details=details,
            performed_by=user_id,
        )
        self.db.add(history)
        self.db.commit()
