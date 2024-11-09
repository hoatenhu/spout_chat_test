from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from app.helpers.time_query import query_debugger
from app.models.vendor import Vendor
from app.serializers.vendor.vendor_serializer import VendorSerializer
from app.utils.handle_response import handle_response
from app.utils.permission import IsAdmin
from drf_yasg import openapi
from app.utils.utils import token_header

from app.views.user import CustomPagination
from django.db.models import Q

@swagger_auto_schema(
    method='get',
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
            description="Number of vendor per page",
            default=10 
        ),
        openapi.Parameter(
            'search', 
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            required=False, 
            description="Search term to filter vendors by name or industry"
        ),
        token_header
    ],
    operation_description='Retrieve all vendors',
    responses={200: VendorSerializer(many=True)}
)
@swagger_auto_schema(method='post', request_body=VendorSerializer, manual_parameters=[token_header])
@api_view(['GET', 'POST'])
@permission_classes([IsAdmin])
@query_debugger
def vendor_list(request):
    if request.method == 'GET':
        paginator = CustomPagination()
        vendors = Vendor.objects.all()
        search_query = request.GET.get('search', '')
        filters = Q()
        if search_query:
            filters |= Q(name__icontains=search_query)
            filters |= Q(industry__icontains=search_query)
            
        vendors = vendors.filter(filters)
        paginated_vendors = paginator.paginate_queryset(vendors, request)
        serializer = VendorSerializer(paginated_vendors, many=True)
        data = paginator.get_paginated_response(serializer.data).data
        return handle_response(data=data, message='Vendors retrieved successfully', status_code=status.HTTP_200_OK)
    
    if request.method == 'POST':
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data, message='Vendor created successfully', status_code=status.HTTP_201_CREATED)
        return handle_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get', 
    operation_description='Retrieve a specific vendor',
    responses={200: VendorSerializer()},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='patch', 
    operation_description='Update a specific vendor',                 
    request_body=VendorSerializer,
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='delete', 
    operation_description='Delete a specific vendor',
    responses={204: 'Vendor deleted successfully'},
    manual_parameters=[token_header]
)
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdmin])
def vendor_detail(request, pk):
    try:
        vendor = Vendor.objects.get(pk=pk)
    except Vendor.DoesNotExist:
        return handle_response(message='Vendor not found', status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = VendorSerializer(vendor)
        return handle_response(data=serializer.data, message='Vendor retrieved successfully', status_code=status.HTTP_200_OK)
    
    if request.method == 'PATCH':
        serializer = VendorSerializer(vendor, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data, message='Vendor updated successfully', status_code=status.HTTP_200_OK)
        return handle_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    if request.method == 'DELETE':
        vendor.delete()
        return handle_response(message='Vendor deleted successfully', status_code=status.HTTP_204_NO_CONTENT)
    
@swagger_auto_schema(
        method='delete',
        operation_description='Delete multiple vendors',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'vendorIds': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.FORMAT_UUID),
                    description='List of vendor IDs to delete'
                )
            },
            required=['vendorIds']
        ),
        manual_parameters=[token_header],
        responses={204: 'Vendors deleted successfully'}
    )
@api_view(['DELETE'])
@permission_classes([IsAdmin])
def delete_vendors(request):
    ids = request.data.get('vendorIds', [])
    if not ids:
        return handle_response(message='No vendor IDs provided', status_code=status.HTTP_400_BAD_REQUEST)

    vendors = Vendor.objects.filter(id__in=ids)
    if not vendors.exists():
        return handle_response(message='No vendors found for the provided IDs', status_code=status.HTTP_404_NOT_FOUND)

    vendors.delete()
    return handle_response(message='Vendors deleted successfully', status_code=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method='put',
    operation_description="Update multiple vendors",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'vendorIds': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.FORMAT_UUID),
                description='List of vendor IDs to update',
            ),
            'name': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Name to update for the vendors',
            ),
            'industry': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Industry to update for the vendors',
            ),
            'website': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Address to update for the vendors',
            ),
            'size': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Phone number to update for the vendors',
            ),
        }
    ),
    manual_parameters=[token_header],
    responses={200: 'Vendors updated successfully', 400: 'Bad Request', 404: 'Vendors not found'}
)
@api_view(['PUT'])
@permission_classes([IsAdmin])
@query_debugger
def update_vendors(request):
    try:
        vendor_ids = request.data.get('vendorIds', [])
        update_data = {key: value for key, value in request.data.items() if key != 'vendorIds'}
                
        if not vendor_ids or not update_data:
            return handle_response(message='Vendor IDs and update data must be provided', status_code=status.HTTP_400_BAD_REQUEST)
                
        vendors = Vendor.objects.filter(id__in=vendor_ids)
        if not vendors.exists():
            return handle_response(message='No vendors found with provided IDs', status_code=status.HTTP_404_NOT_FOUND)
                
        vendors.update(**update_data)
        updated_vendors = Vendor.objects.filter(id__in=vendor_ids)
        serializer = VendorSerializer(updated_vendors, many=True)
        return handle_response(data=serializer.data, message='Vendors updated successfully', status_code=status.HTTP_200_OK)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)