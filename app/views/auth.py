from django.shortcuts import get_object_or_404
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from app.models.user import User
from app.serializers.auth.auth_serializer import LoginSerializer, NewPasswordSerializer, RegisterSerializer
from app.utils.handle_response import handle_response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core import mail
from decouple import config
from app.utils.utils import token_header

@swagger_auto_schema(
    method='post',
    operation_summary="User Registration",
    operation_description="Register a new user by providing the necessary user details.",
    request_body=RegisterSerializer,  # The expected input schema
    responses={
        201: openapi.Response(description="Register successfully", schema=RegisterSerializer),
        400: "Bad Request - Invalid input or user already exists"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
        except Exception as e:
            return handle_response(message='Register Failed: ' + str(e), status_code=status.HTTP_400_BAD_REQUEST)
        
        return handle_response(data=serializer.data, message='Register successful', status_code=status.HTTP_201_CREATED)
    return handle_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="Login user and get JWT tokens",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
        },
    ),
    responses={
        200: 'Access and Refresh tokens along with user data',
        400: "Bad Request - Wrong username or password"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)
        return handle_response(data={
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, message='Login successful', status_code=status.HTTP_200_OK)
    return handle_response(message=serializer.errors['non_field_errors'][0], status_code=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="Logout user",
    operation_description="Logout the user by blacklisting the refresh token.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh'],
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
        },
    ),
    responses={
        200: "Logout successful",
        400: "Bad Request - Invalid token"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return handle_response(message='Refresh token is required', status_code=status.HTTP_400_BAD_REQUEST)    
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return handle_response(message='Logout successful', status_code=status.HTTP_200_OK)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
    
@swagger_auto_schema(
    method='post',
    operation_description="Request a password reset",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_EMAIL,
                description='Email address of the user requesting password reset',
            ),
        }
    ),
    responses={200: 'Password reset email sent', 400: 'Bad Request', 404: 'User not found'}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    try:
        email = request.data.get('email')
        if not email:
            return handle_response(message='Email must be provided', status_code=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return handle_response(message='User not found', status_code=status.HTTP_404_NOT_FOUND)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.id))
        reset_url = f"https://spout-jet.vercel.app/reset-password?uid={uid}&token={token}"

        email_message = (
            'Password Reset Request',
            f'Please click the following link to reset your password: {reset_url}',
            config('EMAIL_HOST_USER'),
            [email]
        )
        
        mail.send_mail(*email_message, fail_silently=False)
        return handle_response(message='Password reset email sent', status_code=status.HTTP_200_OK)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_description="Reset password",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'uid': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='UID of the user',
            ),
            'token': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Password reset token',
            ),
            'newPassword': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='New password',
            ),
        }
    ),
    responses={200: 'Password reset successfully', 400: 'Bad Request', 404: 'User not found'}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    try:
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('newPassword')

        if not uid or not token or not new_password:
            return handle_response(message='UID, token, and new password must be provided', status_code=status.HTTP_400_BAD_REQUEST)

        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.filter(id=user_id).first()
        if not user:
            return handle_response(message='User not found', status_code=status.HTTP_404_NOT_FOUND)

        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return handle_response(message='Password reset successfully', status_code=status.HTTP_200_OK)
        else:
            return handle_response(message='Invalid token', status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_description="Change password",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'oldPassword': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Current password',
            ),
            'newPassword': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='New password',
            ),
        }
    ),
    manual_parameters=[token_header],
    responses={200: 'Password changed successfully', 400: 'Bad Request', 401: 'Unauthorized'}
)
@api_view(['POST'])
def change_password(request):
    try:
        user = request.user
        old_password = request.data.get('oldPassword')
        new_password = request.data.get('newPassword')

        if not old_password or not new_password:
            return handle_response(message='Old password and new password must be provided', status_code=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return handle_response(message='Old password is incorrect', status_code=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return handle_response(message='Password changed successfully', status_code=status.HTTP_200_OK)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
