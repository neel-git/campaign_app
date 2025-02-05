import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from authentication.models import UserRoles
from practices.models import Practice, PracticeUserAssignment


@pytest.fixture
def api_client():
    """Fixture for API client"""
    return APIClient()


@pytest.fixture
def super_admin_user(db_session):
    """Fixture to create a Super Admin user"""
    from authentication.models import User

    user = User(
        username="superadmin",
        email="superadmin@example.com",
        role=UserRoles.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Fixture to create an Admin user"""
    from authentication.models import User

    user = User(
        username="admin",
        email="admin@example.com",
        role=UserRoles.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def practice_user(db_session):
    """Fixture to create a Practice User"""
    from authentication.models import User

    user = User(
        username="practiceuser",
        email="practiceuser@example.com",
        role=UserRoles.PRACTICE_USER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def practice(db_session):
    """Fixture to create a practice"""
    practice = Practice(
        name="Test Practice", description="Test Description", is_active=True
    )
    db_session.add(practice)
    db_session.commit()
    db_session.refresh(practice)
    return practice


@pytest.fixture
def practice_assignment(db_session, practice, practice_user):
    """Fixture to create a Practice User Assignment"""
    assignment = PracticeUserAssignment(
        practice_id=practice.id, user_id=practice_user.id
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


@pytest.mark.django_db
def test_list_practices(api_client, practice, super_admin_user):
    """Test listing practices as Super Admin"""
    api_client.force_authenticate(user=super_admin_user)

    response = api_client.get(reverse("practice-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1
    assert response.data[0]["name"] == practice.name


@pytest.mark.django_db
def test_create_practice_super_admin(api_client, super_admin_user):
    """Test Super Admin can create a practice"""
    api_client.force_authenticate(user=super_admin_user)

    data = {"name": "New Practice", "description": "New Description"}
    response = api_client.post(reverse("practice-list"), data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "New Practice"


@pytest.mark.django_db
def test_create_practice_admin_forbidden(api_client, admin_user):
    """Test Admin cannot create a practice"""
    api_client.force_authenticate(user=admin_user)

    data = {"name": "Admin Created Practice", "description": "Should Fail"}
    response = api_client.post(reverse("practice-list"), data)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_retrieve_practice(api_client, practice):
    """Test retrieving a specific practice"""
    response = api_client.get(reverse("practice-detail", args=[practice.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == practice.name


@pytest.mark.django_db
def test_update_practice_super_admin(api_client, super_admin_user, practice):
    """Test Super Admin can update practice details"""
    api_client.force_authenticate(user=super_admin_user)

    updated_data = {"name": "Updated Practice", "description": "Updated Description"}
    response = api_client.put(
        reverse("practice-detail", args=[practice.id]), updated_data
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Updated Practice"


@pytest.mark.django_db
def test_update_practice_admin_forbidden(api_client, admin_user, practice):
    """Test Admin cannot update a practice"""
    api_client.force_authenticate(user=admin_user)

    updated_data = {"name": "Admin Updated Practice"}
    response = api_client.put(
        reverse("practice-detail", args=[practice.id]), updated_data
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_delete_practice_super_admin(api_client, super_admin_user, practice):
    """Test Super Admin can delete a practice"""
    api_client.force_authenticate(user=super_admin_user)

    response = api_client.delete(reverse("practice-detail", args=[practice.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_delete_practice_admin_forbidden(api_client, admin_user, practice):
    """Test Admin cannot delete a practice"""
    api_client.force_authenticate(user=admin_user)

    response = api_client.delete(reverse("practice-detail", args=[practice.id]))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_approve_user_assignment_super_admin(
    api_client, super_admin_user, practice, practice_user
):
    """Test Super Admin can approve a user's practice assignment"""
    api_client.force_authenticate(user=super_admin_user)

    data = {"user_id": practice_user.id, "role": UserRoles.PRACTICE_USER}
    response = api_client.post(
        reverse("practice-approve-user-assignment", args=[practice.id]), data
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_approve_user_assignment_admin_forbidden(
    api_client, admin_user, practice, practice_user
):
    """Test Admin cannot approve another Admin"""
    api_client.force_authenticate(user=admin_user)

    data = {"user_id": practice_user.id, "role": UserRoles.ADMIN}
    response = api_client.post(
        reverse("practice-approve-user-assignment", args=[practice.id]), data
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_my_practice(api_client, practice_user, practice_assignment):
    """Test getting user's assigned practice"""
    api_client.force_authenticate(user=practice_user)

    response = api_client.get(reverse("practice-my-practice"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == practice_assignment.practice.name
