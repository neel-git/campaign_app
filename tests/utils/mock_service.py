from rest_framework.exceptions import ValidationError
from tests.utils.mock_models import MockPractice, MockUser, MockPracticeUserAssignment
from typing import Optional, List


class TestPracticeService:
    """Tesing using mock service"""

    def __init__(self, db_session):
        self.db = db_session

    def create_practice(
        self, name: str, description: Optional[str] = None
    ) -> MockPractice:
        existing = self.db.query(MockPractice).filter(MockPractice.name == name).first()
        if existing:
            raise ValidationError("Practice with this name already exists")

        practice = MockPractice(name=name, description=description)
        self.db.add(practice)
        self.db.commit()
        self.db.refresh(practice)
        return practice

    def get_practice(self, practice_id: int) -> Optional[MockPractice]:
        try:
            return (
                self.db.query(MockPractice)
                .filter(MockPractice.id == practice_id)
                .first()
            )
        except Exception as e:
            raise ValidationError(f"Failed to fetch practice: {str(e)}")

    def get_all_practices(self, include_inactive: bool = False) -> List[MockPractice]:
        try:
            query = self.db.query(MockPractice)
            if not include_inactive:
                query = query.filter(MockPractice.is_active == True)
            return query.order_by(MockPractice.name).all()
        except Exception as e:
            raise ValidationError(f"Failed to fetch practices: {str(e)}")

    def update_practice(self, practice_id: int, **kwargs) -> Optional[MockPractice]:
        try:
            practice = (
                self.db.query(MockPractice)
                .filter(MockPractice.id == practice_id)
                .first()
            )
            if not practice:
                raise ValidationError("Practice not found")
            
            if "name" in kwargs:
                existing = (
                    self.db.query(MockPractice)
                    .filter(
                        MockPractice.name == kwargs["name"],
                        MockPractice.id != practice_id,
                    )
                    .first()
                )
                if existing:
                    raise ValidationError("Practice with this name already exists")

            # Update fields
            for key, value in kwargs.items():
                setattr(practice, key, value)

            self.db.commit()
            self.db.refresh(practice)
            return practice
        except ValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update practice: {str(e)}")

    def get_practice_users(self, practice_id: int) -> List[MockUser]:
        assignments = (
            self.db.query(MockPracticeUserAssignment)
            .filter_by(practice_id=practice_id)
            .all()
        )
        return [self.db.query(MockUser).get(a.user_id) for a in assignments]

    def remove_user_from_practice(self, practice_id: int, user_id: int) -> bool:
        assignment = (
            self.db.query(MockPracticeUserAssignment)
            .filter_by(practice_id=practice_id, user_id=user_id)
            .first()
        )

        if assignment:
            self.db.delete(assignment)
            self.db.commit()
            return True
        return False

    def get_user_practice(self, user_id: int) -> Optional[MockPractice]:
        try:
            assignment = (
                self.db.query(MockPracticeUserAssignment)
                .filter(MockPracticeUserAssignment.user_id == user_id)
                .first()
            )

            if assignment:
                return self.get_practice(assignment.practice_id)
            return None
        except Exception as e:
            raise ValidationError(f"Failed to fetch user's practice: {str(e)}")
