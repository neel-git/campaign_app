# practices/services.py
from typing import Optional, List
from sqlalchemy.orm import Session
from .models import Practice, PracticeUserAssignment
from authentication.models import User
from rest_framework.exceptions import ValidationError


class PracticeService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_practice(self, name: str, description: Optional[str] = None) -> Practice:
        existing = self.db.query(Practice).filter(Practice.name == name).first()
        if existing:
            raise ValidationError("Practice with this name already exists")

        practice = Practice(name=name, description=description)
        self.db.add(practice)
        self.db.commit()
        self.db.refresh(practice)
        return practice

    def get_practice(self, practice_id: int) -> Optional[Practice]:
        try:
            return self.db.query(Practice).filter(Practice.id == practice_id).first()
        except Exception as e:
            raise ValidationError(f"Failed to fetch practice: {str(e)}")

    def get_all_practices(self, include_inactive: bool = False) -> List[Practice]:
        try:
            query = self.db.query(Practice)

            if not include_inactive:
                # Only return active practices
                query = query.filter(Practice.is_active == True)

            # Order by name for consistency
            return query.order_by(Practice.name).all()

        except Exception as e:
            raise ValidationError(f"Failed to fetch practices: {str(e)}")

    def remove_user_from_practice(self, practice_id: int, user_id: int) -> bool:
        assignment = (
            self.db.query(PracticeUserAssignment)
            .filter_by(practice_id=practice_id, user_id=user_id)
            .first()
        )

        if assignment:
            self.db.delete(assignment)
            self.db.commit()
            return True
        return False

    def get_practice_users(self, practice_id: int) -> List[User]:
        assignments = (
            self.db.query(PracticeUserAssignment)
            .filter_by(practice_id=practice_id)
            .all()
        )
        return [self.db.query(User).get(a.user_id) for a in assignments]

    def update_practice(self, practice_id: int, **kwargs) -> Optional[Practice]:
        try:
            practice = (
                self.db.query(Practice).filter(Practice.id == practice_id).first()
            )
            if not practice:
                raise ValidationError("Practice not found")

            # Check if name is being updated and if it already exists
            if "name" in kwargs:
                existing = (
                    self.db.query(Practice)
                    .filter(Practice.name == kwargs["name"], Practice.id != practice_id)
                    .first()
                )
                if existing:
                    raise ValidationError("Practice with this name already exists")

            # Update allowed fields
            allowed_fields = ["name", "description", "is_active"]
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(practice, key, value)

            self.db.commit()
            self.db.refresh(practice)
            return practice
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update practice: {str(e)}")
        
    def get_user_practice(self, user_id: int) -> Optional[Practice]:
        try:
            # Find the practice assignment for this user
            assignment = (
                self.db.query(PracticeUserAssignment)
                .filter(PracticeUserAssignment.user_id == user_id)
                .first()
            )
            
            if assignment:
                # Get the practice details
                practice = self.get_practice(assignment.practice_id)
                return practice
                
            return None
        except Exception as e:
            raise ValidationError(f"Failed to fetch user's practice: {str(e)}")