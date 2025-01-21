# authentication/services.py
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import User, UserRoleType, UserRegistrationRequest
from practices.models import PracticeUserAssignment
from rest_framework.exceptions import ValidationError

class UserRegistrationRequestService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_request(self, user_id: int, practice_id: int, requested_role: str) -> UserRegistrationRequest:
        try:
            with self.db.begin():
                request = UserRegistrationRequest(
                    user_id=user_id,
                    desired_practice_id=practice_id,
                    requested_role=UserRoleType[requested_role]
                )
                self.db.add(request)
                self.db.commit()
                self.db.refresh(request)
                return request
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create request: {str(e)}")

    def get_pending_requests(self, reviewer_role: UserRoleType) -> List[UserRegistrationRequest]:
        try:
            with self.db.begin():
                query = self.db.query(UserRegistrationRequest)\
                    .filter(UserRegistrationRequest.status == "PENDING")
                
                # Filter based on reviewer role
                if reviewer_role == UserRoleType.admin:
                    query = query.filter(
                        UserRegistrationRequest.requested_role == UserRoleType.practice_user
                    )
                elif reviewer_role == UserRoleType.super_admin:
                    query = query.filter(
                        UserRegistrationRequest.requested_role == UserRoleType.admin
                    )
                    
                return query.all()
        except Exception as e:
            raise ValidationError(f"Failed to fetch pending requests: {str(e)}")

    def approve_request(self, request_id: int, reviewer_id: int) -> UserRegistrationRequest:
        try:
            with self.db.begin():
                request = self.db.query(UserRegistrationRequest)\
                    .filter(UserRegistrationRequest.id == request_id)\
                    .first()
                
                if not request:
                    raise ValidationError("Request not found")

                # Update user role and approval status
                user = self.db.query(User).get(request.user_id)
                if not user:
                    raise ValidationError("User not found")

                user.role = request.requested_role
                user.is_approved = True

                # Create practice assignment
                practice_assignment = PracticeUserAssignment(
                    practice_id=request.desired_practice_id,
                    user_id=request.user_id
                )
                self.db.add(practice_assignment)

                # Update request status
                request.status = "APPROVED"
                request.reviewed_by = reviewer_id

                self.db.commit()
                self.db.refresh(request)
                return request
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to approve request: {str(e)}")

    def reject_request(
        self, request_id: int, reviewer_id: int, reason: str
    ) -> UserRegistrationRequest:
        try:
            with self.db.begin():
                request = self.db.query(UserRegistrationRequest)\
                    .filter(UserRegistrationRequest.id == request_id)\
                    .first()
                
                if not request:
                    raise ValidationError("Request not found")

                request.status = "REJECTED"
                request.reviewed_by = reviewer_id
                request.rejection_reason = reason

                self.db.commit()
                self.db.refresh(request)
                return request
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to reject request: {str(e)}")