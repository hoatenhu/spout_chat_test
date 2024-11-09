from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes

from app.helpers.time_query import query_debugger
from app.models.booking import CategoryBooking
from app.serializers.booking.booking_serializer import CategoryBookingSerializer
from app.utils.handle_response import handle_response
from app.utils.permission import IsAdmin
from app.utils.utils import token_header


@swagger_auto_schema(
    method='get', 
    operation_description='Retrieve all Category',                 
    responses={200: CategoryBookingSerializer(many=True)},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='post', 
    operation_description='Create a new Category',
    request_body=CategoryBookingSerializer,
    manual_parameters=[token_header]
)
@api_view(['GET', 'POST'])
@permission_classes([IsAdmin])
@query_debugger
def category_list(request):
    if request.method == 'GET':
        roles = CategoryBooking.objects.all()
        serializer = CategoryBookingSerializer(roles, many=True)
        return handle_response(data=serializer.data, message='Category retrieved successfully', status_code=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = CategoryBookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data, message='Category created successfully', status_code=status.HTTP_201_CREATED)
        return handle_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get', 
    operation_description='Retrieve a specific Category',
    responses={200: CategoryBookingSerializer()},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='patch', 
    operation_description='Update a specific Category',
    request_body=CategoryBookingSerializer,
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='delete', 
    operation_description='Delete a specific Category',                 
    responses={204: 'Category deleted successfully'},
    manual_parameters=[token_header]
)
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdmin])
def category_detail(request, pk):
    try:
        category = CategoryBooking.objects.get(pk=pk)
    except CategoryBooking.DoesNotExist:
        return handle_response(message='Category not found', status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CategoryBookingSerializer(category)
        return handle_response(data=serializer.data, message='Category retrieved successfully', status_code=status.HTTP_200_OK)

    if request.method == 'PATCH':
        serializer = CategoryBookingSerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data, message='Category updated successfully', status_code=status.HTTP_200_OK)
        return handle_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        category.delete()
        return handle_response(message='Category deleted successfully', status_code=status.HTTP_204_NO_CONTENT)