from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes

from app.helpers.time_query import query_debugger
from app.models.role import Role
from app.serializers.user.role_serializer import RoleSerializer
from app.utils.handle_response import handle_response
from app.utils.permission import IsAdmin
from app.utils.utils import token_header

@swagger_auto_schema(
    method='get', 
    operation_description='Retrieve all roles',                 
    responses={200: RoleSerializer(many=True)},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='post', 
    operation_description='Create a new role',
    request_body=RoleSerializer,
    manual_parameters=[token_header]
)
@api_view(['GET', 'POST'])
@permission_classes([IsAdmin])
@query_debugger
def role_list(request):
    if request.method == 'GET':
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return handle_response(data=serializer.data, message='Roles retrieved successfully', status_code=status.HTTP_200_OK)
    
    if request.method == 'POST':
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data, message='Role created successfully', status_code=status.HTTP_201_CREATED)
        return handle_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get', 
    operation_description='Retrieve a specific role',
    responses={200: RoleSerializer()},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='patch', 
    operation_description='Update a specific role',
    request_body=RoleSerializer,
    manual_parameters=[token_header]    
)
@swagger_auto_schema(
    method='delete', 
    operation_description='Delete a specific role',                 
    responses={204: 'Role deleted successfully'},
    manual_parameters=[token_header]
)
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdmin])
def role_detail(request, pk):
    try:
        role = Role.objects.get(pk=pk)
    except Role.DoesNotExist:
        return handle_response(message='Role not found', status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = RoleSerializer(role)
        return handle_response(data=serializer.data, message='Role retrieved successfully', status_code=status.HTTP_200_OK)
    
    if request.method == 'PATCH':
        serializer = RoleSerializer(role, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data, message='Role updated successfully', status_code=status.HTTP_200_OK)
        return handle_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'DELETE':
        role.delete()
        return handle_response(message='Role deleted successfully', status_code=status.HTTP_204_NO_CONTENT)
