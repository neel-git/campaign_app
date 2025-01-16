# authentication/backends.py
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User
from utils.db_session import get_db_session


class SessionAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        user_id = request.session.get("user_id")

        if not user_id:
            return None

        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user and user.is_active and user.is_session_valid():
                return (user, None)

        return None
