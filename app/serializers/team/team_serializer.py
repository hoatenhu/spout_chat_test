from app.models.team import Team, TeamUser
from app.models.user import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from app.models.vendor import Vendor

class TeamUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeamUser
        fields = ['id', 'user', 'team']

class TeamSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    vendor = serializers.UUIDField()
    name = serializers.CharField(max_length=150)
    userIds = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, write_only=True, required=False)
    user_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'vendor', 'user_count', 'userIds']

    def create(self, validated_data):
        userIds = validated_data.pop('userIds', [])
        vendor_id = validated_data.pop('vendor')  

        try:
            vendor = Vendor.objects.get(id=vendor_id) 
        except Vendor.DoesNotExist:
            raise ValidationError("Vendor does not exist.")

        team = Team.objects.create(vendor=vendor, **validated_data)
        existing_users = []
        for user in userIds:
            if TeamUser.objects.filter(user=user, team=team).exists():
                existing_users.append(user.id)

        if existing_users:
            raise ValidationError(f"Users with IDs {existing_users} already exist in this team.")

        # Create TeamUser instances
        for user in userIds:
            TeamUser.objects.create(user=user, team=team)

        return team