from rest_framework import serializers
from .models import Practice, PracticeUserAssignment
from utils.db_session import get_db_session
from authentication.models import User

class PracticeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

class PracticeUserAssignmentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    practice_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    assigned_at = serializers.DateTimeField(read_only=True)

class PracticeDetailSerializer(PracticeSerializer):
    users = serializers.SerializerMethodField()

    def get_users(self, obj):
        from authentication.serializers import UserSerializer
        with get_db_session() as session:
            assignments = session.query(PracticeUserAssignment).filter_by(practice_id=obj.id).all()
            users = [session.query(User).get(a.user_id) for a in assignments]
            return UserSerializer(users, many=True).data
