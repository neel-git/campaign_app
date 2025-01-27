from typing import List, Optional
from sqlalchemy.orm import Session
from rest_framework.exceptions import ValidationError
from .models import UserMessage
from sqlalchemy.sql import func


class MessageService:
    def __init__(self, db_session):
        self.db = db_session

    def list_messages(self, user_id: int) -> List[UserMessage]:
        return (
            self.db.query(UserMessage)
            .filter(UserMessage.user_id == user_id, UserMessage.is_deleted == False)
            .order_by(UserMessage.created_at.desc())
            .all()
        )

    def mark_as_read(self, message_id: int, user_id: int) -> UserMessage:
        message = self._get_user_message(message_id, user_id)
        if not message:
            raise ValidationError("Message not found")

        message.is_read = True
        message.read_at = func.now()
        self.db.commit()
        return message

    def delete_message(self, message_id: int, user_id: int) -> bool:
        message = self._get_user_message(message_id, user_id)
        if not message:
            raise ValidationError("Message not found")

        message.is_deleted = True
        message.deleted_at = func.now()
        self.db.commit()
        return True

    def _get_user_message(self, message_id: int, user_id: int) -> Optional[UserMessage]:
        return (
            self.db.query(UserMessage)
            .filter(
                UserMessage.id == message_id,
                UserMessage.user_id == user_id,
                UserMessage.is_deleted == False,
            )
            .first()
        )
