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
        """Create a new practice"""
        existing = self.db.query(Practice).filter(Practice.name == name).first()
        if existing:
            raise ValidationError("Practice with this name already exists")

        practice = Practice(name=name, description=description)
        self.db.add(practice)
        self.db.commit()
        self.db.refresh(practice)
        return practice

    def get_practice(self, practice_id: int) -> Optional[Practice]:
        """Get a single practice by ID"""
        try:
            return self.db.query(Practice).filter(Practice.id == practice_id).first()
        except Exception as e:
            raise ValidationError(f"Failed to fetch practice: {str(e)}")

    def get_all_practices(self, include_inactive: bool = False) -> List[Practice]:
        """Get practices based on include_inactive flag"""
        try:
            query = self.db.query(Practice)

            if not include_inactive:
                # Only return active practices
                query = query.filter(Practice.is_active == True)

            # Order by name for consistency
            return query.order_by(Practice.name).all()

        except Exception as e:
            raise ValidationError(f"Failed to fetch practices: {str(e)}")

    # def assign_user_to_practice(
    #     self, practice_id: int, user_id: int, user_role: str
    # ) -> PracticeUserAssignment:
    #     """
    #     Assign a user to a practice and update their role
    #     This will be called during user registration approval
    #     """
    #     try:
    #         with self.db.begin():
    #             # Check if practice exists
    #             practice = self.get_practice(practice_id)
    #             if not practice:
    #                 raise ValidationError("Practice not found")

    #             # Check if user exists
    #             user = self.db.query(User).filter(User.id == user_id).first()
    #             if not user:
    #                 raise ValidationError("User not found")

    #             # Check if assignment already exists
    #             existing = (
    #                 self.db.query(PracticeUserAssignment)
    #                 .filter_by(practice_id=practice_id, user_id=user_id)
    #                 .first()
    #             )
    #             if existing:
    #                 raise ValidationError("User is already assigned to this practice")

    #             # Create the practice assignment
    #             assignment = PracticeUserAssignment(
    #                 practice_id=practice_id, user_id=user_id
    #             )
    #             self.db.add(assignment)

    #             # Update user's role
    #             user.role = user_role
    #             user.is_approved = True

    #             self.db.commit()
    #             self.db.refresh(assignment)
    #             return assignment
    #     except Exception as e:
    #         self.db.rollback()
    #         raise ValidationError(str(e))

    def remove_user_from_practice(self, practice_id: int, user_id: int) -> bool:
        """Remove a user from a practice"""
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
        """Get all users assigned to a practice"""
        assignments = (
            self.db.query(PracticeUserAssignment)
            .filter_by(practice_id=practice_id)
            .all()
        )
        return [self.db.query(User).get(a.user_id) for a in assignments]

    def update_practice(self, practice_id: int, **kwargs) -> Optional[Practice]:
        """Update practice details"""
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
