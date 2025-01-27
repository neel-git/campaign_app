# authentication/middleware.py
from django.http import JsonResponse
from datetime import datetime
from utils.db_session import get_db_session
from .models import User


class CustomAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check session validity
        if "user_id" in request.session:
            with get_db_session() as session:
                user = (
                    session.query(User)
                    .filter(User.id == request.session["user_id"])
                    .first()
                )

                if user and user.is_session_valid():
                    request.user = user
                else:
                    # Clear invalid session
                    request.session.flush()
                    return JsonResponse({"error": "Session expired"}, status=401)

        response = self.get_response(request)
        return response
