from rest_framework import serializers
from .models import User, UserRoles, UserRegistrationRequest, RoleChangeRequest
from utils.db_session import get_db_session
from django.utils import timezone
from practices.models import Practice
from practices.serializers import PracticeSerializer


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=255, required=False)
    desired_practice_id = serializers.IntegerField(required=True)
    requested_role = serializers.CharField(required=True)

    def validate_requested_role(self, value):
        """Convert frontend role format to backend format"""
        role_mapping = {"ADMIN": "Admin", "PRACTICE USER": "Practice User"} #Mapping

        # Convert role format if needed
        converted_role = role_mapping.get(value, value)

        # Validate the converted role
        valid_roles = ["Admin", "Practice User"]
        if converted_role not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )

        return converted_role

    def validate_username(self, value):
        with get_db_session() as session:
            user = session.query(User).filter(User.username == value).first()
            if user:
                raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        with get_db_session() as session:
            user = session.query(User).filter(User.email == value).first()
            if user:
                raise serializers.ValidationError("Email already exists")
        return value

    def validate_desired_practice_id(self, value):
        if value:
            with get_db_session() as session:
                practice = session.query(Practice).filter(Practice.id == value).first()
                if not practice:
                    raise serializers.ValidationError("Practice not found")
        return value

    def validate_role(self, value):
        if value not in [UserRoles.ADMIN, UserRoles.PRACTICE_USER]:
            raise serializers.ValidationError("Invalid role")
        return value

    def create(self, validated_data):
        try:
            user = User(
                username=validated_data["username"],
                email=validated_data["email"],
                full_name=validated_data.get("full_name"),
                role=None,  # No default role
                is_active=True,
                created_at=timezone.now(),
            )
            user.set_password(validated_data["password"])
            return user
        except Exception as e:
            raise


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField()
    full_name = serializers.CharField(allow_null=True)
    email = serializers.EmailField()
    role = serializers.CharField()
    is_active = serializers.BooleanField()
    last_login = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long"
            )
        return value


class UserRegistrationRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    desired_practice_id = serializers.IntegerField()
    requested_role = serializers.ChoiceField(choices=["admin", "practice_user"])
    status = serializers.CharField(read_only=True)
    rejection_reason = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    user = UserSerializer(read_only=True)
    practice = PracticeSerializer(read_only=True)


class RoleChangeRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    practice_id = serializers.IntegerField(read_only=True)
    current_role = serializers.CharField(read_only=True)
    requested_role = serializers.ChoiceField(
        choices=[(UserRoles.ADMIN, "Admin"), (UserRoles.PRACTICE_USER, "Practice User")]
    )
    status = serializers.CharField(read_only=True)
    requested_at = serializers.DateTimeField(read_only=True)
    rejection_reason = serializers.CharField(read_only=True, allow_null=True)
    user = UserSerializer(read_only=True)
    practice = PracticeSerializer(read_only=True)
