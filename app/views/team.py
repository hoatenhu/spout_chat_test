from django.shortcuts import get_object_or_404
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from app.helpers.time_query import query_debugger
from app.models.team import Team, TeamUser
from app.models.user import User
from app.serializers.team.team_serializer import TeamSerializer
from app.utils.handle_response import handle_response
from app.utils.permission import IsAdmin
from drf_yasg import openapi
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count
from app.utils.utils import token_header

class CustomPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'limit'
    max_page_size = 100

@swagger_auto_schema(
    method='get',
    operation_description="Get a list of teams with pagination",
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
            description="Number of team per page",
            default=10 
        ),
        token_header
    ],
    responses={200: 'Teams retrieved successfully'}
)
@swagger_auto_schema(
    method='post',
    operation_description='Create a new team',
    request_body=TeamSerializer,
    responses={201: TeamSerializer, 400: 'Validation error'},
    manual_parameters=[token_header]
)
@api_view(['GET','POST'])
@permission_classes([IsAdmin])
@query_debugger
def list_teams(request):
    if request.method == 'GET':
        try:
            paginator = CustomPagination()
            search_query = request.GET.get('search', '')
            filters = Q()
            if search_query:
                filters |= Q(name__icontains=search_query)
        
            teams = Team.objects.filter(vendor__id=request.user.vendor.id).filter(filters).annotate(
                user_count=Count('teamuser')).order_by('id')

            paginated_teams = paginator.paginate_queryset(teams, request)
            serializer = TeamSerializer(paginated_teams, many=True)
            for team, team_data in zip(paginated_teams, serializer.data):
                team_data['user_count'] = team.user_count
            paginated_teams = paginator.paginate_queryset(teams, request)
            serializer = TeamSerializer(paginated_teams, many=True)
            data = paginator.get_paginated_response(serializer.data).data
            return handle_response(data=data, message='Teams retrieved successfully', status_code=status.HTTP_200_OK)
        except Exception as e:
            return handle_response(message=str(e), status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        try:
            request.data['vendor'] = request.user.vendor.id
            serializer = TeamSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return handle_response(data=serializer.data, message='Team created successfully', status_code=status.HTTP_201_CREATED)
            return handle_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    operation_description='Retrieve a specific team',
    responses={200: TeamSerializer},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='patch',
    operation_description='Update a specific team',
    request_body=TeamSerializer,
    responses={200: TeamSerializer, 400: 'Validation error'},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='delete',
    operation_description='Delete a specific team',
    responses={204: 'No content'},
    manual_parameters=[token_header]
)
@api_view(['GET','PATCH','DELETE'])
@permission_classes([IsAdmin])
def team_details(request, id):
    try:
        team = Team.objects.get(id=id)
        if not team:
             return handle_response(message='Team not found', status_code=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = TeamSerializer(team)
            return handle_response(data=serializer.data, message='Team retrieved successfully', status_code=status.HTTP_200_OK)
        
        if request.method == 'PATCH':
            serializer = TeamSerializer(team, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return handle_response(data=serializer.data, message='Team updated successfully', status_code=status.HTTP_200_OK)
            return handle_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            team.delete()
            return handle_response(message='Team deleted successfully', status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
    
@swagger_auto_schema(
    method='delete',
    operation_description='Delete multiple teams',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'teamIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
        },
        required=['teamIds']
    ),
    responses={204: 'Teams deleted successfully', 400: 'Error occurred'}
)
@api_view(['DELETE'])
@permission_classes([IsAdmin])
def delete_teams(request):
    try:
        teamIds = request.data.get('teamIds', [])
        teams = Team.objects.filter(id__in=teamIds)

        if not teams.exists():
            return handle_response(message='No teams found to delete', status_code=status.HTTP_404_NOT_FOUND)

        teams.delete()
        return handle_response(message='Teams deleted successfully', status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_description='Add users to multiple teams',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'userIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.FORMAT_UUID)),
            'teamIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.FORMAT_UUID)),
        },
        required=['userIds', 'teamIds']
    ),
    manual_parameters=[token_header],
    responses={200: 'Users added successfully', 400: 'Some users already exist in some teams'}
)
@api_view(['POST'])
@permission_classes([IsAdmin])
def add_users_to_teams(request):
    try:
        userIds = request.data.get('userIds', [])
        teamIds = request.data.get('teamIds', [])
        existing_users = {}

        teams = Team.objects.filter(id__in=teamIds)
        users = User.objects.filter(id__in=userIds)
        team_user_pairs = TeamUser.objects.filter(team__in=teams, user__in=users)

        existing_users = {
            team_user.team.id: [] for team_user in team_user_pairs
        }

        for team_user in team_user_pairs:
            existing_users[team_user.team.id].append(team_user.user.id)

        new_team_users = [
            TeamUser(user=user, team=team)
            for team in teams
            for user in users
            if user.id not in existing_users.get(team.id, [])
        ]

        TeamUser.objects.bulk_create(new_team_users)

        if existing_users:
            return handle_response(data={"existing_users": existing_users}, message='Some users already exist in some teams', status_code=status.HTTP_400_BAD_REQUEST)
        return handle_response(message='Users added to teams successfully', status_code=status.HTTP_200_OK)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    operation_description='Remove users from multiple teams',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'userIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.FORMAT_UUID)),
            'teamIds': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.FORMAT_UUID)),
        },
        required=['userIds', 'teamIds']
    ),
    responses={200: 'Users removed successfully'},
    manual_parameters=[token_header]
)
@api_view(['POST'])
@permission_classes([IsAdmin])
def remove_users_from_teams(request):
    try:
        userIds = request.data.get('userIds', [])
        teamIds = request.data.get('teamIds', [])

        for team_id in teamIds:
            team = get_object_or_404(Team, id=team_id)
            for user_id in userIds:
                user = get_object_or_404(User, id=user_id)
                TeamUser.objects.filter(user=user, team=team).delete()

        return handle_response(message='Users removed from teams successfully', status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
