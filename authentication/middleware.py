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


# from django.http import JsonResponse
# from utils.db_session import get_db_session
# from .models import User


# class CustomAuthMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         request.user = None
#         if "user_id" in request.session:
#             with get_db_session() as session:
#                 user = (
#                     session.query(User)
#                     .filter(User.id == request.session["user_id"])
#                     .first()
#                 )

#                 if user and user.is_session_valid():
#                     # Create a dictionary of user attributes
#                     request.user = {
#                         "id": user.id,
#                         "username": user.username,
#                         "email": user.email,
#                         "role": user.role.value,
#                         "is_active": user.is_active,
#                         "session_expires_at": user.session_expires_at,
#                     }
#                 else:
#                     request.session.flush()
#                     return JsonResponse({"error": "Session expired"}, status=401)

#         response = self.get_response(request)
#         return response
