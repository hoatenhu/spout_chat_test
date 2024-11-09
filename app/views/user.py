from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from app.helpers.time_query import query_debugger
from app.models.role import Role
from app.models.team import TeamUser
from app.models.user import User
from app.serializers.user.user_serializer import UserCreateSerializer, UserSerializer, UserUpdateSerializer
from app.utils.handle_response import handle_response
from app.utils.permission import IsAdmin, IsAdminOrTeamAdmin
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Prefetch
from rest_framework.pagination import PageNumberPagination
from drf_yasg import openapi
from django.db.models import Q
from django.core import mail
from decouple import config
from rest_framework.permissions import AllowAny
from app.utils.utils import token_header
import boto3

class CustomPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'limit'
    max_page_size = 100

@swagger_auto_schema(
    method='get',
    operation_description="Get a list of all users with pagination",
    manual_parameters=[
        openapi.Parameter(
            'page', 
            openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            required=False, 
            description="Page number to retrieve",
            default=1 
        ),
        openapi.Parameter(
            'limit', 
            openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            required=False, 
            description="Number of users per page",
            default=10 
        ),
        openapi.Parameter(
            'search', 
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            required=False, 
            description="Search query to filter users"
        ),
        openapi.Parameter(
            'teamId', 
            openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            required=False, 
            description="Team ID to filter users"
        ),
        token_header
    ],
    responses={200: UserSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAdminOrTeamAdmin])
@query_debugger
def user_list(request):
    try:
        search_query = request.GET.get('search', '')
        team_id = request.GET.get('teamId', None)
        filters = Q()
        if search_query:
            filters |= Q(email__icontains=search_query) 
            filters |= Q(phoneNumber__icontains=search_query)  
            filters |= Q(firstName__icontains=search_query)  
            filters |= Q(lastName__icontains=search_query)  
            filters |= Q(role__roleName__icontains=search_query)
            filters |= Q(gender__icontains=search_query)
            filters |= Q(position__icontains=search_query)
        if team_id:
            filters &= Q(teamuser__team_id=team_id)
        
        filters &= Q(vendor__id=request.user.vendor.id)
        paginator = CustomPagination()
        users_with_teams = User.objects.filter(filters).distinct().order_by('id')
        paginated_users = paginator.paginate_queryset(users_with_teams, request)
        serializer = UserSerializer(paginated_users, many=True)
        data = paginator.get_paginated_response(serializer.data).data
        
        return handle_response(data=data, message='Users retrieved successfully', status_code=status.HTTP_200_OK)
    except User.DoesNotExist:
        return handle_response(message='No users found', status_code=status.HTTP_404_NOT_FOUND)
    
@swagger_auto_schema(
    method='post',
    operation_description="Create a new user",
    request_body=UserCreateSerializer,
    responses={201: UserCreateSerializer, 400: 'Bad Request'},
    manual_parameters=[token_header]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_user(request):
    try:
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data,message='Created account successfully', status_code=status.HTTP_201_CREATED)
        return handle_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a user by ID",
    responses={200: UserSerializer, 404: 'User not found'},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
        method='patch',
        operation_description="Update a user by ID",
        request_body=UserUpdateSerializer,
        responses={200: UserUpdateSerializer, 400: 'Bad Request', 404: 'User not found'},
        manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a user by ID",
    responses={204: 'No Content', 404: 'User not found'},
    manual_parameters=[token_header]
)
@api_view(['GET','PATCH', 'DELETE'])
@permission_classes([IsAdmin])
@query_debugger
def user_detail(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return handle_response(message='User not found', status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return handle_response(data=serializer.data, message='User retrieved successfully', status_code=status.HTTP_200_OK)
    
    if request.method == 'PATCH':
        serializer = UserUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data, message='User updated successfully', status_code=status.HTTP_200_OK)
        return handle_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'DELETE':
        try:
            user.delete()
            return handle_response(status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
    
@swagger_auto_schema(
    method='delete',
    operation_description="Delete multiple users",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'userIds': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.FORMAT_UUID),
                description='List of user IDs to delete',
            ),
        }
    ),
    manual_parameters=[token_header],
    responses={204: 'No Content', 400: 'Bad Request', 404: 'Users not found'}
)
@api_view(['DELETE'])
@permission_classes([IsAdmin])
@query_debugger
def delete_users(request):
    try:
        user_ids = request.data.get('userIds', [])
        if not user_ids:
            return handle_response(message='No user IDs provided', status_code=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(id__in=user_ids)
        if not users.exists():
            return handle_response(message='No users found with provided IDs', status_code=status.HTTP_404_NOT_FOUND)

        users.delete()
        return handle_response(message='Users deleted successfully', status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='put',
    operation_description="Update multiple users",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'userIds': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.FORMAT_UUID),
                description='List of user IDs to update',
            ),
                'firstName': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='First name to update for the users',
            ),
            'lastName': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Last name to update for the users',
            ),
            'phoneNumber': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Phone number to update for the users',
            ),
            'gender': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Gender to update for the users',
            ),
            'position': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Position to update for the users',
            ),
            'role': openapi.Schema(
                type=openapi.FORMAT_UUID,
                description='Role to update for the users',
            ),
            'vendor': openapi.Schema(
                type=openapi.FORMAT_UUID,
                description='Vendor to update for the users',
            ),
        }
    ),
    manual_parameters=[token_header],
    responses={200: 'Users updated successfully', 400: 'Bad Request', 404: 'Users not found'}
)
@api_view(['PUT'])
@permission_classes([IsAdmin])
@query_debugger
def update_users(request):
    try:
        user_ids = request.data.get('userIds', [])
        update_data = {key: value for key, value in request.data.items() if key != 'userIds'}
                
        if not user_ids or not update_data:
            return handle_response(message='User IDs and update data must be provided', status_code=status.HTTP_400_BAD_REQUEST)
        
        # Check if email already exists
        if 'email' in update_data:
            existing_email = User.objects.filter(email=update_data['email']).exclude(id__in=user_ids).exists()
            if existing_email:
                return handle_response(message='Email already exists', status_code=status.HTTP_400_BAD_REQUEST)
                
        users = User.objects.filter(id__in=user_ids)
        if not users.exists():
            return handle_response(message='No users found with provided IDs', status_code=status.HTTP_404_NOT_FOUND)
                
        users.update(**update_data)
        updated_users = User.objects.filter(id__in=user_ids)
        serializer = UserSerializer(updated_users, many=True)
        return handle_response(data=serializer.data, message='Users updated successfully', status_code=status.HTTP_200_OK)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    operation_description="Get a list of users by team ID with pagination",
    manual_parameters=[
        openapi.Parameter(
            'page', 
            openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            required=False, 
            description="Page number to retrieve",
            default=1 
        ),
        openapi.Parameter(
            'limit', 
            openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            required=False, 
            description="Number of users per page",
            default=10 
        ),
        token_header
    ],
    responses={200: UserSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAdmin])
@query_debugger
def users_by_team(request, pk):
    try:
        paginator = CustomPagination()
        users_in_team = User.objects.filter(teamuser__team_id=pk).distinct().order_by('id')
        paginated_users = paginator.paginate_queryset(users_in_team, request)
        serializer = UserSerializer(paginated_users, many=True)
        data = paginator.get_paginated_response(serializer.data).data
            
        return handle_response(data=data, message='Users retrieved successfully', status_code=status.HTTP_200_OK)
    except User.DoesNotExist:
            return handle_response(message='No users found', status_code=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='get',
    operation_description="Get the profile of the authenticated user",
    responses={200: UserSerializer, 401: 'Unauthorized'},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='patch',
    operation_description="Update the profile of the authenticated user",
    request_body=UserUpdateSerializer,
    responses={200: UserUpdateSerializer, 400: 'Bad Request'},
    manual_parameters=[token_header]
)
@api_view(['GET', 'PATCH'])
@query_debugger
def my_profile(request):
    if request.method == 'GET':
        try:
            user = request.user
            serializer = UserSerializer(user)
            return handle_response(data=serializer.data, message='Profile retrieved successfully', status_code=status.HTTP_200_OK)
        except User.DoesNotExist:   
            return handle_response(message='User not found', status_code=status.HTTP_404_NOT_FOUND)
    elif request.method == 'PATCH':
        try:
            user = request.user
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return handle_response(data=serializer.data, message='Profile updated successfully', status_code=status.HTTP_200_OK)
            return handle_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return handle_response(message='User not found', status_code=status.HTTP_404_NOT_FOUND)
        
@swagger_auto_schema(
    method='post',
    operation_description="Invite multiple users via email",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'emails': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                description='List of email addresses to invite',
            ),
            'role': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Role to assign to the invited users',
            ),
        }
    ),
    manual_parameters=[token_header],
    responses={200: 'Invitations sent successfully', 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([IsAdmin])
def invite_users(request):
    try:
        emails = request.data.get('emails', [])
        role = request.data.get('role', '')

        if not emails or not role:
            return handle_response(message='Emails, role, must be provided', status_code=status.HTTP_400_BAD_REQUEST)

        email_messages = []
        for email in emails:
            invite_url = f"https://spout-jet.vercel.app/create-account?role={role}&vendor={request.user.vendor.id}&email={email}"
            email_message = (
            'You are invited to join our platform',
            f'Please click the following link to create your account: {invite_url}',
            config('EMAIL_HOST_USER'),
            [email]
            )
            email_messages.append(email_message)
        
        connection = mail.get_connection()
        connection.open()
        mail.send_mass_mail(email_messages, fail_silently=False, connection=connection)
        connection.close()
        return handle_response(message='Invitations sent successfully', status_code=status.HTTP_200_OK)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    operation_description="generate presigned url for uploading image",
    responses={200: 'Presigned URL generated successfully', 500: 'Internal Server Error'},
    manual_parameters=[
        openapi.Parameter(
            'object_name', 
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            required=True, 
            description="Name of the object to upload",
        ),
        token_header
    ]
)        
@api_view(['GET'])
def generate_presigned_url(request):
    s3 = boto3.client(
        's3',
        aws_access_key_id=config('AWS_ACCESS_KEY'),
        aws_secret_access_key=config('AWS_SECRET_KEY'),
        region_name=config('AWS_REGION'),
        config=boto3.session.Config(signature_version='v4')
    )

    bucket_name = config('AWS_S3_BUCKET')
    object_name = request.query_params.get('object_name')
    expiration = 3600

    try:
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
        return handle_response(data={'url': presigned_url}, message='Presigned URL generated successfully', status_code=status.HTTP_200_OK)

    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

