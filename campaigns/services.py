# campaigns/services.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from .models import (
    Campaign,
    CampaignHistory,
    CampaignPracticeAssociation,
    CampaignSchedule,
)
from usermessages.models import UserMessage
from authentication.models import User, UserRoles
from practices.models import Practice, PracticeUserAssignment
from rest_framework.exceptions import ValidationError


class CampaignService:
    def __init__(self, db_session: Session, user=None):
        self.db = db_session
        self.user = user

    def create_campaign(self, data: Dict[str, Any], user: User) -> Campaign:
        if self._campaign_name_exists(data["name"]):
            raise ValidationError("Campaign with this name already exists")

        try:
            # Set campaign type based on user role
            campaign_type = (
                "DEFAULT" if user.role == UserRoles.SUPER_ADMIN else "CUSTOM"
            )

            # Create campaign
            campaign = Campaign(
                name=data["name"],
                content=data["content"],
                description=data.get("description"),
                campaign_type=campaign_type,
                delivery_type=data["delivery_type"],
                status="DRAFT",
                created_by=user.id,
                target_roles=data["target_roles"],
            )

            if user.role == UserRoles.SUPER_ADMIN:
                for practice_id in data["target_practices"]:
                    if not self._practice_exists(practice_id):
                        raise ValidationError(
                            f"Practice with id {practice_id} does not exist"
                        )
                    association = CampaignPracticeAssociation(practice_id=practice_id)
                    campaign.practice_associations.append(association)
            else:
                practice_assignment = (
                    self.db.query(PracticeUserAssignment)
                    .filter(PracticeUserAssignment.user_id == user.id)
                    .first()
                )

                if not practice_assignment:
                    raise ValidationError("Admin user is not assigned to any practice")

                association = CampaignPracticeAssociation(
                    practice_id=practice_assignment.practice_id
                )
                campaign.practice_associations.append(association)

            self.db.add(campaign)
            self.db.flush()

            if data["delivery_type"] == "SCHEDULED":
                if "scheduled_date" not in data:
                    raise ValidationError(
                        "Scheduled date is required for SCHEDULED campaigns"
                    )

                schedule = CampaignSchedule(
                    campaign_id=campaign.id,
                    scheduled_date=data["scheduled_date"],
                    status="PENDING",
                    created_at=datetime.utcnow(),
                )
                self.db.add(schedule)

            self.db.commit()
            self.db.refresh(campaign)

            # Record history
            self._record_history(
                campaign.id,
                "CREATED",
                f"Campaign created with type: {campaign_type}, delivery: {data['delivery_type']}"
                + (
                    f" scheduled for {data['scheduled_date']}"
                    if data["delivery_type"] == "SCHEDULED"
                    else ""
                ),
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

            current_time = datetime.utcnow()
            messages = []
            for target_user in target_users:
                message = UserMessage(
                    user_id=target_user.id,
                    campaign_id=campaign.id,
                    content=campaign.content,
                    created_at=current_time,
                )
                messages.append(message)

            
            self.db.bulk_save_objects(messages)
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

            if (
                user.role == "Practice by Numbers Support"
                and "target_practices" in data
            ):
                campaign.practice_associations = []
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
        practice_ids = [assoc.practice_id for assoc in campaign.practice_associations]
        target_roles = [
            (
                "Admin"
                if role == "Admin"
                else "Practice User" if role == "Practice User" else role
            )
            for role in campaign.target_roles
        ]
        
        # Get all users first
        users = (
            self.db.query(User)
            .join(PracticeUserAssignment, User.id == PracticeUserAssignment.user_id)
            .filter(
                PracticeUserAssignment.practice_id.in_(practice_ids),
                User.role.in_(target_roles),
                User.is_active == True,
                User.is_approved == True,  # Add this condition
            )
            .distinct()
            .all()
        )
        return users

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

    def get_user_campaigns(self, user_id: int) -> List[Campaign]:
        try:
            query = self.db.query(Campaign)

            if self.user.role == UserRoles.SUPER_ADMIN:
                # Super admins see all campaigns
                campaigns = query.order_by(Campaign.created_at.desc()).all()

            elif self.user.role == UserRoles.ADMIN:
                campaigns = (
                    query.filter(
                        Campaign.created_by == user_id,  # Only their own campaigns
                        Campaign.campaign_type == "CUSTOM",  # Only CUSTOM type
                    )
                    .order_by(Campaign.created_at.desc())
                    .all()
                )

            else:
                campaigns = []

            return campaigns

        except Exception as e:
            error_msg = f"Failed to fetch user campaigns: {str(e)}"
            raise ValidationError(error_msg)