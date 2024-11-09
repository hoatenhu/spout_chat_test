import re
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password

from app.models.role import Role
from app.models.user import User
from app.models.vendor import Vendor

class RegisterSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    username = serializers.CharField(max_length=50,allow_null=True)
    password = serializers.CharField(write_only=True, required=True)
    phoneNumber = serializers.CharField(max_length=10, allow_null=True, required=False)
    dateOfBirth = serializers.CharField(max_length=50,allow_null=True, required=False)
    firstName = serializers.CharField(max_length=150, allow_null=True, required=False)
    lastName = serializers.CharField(max_length=150, allow_null=True, required=False)
    gender = serializers.CharField(max_length=50, allow_null=True, required=False)
    countryCode = serializers.CharField(max_length=8, allow_null=True, required=False)
    position = serializers.CharField(max_length=50, allow_null=True, required=False)
    companyName = serializers.CharField(max_length=150,required=False)
    website = serializers.CharField(max_length=150, required=False)    
    industry = serializers.CharField(max_length=150,required=False)   
    size = serializers.CharField(max_length=150, required=False) 
        
    class Meta:
        model = User
        fields = [
            'id', 'email', 'firstName', 'lastName',
            'phoneNumber', 'dateOfBirth', 'gender', 'countryCode',
            'password', 'whatsappId', 'subjectId',
            'username', 'position',
            'companyName', 'website', 'industry', 'size'
        ]

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return data

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        try:
            default_role = Role.objects.get(roleName='admin')
            validated_data['role'] = default_role

            company_name = validated_data.pop('companyName', None)
            website = validated_data.pop('website', None)
            industry = validated_data.pop('industry', None)
            size = validated_data.pop('size', None)

            vendor = None
            if company_name and industry and size:
                vendor_data = {
                    'name': company_name,
                    'website': website,
                    'industry': industry,
                    'size': size
                }
                vendor = Vendor.objects.create(**vendor_data)
        
            validated_data['vendor'] = vendor
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Default role 'admin' does not exist.")

        return super(RegisterSerializer, self).create(validated_data)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid username.")

        # Validate the password
        if not check_password(password, user.password):
            raise serializers.ValidationError("Invalid password.")
        
        return user
    
class ChangePasswordSerializer(serializers.Serializer):
    oldPassword = serializers.CharField(max_length=256)
    newPassword = serializers.CharField(max_length=256)
    
class RespondToNewPasswordChallengeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=2048)
    email = serializers.EmailField()

class ResendConfirmationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class NewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128)