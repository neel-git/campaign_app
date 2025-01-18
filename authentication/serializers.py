from rest_framework import serializers
from .models import User, UserRoleType
from utils.db_session import get_db_session
from django.utils import timezone
from practices.models import Practice


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=255, required=False)
    desired_practice_id = serializers.IntegerField(required=False, allow_null=True)

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
        try:
            return UserRoleType(value)
        except ValueError:
            raise serializers.ValidationError("Invalid role")

    def create(self, validated_data):
        try:
            user = User(
                username=validated_data["username"],
                email=validated_data["email"],
                full_name=validated_data.get("full_name"),
                role=UserRoleType.practice_user,  # Default role will be Practice_user only
                desired_practice_id=validated_data.get("desired_practice_id"),
                is_active=True,
                created_at=timezone.now(),
            )
            user.set_password(validated_data["password"])
            return user
        except Exception as e:
            print(f"Error in create method: {str(e)}")  # logging
            raise


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField()
    full_name = serializers.CharField(allow_null = True)
    email = serializers.EmailField()
    role = serializers.CharField()
    desired_practice_id = serializers.IntegerField(allow_null=True)
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
