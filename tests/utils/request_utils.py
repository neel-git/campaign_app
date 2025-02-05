from rest_framework.test import APIRequestFactory, force_authenticate
from authentication.models import UserRoles


class TestUser:
    """A test user class that mimics the behavior of our real User model"""

    def __init__(
        self,
        id=1,
        username="testuser",
        role=UserRoles.PRACTICE_USER,
        is_authenticated=True,
    ):
        self.id = id
        self.username = username
        self.role = role
        self.is_authenticated = is_authenticated
        self.is_active = True


def create_test_request(url, user=None, method="get", data=None):
    """
    Creates a test request with proper authentication and data.

    Args:
        url: The URL for the request
        user: Optional TestUser instance for authentication
        method: HTTP method (get, post, put, patch, delete)
        data: Optional data for the request body
    """
    factory = APIRequestFactory()

    # Map HTTP methods to factory methods
    method_map = {
        "get": factory.get,
        "post": factory.post,
        "put": factory.put,
        "patch": factory.patch,
        "delete": factory.delete,
    }

    # Get the appropriate factory method
    request_method = method_map.get(method.lower(), factory.get)

    # Create the request with the proper format
    if data and method.lower() in ["post", "put", "patch"]:
        request = request_method(url, data, format="json")
    else:
        request = request_method(url)

    # Set up authentication if a user is provided
    if user:
        force_authenticate(request, user)

    # Ensure the request has all needed attributes
    request.user = user if user else TestUser(is_authenticated=False)
    request.data = data or {}

    return request
