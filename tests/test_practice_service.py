import pytest
from rest_framework.exceptions import ValidationError
from tests.utils.mock_models import (
    TestBase,
    MockPractice,
    MockUser,
    MockPracticeUserAssignment,
)
from authentication.models import UserRoles


class TestPracticeService:
    def test_create_practice(self, practice_service, db_session):
        practice = practice_service.create_practice(
            name="New Practice", description="Test Description"
        )

        assert practice.id is not None
        assert practice.name == "New Practice"
        assert practice.description == "Test Description"
        assert practice.is_active is True

        # Verify in database
        saved_practice = db_session.query(MockPractice).get(practice.id)
        assert saved_practice is not None
        assert saved_practice.name == practice.name

    def test_create_duplicate_practice(self, practice_service, sample_practice):
        with pytest.raises(ValidationError) as exc:
            practice_service.create_practice(name=sample_practice.name)
        assert "already exists" in str(exc.value)

    def test_get_all_practices(self, practice_service, db_session):
        practices = [
            MockPractice(name="Active 1", is_active=True),
            MockPractice(name="Active 2", is_active=True),
            MockPractice(name="Inactive", is_active=False),
        ]
        for p in practices:
            db_session.add(p)
        db_session.commit()

        active_practices = practice_service.get_all_practices(include_inactive=False)
        assert len(active_practices) == 2
        assert all(p.is_active for p in active_practices)


        all_practices = practice_service.get_all_practices(include_inactive=True)
        assert len(all_practices) == 3

    def test_update_practice(self, practice_service, sample_practice):
        updated = practice_service.update_practice(
            sample_practice.id,
            name="Updated Name",
            description="Updated Description",
            is_active=False,
        )

        assert updated.name == "Updated Name"
        assert updated.description == "Updated Description"
        assert updated.is_active is False

    def test_get_practice_users(
        self,
        practice_service,
        db_session,
        sample_practice,
        sample_user,
        sample_assignment,
    ):
        users = practice_service.get_practice_users(sample_practice.id)

        assert len(users) == 1
        assert users[0].id == sample_user.id
        assert users[0].username == sample_user.username

    def test_remove_user_from_practice(
        self,
        practice_service,
        db_session,
        sample_practice,
        sample_user,
        sample_assignment,
    ):
        result = practice_service.remove_user_from_practice(
            practice_id=sample_practice.id, user_id=sample_user.id
        )

        assert result is True

        assignment = (
            db_session.query(MockPracticeUserAssignment)
            .filter_by(practice_id=sample_practice.id, user_id=sample_user.id)
            .first()
        )
        assert assignment is None

    def test_get_user_practice(
        self, practice_service, sample_practice, sample_user, sample_assignment
    ):
        practice = practice_service.get_user_practice(sample_user.id)

        assert practice is not None
        assert practice.id == sample_practice.id
        assert practice.name == sample_practice.name
