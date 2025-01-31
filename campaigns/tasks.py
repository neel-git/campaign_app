from core.celery import app
from datetime import datetime, timezone
from utils.db_session import get_db_session
from .models import Campaign, CampaignSchedule
from .services import CampaignService
from usermessages.models import UserMessage
from sqlalchemy import and_


@app.task
def check_scheduled_campaigns():
    """Check and process any pending scheduled campaigns"""
    print("Starting scheduled campaigns check...")
    with get_db_session() as session:
        try:
            pending_schedules = (
                session.query(CampaignSchedule)
                .join(Campaign)
                .filter(
                    and_(
                        CampaignSchedule.status == "PENDING",
                        CampaignSchedule.scheduled_date <= datetime.now(timezone.utc),
                        Campaign.status == "DRAFT",
                    )
                )
                .all()
            )

            for schedule in pending_schedules:
                process_scheduled_campaign.delay(schedule.id)

        except Exception as e:
            print(f"Error checking scheduled campaigns: {str(e)}")


@app.task
def process_scheduled_campaign(schedule_id: int):
    with get_db_session() as session:
        try:
            schedule = session.query(CampaignSchedule).get(schedule_id)
            if not schedule:
                return

            campaign = schedule.campaign
            if not campaign:
                return

            user = campaign.creator

            service = CampaignService(session)

            campaign.status = "IN_PROGRESS"
            session.commit()

            target_users = service._get_target_users(campaign)

            if not target_users:
                raise ValueError("No eligible users found for this campaign")

            current_time = datetime.now(timezone.utc)
            messages = []
            for target_user in target_users:
                message = UserMessage(
                    user_id=target_user.id,
                    campaign_id=campaign.id,
                    content=campaign.content,
                    created_at=current_time,
                )
                messages.append(message)

            session.bulk_save_objects(messages)

            schedule.status = "PROCESSED"
            schedule.execution_time = current_time
            campaign.status = "COMPLETED"

            service._record_history(
                campaign.id,
                "SENT",
                f"Scheduled campaign sent successfully to {len(messages)} users",
                user.id,
            )

            session.commit()

        except Exception as e:
            if campaign:
                campaign.status = "FAILED"
                schedule.status = "FAILED"
                schedule.error_message = str(e)
                session.commit()
            print(f"Error processing scheduled campaign {schedule_id}: {str(e)}")
