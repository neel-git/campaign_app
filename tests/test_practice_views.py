import pytest
from rest_framework import status
from practices.views import PracticeViewSet
from tests.utils.request_utils import TestUser, create_test_request
from authentication.models import UserRoles
from tests.utils.mock_models import MockPractice, MockPracticeUserAssignment
from unittest.mock import patch


class TestPracticeViewSet:
    """Test suite for PracticeViewSet"""

    @pytest.fixture
    def viewset(self):
        """Creates a fresh viewset instance for each test"""
        return PracticeViewSet()

    def test_list_practices_unauthenticated(self, viewset, db_session):
        """Tests that unauthenticated users can only see active practices"""
        # Create test practices
        active_practice = MockPractice(name="Active Practice", is_active=True)
        inactive_practice = MockPractice(name="Inactive Practice", is_active=False)
        db_session.add_all([active_practice, inactive_practice])
        db_session.commit()

        # Create unauthenticated request
        request = create_test_request("/api/practice/", is_authenticated=False)

        # Test the response
        with patch("practices.views.get_db_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            response = viewset.list(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Active Practice"

    def test_list_practices_super_admin(self, viewset, db_session):
        """Tests that super admin users can see all practices"""
        # Create test practices
        practices = [
            MockPractice(name="Active Practice", is_active=True),
            MockPractice(name="Inactive Practice", is_active=False),
        ]
        db_session.add_all(practices)
        db_session.commit()

        # Create super admin user and request
        super_admin = TestUser(role=UserRoles.SUPER_ADMIN)
        request = create_test_request("/api/practice/", user=super_admin)

        with patch("practices.views.get_db_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            response = viewset.list(request)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_practice_super_admin(self, viewset, db_session):
        """Tests practice creation by super admin"""
        data = {
            "name": "New Practice",
            "description": "Test Description",
            "is_active": True,
        }
        super_admin = TestUser(role=UserRoles.SUPER_ADMIN)
        request = create_test_request(
            "/api/practice/", user=super_admin, method="post", data=data
        )

        with patch("practices.views.get_db_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            response = viewset.create(request)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Practice"

    def test_update_practice(self, viewset, db_session):
        """Tests practice update functionality"""
        # Create test practice
        practice = MockPractice(name="Original Name", is_active=True)
        db_session.add(practice)
        db_session.commit()

        data = {"name": "Updated Name", "description": "Updated Description"}
        super_admin = TestUser(role=UserRoles.SUPER_ADMIN)
        request = create_test_request(
            f"/api/practice/{practice.id}/", user=super_admin, method="put", data=data
        )

        with patch("practices.views.get_db_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            response = viewset.update(request, pk=practice.id)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Name"

    def test_delete_practice(self, viewset, db_session):
        """Tests practice deletion"""
        # Create test practice
        practice = MockPractice(name="To Delete", is_active=True)
        db_session.add(practice)
        db_session.commit()

        super_admin = TestUser(role=UserRoles.SUPER_ADMIN)
        request = create_test_request(
            f"/api/practice/{practice.id}/", user=super_admin, method="delete"
        )

        with patch("practices.views.get_db_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            response = viewset.destroy(request, pk=practice.id)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_my_practice(self, viewset, db_session):
        """Tests retrieving user's practice"""
        # Create test practice and user
        practice = MockPractice(name="User Practice", is_active=True)
        db_session.add(practice)
        db_session.commit()

        user = TestUser(id=1, role=UserRoles.PRACTICE_USER)

        # Create practice assignment
        assignment = MockPracticeUserAssignment(
            practice_id=practice.id, user_id=user.id
        )
        db_session.add(assignment)
        db_session.commit()

        request = create_test_request("/api/practice/my_practice/", user=user)

        with patch("practices.views.get_db_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            response = viewset.my_practice(request)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "User Practice"

    def test_approve_user_assignment(self, viewset, db_session):
        """Tests user assignment approval"""
        # Create test practice
        practice = MockPractice(name="Test Practice", is_active=True)
        db_session.add(practice)
        db_session.commit()

        data = {"user_id": 1, "role": UserRoles.PRACTICE_USER}
        super_admin = TestUser(role=UserRoles.SUPER_ADMIN)
        request = create_test_request(
            f"/api/practice/{practice.id}/approve_user_assignment/",
            user=super_admin,
            method="post",
            data=data,
        )

        with patch("practices.views.get_db_session") as mock_session:
            mock_session.return_value.__enter__.return_value = db_session
            response = viewset.approve_user_assignment(request, pk=practice.id)

        assert response.status_code == status.HTTP_201_CREATED
