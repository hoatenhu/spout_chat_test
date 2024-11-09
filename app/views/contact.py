from django.shortcuts import get_object_or_404
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from app.helpers.time_query import query_debugger
from app.models.contact import Contact
from app.models.user import User
from app.serializers.contact.contact_serializer import ContactSerializer
from app.utils.handle_response import handle_response
from app.utils.permission import IsAdmin
from drf_yasg import openapi
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count

class CustomPagination(PageNumberPagination):
    page_size = 10 
    page_size_query_param = 'limit'
    max_page_size = 100

@swagger_auto_schema(
    method='get',
    operation_description="Get a list of contacts with pagination",
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
            description="Number of contact per page",
            default=10 
        )
    ],
    responses={200: 'Contacts retrieved successfully'}
)
@swagger_auto_schema(
    method='post',
    operation_description='Create a new contact',
    request_body=ContactSerializer,
    responses={201: ContactSerializer, 400: 'Validation error'}
)
@api_view(['GET','POST'])
# @permission_classes([IsAdmin])
@query_debugger
def list_contacts(request):
    if request.method == 'GET':
        try:
            paginator = CustomPagination()
            search_query = request.GET.get('search', '')
            filters = Q()
            if search_query:
                filters |= Q(name__icontains=search_query)
        
            contacts = Contact.objects.filter(filters)
            paginated_contacts = paginator.paginate_queryset(contacts, request)
            serializer = ContactSerializer(paginated_contacts, many=True)
            data = paginator.get_paginated_response(serializer.data).data
            return handle_response(data=data, message='Contacts retrieved successfully', status_code=status.HTTP_200_OK)
        except Exception as e:
            return handle_response(message=str(e), status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        try:
            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return handle_response(data=serializer.data, message='Contact created successfully', status_code=status.HTTP_201_CREATED)
            return handle_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    operation_description='Retrieve a specific contact',
    responses={200: ContactSerializer}
)
@swagger_auto_schema(
    method='patch',
    operation_description='Update a specific contact',
    request_body=ContactSerializer,
    responses={200: ContactSerializer, 400: 'Validation error'}
)
@swagger_auto_schema(
    method='delete',
    operation_description='Delete a specific contact',
    responses={204: 'No content'}
)
@api_view(['GET','PATCH','DELETE'])
# @permission_classes([IsAdmin])
def contact_details(request, id):
    try:
        contact = Contact.objects.get(id=id)
        if not contact:
             return handle_response(message='Contact not found', status_code=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = ContactSerializer(contact)
            return handle_response(data=serializer.data, message='Contact retrieved successfully', status_code=status.HTTP_200_OK)
        
        if request.method == 'PATCH':
            serializer = ContactSerializer(contact, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return handle_response(data=serializer.data, message='Contact updated successfully', status_code=status.HTTP_200_OK)
            return handle_response(message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            contact.delete()
            return handle_response(message='Contact deleted successfully', status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)