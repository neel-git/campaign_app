# authentication/services.py
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import User, UserRoles, UserRegistrationRequest, RoleChangeRequest
from practices.models import PracticeUserAssignment, Practice
from rest_framework.exceptions import ValidationError
from typing import Union


class UserRegistrationRequestService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_request(
        self, user_id: int, practice_id: int, requested_role: str
    ) -> UserRegistrationRequest:
        try:
            # Verify practice exists
            practice = (
                self.db.query(Practice)
                .filter_by(id=practice_id, is_active=True)
                .first()
            )
            if not practice:
                raise ValidationError("Practice not found or inactive")

            request = UserRegistrationRequest(
                user_id=user_id,
                desired_practice_id=practice_id,
                requested_role=requested_role,
                status="PENDING",
            )
            self.db.add(request)
            self.db.commit()
            self.db.refresh(request)
            return request
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create request: {str(e)}")

    def get_admin_pending_requests(self, admin_practice_id: int) -> dict:
        """Get all pending requests for a specific practice admin"""
        try:
            # Get practice users registration requests
            registration_requests = (
                self.db.query(UserRegistrationRequest)
                .filter(
                    UserRegistrationRequest.desired_practice_id == admin_practice_id,
                    UserRegistrationRequest.status == "PENDING",
                    UserRegistrationRequest.requested_role == UserRoles.PRACTICE_USER,
                )
                .all()
            )

            # Get role change requests within the practice
            role_changes = (
                self.db.query(RoleChangeRequest)
                .filter(
                    RoleChangeRequest.practice_id == admin_practice_id,
                    RoleChangeRequest.status == "PENDING",
                    RoleChangeRequest.requested_role == UserRoles.PRACTICE_USER,
                )
                .all()
            )

            return {
                "registration_requests": registration_requests,
                "role_change_requests": role_changes,
            }
        except Exception as e:
            raise ValidationError(f"Failed to fetch admin requests: {str(e)}")

    def get_super_admin_pending_requests(self) -> dict:
        """Get all pending admin role requests for super admin"""
        try:
            registration_requests = (
                self.db.query(UserRegistrationRequest)
                .filter(
                    UserRegistrationRequest.status == "PENDING",
                    UserRegistrationRequest.requested_role == UserRoles.ADMIN,
                )
                .all()
            )

            role_changes = (
                self.db.query(RoleChangeRequest)
                .filter(
                    RoleChangeRequest.status == "PENDING",
                    RoleChangeRequest.requested_role == UserRoles.ADMIN,
                )
                .all()
            )

            return {
                "registration_requests": registration_requests,
                "role_change_requests": role_changes,
            }
        except Exception as e:
            raise ValidationError(f"Failed to fetch super admin requests: {str(e)}")

    def create_role_change_request(
        self, user_id: int, practice_id: int, requested_role: str
    ) -> RoleChangeRequest:
        try:
            user = self.db.query(User).get(user_id)
            if not user:
                raise ValidationError("User not found")

            # Check existing pending request
            existing_request = (
                self.db.query(RoleChangeRequest)
                .filter(
                    RoleChangeRequest.user_id == user_id,
                    RoleChangeRequest.status == "PENDING",
                )
                .first()
            )
            if existing_request:
                raise ValidationError("User already has a pending role change request")

            # Verify practice assignment
            practice_assignment = (
                self.db.query(PracticeUserAssignment)
                .filter(
                    PracticeUserAssignment.user_id == user_id,
                    PracticeUserAssignment.practice_id == practice_id,
                )
                .first()
            )
            if not practice_assignment:
                raise ValidationError("User is not assigned to this practice")

            request = RoleChangeRequest(
                user_id=user_id,
                practice_id=practice_id,
                current_role=user.role,
                requested_role=requested_role,
                status="PENDING",
            )
            self.db.add(request)
            self.db.commit()
            self.db.refresh(request)
            return request
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create role change request: {str(e)}")

    def assign_user_to_practice(
        self, user_id: int, practice_id: int, role: str
    ) -> PracticeUserAssignment:
        try:
            # Check if user exists
            user = self.db.query(User).get(user_id)
            if not user:
                raise ValidationError("User not found")

            # Check if practice exists and is active
            practice = (
                self.db.query(Practice)
                .filter_by(id=practice_id, is_active=True)
                .first()
            )
            if not practice:
                raise ValidationError("Practice not found or inactive")

            # Check if assignment already exists
            existing_assignment = (
                self.db.query(PracticeUserAssignment)
                .filter_by(user_id=user_id, practice_id=practice_id)
                .first()
            )
            if existing_assignment:
                raise ValidationError("User is already assigned to this practice")

            # Create assignment
            assignment = PracticeUserAssignment(
                user_id=user_id, practice_id=practice_id
            )

            # Update user role
            user.role = role
            user.is_approved = True

            self.db.add(assignment)
            self.db.commit()
            self.db.refresh(assignment)
            return assignment
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to assign user to practice: {str(e)}")

    def handle_request_approval(
        self, request_id: int, request_type: str, reviewer_id: int
    ) -> Union[UserRegistrationRequest, RoleChangeRequest]:
        try:
            if request_type == "registration":
                request = self.db.query(UserRegistrationRequest).get(request_id)
                if not request:
                    raise ValidationError("Registration request not found")

                # Create practice assignment
                self.assign_user_to_practice(
                    user_id=request.user_id,
                    practice_id=request.desired_practice_id,
                    role=request.requested_role,
                )
            else:
                request = self.db.query(RoleChangeRequest).get(request_id)
                if not request:
                    raise ValidationError("Role change request not found")

                # Update user role
                user = self.db.query(User).get(request.user_id)
                if not user:
                    raise ValidationError("User not found")
                user.role = request.requested_role

            # Update request status
            request.status = "APPROVED"
            request.reviewed_by = reviewer_id

            self.db.commit()
            self.db.refresh(request)
            return request
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to approve request: {str(e)}")

    def handle_request_rejection(
        self, request_id: int, request_type: str, reviewer_id: int, reason: str
    ) -> Union[UserRegistrationRequest, RoleChangeRequest]:
        try:
            if request_type == "registration":
                request = self.db.query(UserRegistrationRequest).get(request_id)
            else:
                request = self.db.query(RoleChangeRequest).get(request_id)

            if not request:
                raise ValidationError(f"{request_type} request not found")

            request.status = "REJECTED"
            request.reviewed_by = reviewer_id
            request.rejection_reason = reason

            self.db.commit()
            self.db.refresh(request)
            return request
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to reject request: {str(e)}")
