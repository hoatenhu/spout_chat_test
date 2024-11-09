from rest_framework import serializers
from django.contrib.auth.hashers import make_password

from app.models.role import Role
from app.models.team import TeamUser, Team
from app.models.user import User
from app.models.vendor import Vendor
from app.serializers.team.team_serializer import TeamSerializer
from app.serializers.user.role_serializer import RoleSerializer
from app.serializers.vendor.vendor_serializer import VendorSerializer

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    vendor = VendorSerializer(read_only=True)
    teams = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'role', 'vendor', 'email', 'firstName', 'lastName', 
            'phoneNumber', 'dateOfBirth', 'gender', 'countryCode', 'avatar', 
            'whatsappId', 'subjectId', 'username', 'position', 'teams'
        ]

    def get_teams(self, obj):
        team_users = TeamUser.objects.filter(user=obj)
        teams = [team_user.team for team_user in team_users]
        return TeamSerializer(teams, many=True).data

class UserCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False)
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all(), required=False)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'role', 'vendor', 'email', 'firstName', 'lastName', 
            'phoneNumber', 'dateOfBirth', 'gender', 'countryCode', 'avatar', 
            'whatsappId', 'subjectId', 'username', 'position', 'password'
        ]
        
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['password'] = make_password(password)
        user = User.objects.create(**validated_data)
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['role'] = RoleSerializer(instance.role).data if instance.role else None
        representation['vendor'] = VendorSerializer(instance.vendor).data if instance.vendor else None
        return representation

class UserUpdateSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False, allow_null=True)
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all(), required=False, allow_null=True)
    teams = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), many=True, required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    firstName = serializers.CharField(required=False, allow_blank=True)
    lastName = serializers.CharField(required=False, allow_blank=True)
    phoneNumber = serializers.CharField(required=False, allow_blank=True)
    dateOfBirth = serializers.CharField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    countryCode = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.CharField(required=False, allow_null=True)
    whatsappId = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    position = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'role', 'vendor', 'email', 'firstName', 'lastName', 
            'phoneNumber', 'dateOfBirth', 'gender', 'countryCode', 'avatar', 
            'whatsappId', 'subjectId', 'username', 'position', 'teams'
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def update(self, instance, validated_data):
        teams = validated_data.pop('teams', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if teams is not None:
            TeamUser.objects.filter(user=instance).delete()
            for team in teams:
                TeamUser.objects.create(user=instance, team=team)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['role'] = RoleSerializer(instance.role).data if instance.role else None
        representation['vendor'] = VendorSerializer(instance.vendor).data if instance.vendor else None
        team_users = TeamUser.objects.filter(user=instance)
        teams = [team_user.team for team_user in team_users]
        representation['teams'] = TeamSerializer(teams, many=True).data
        return representation