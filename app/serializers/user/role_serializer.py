from rest_framework import serializers
from app.models.role import Role


class RoleSerializer(serializers.ModelSerializer):
    roleName = serializers.CharField(max_length=50)
    class Meta:
        model = Role
        fields = ['id','roleName']