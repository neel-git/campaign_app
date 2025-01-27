from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    campaign_id = serializers.IntegerField(read_only=True)
    campaign_name = serializers.SerializerMethodField()
    content = serializers.CharField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_campaign_name(self, obj):
        return obj.campaign.name if obj.campaign else None
