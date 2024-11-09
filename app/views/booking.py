from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from app.helpers.time_query import query_debugger
from app.models.booking import Booking, CategoryBooking
from app.models.contact import Contact
from app.models.team import TeamUser
from app.serializers.booking.booking_serializer import BookingSerializer, CreateBookingSerializer, UpdateBookingSerializer
from app.utils.handle_response import handle_response
from app.utils.permission import IsAdmin, IsAdminOrTeamAdmin
from drf_yasg import openapi
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from rest_framework.pagination import PageNumberPagination

from app.views.user import CustomPagination
from app.utils.utils import token_header

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
            description="Number of booking per page",
            default=10 
        ),
        openapi.Parameter(
            'search', 
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            required=False, 
            description="Search term to filter bookings by name or description"
        ),
        token_header
    ],
    operation_description='Retrieve all bookings',
    responses={200: BookingSerializer(many=True)}
)
@swagger_auto_schema(
    method='post', 
    operation_description='Create a new booking',
    request_body=BookingSerializer,
    manual_parameters=[token_header]
)
@api_view(['GET', 'POST'])
@permission_classes([IsAdminOrTeamAdmin])
@query_debugger
def booking_list(request):
    if request.method == 'GET':
        paginator = CustomPagination()
        bookings = Booking.objects.all()
        search_query = request.GET.get('search', '')
        filters = Q()
        if search_query:
            filters |= Q(title__icontains=search_query)
            filters |= Q(description__icontains=search_query)

        bookings = bookings.filter(vendor__id=request.user.vendor.id).filter(filters)
        paginated_bookings = paginator.paginate_queryset(bookings, request)
        serializer = BookingSerializer(paginated_bookings, many=True)
        data = paginator.get_paginated_response(serializer.data).data
        return handle_response(data=data, message='Bookings retrieved successfully', status_code=status.HTTP_200_OK)

    if request.method == 'POST':
        user_id = request.data.get('user_id') 
        start_at = request.data.get('start_at')  
        end_at = request.data.get('end_at') 

        if not user_id or not start_at or not end_at:
            return handle_response(data={'error': 'Missing user_id, start_at or end_at'}, status_code=status.HTTP_400_BAD_REQUEST)

        overlapping_bookings = Booking.objects.filter(
            Q(start_at__lt=end_at) & Q(end_at__gt=start_at),
            user_id=user_id
        )
       
        if overlapping_bookings.exists():
            return handle_response(data={'error': 'User already has a booking in this time range'}, status_code=status.HTTP_400_BAD_REQUEST)
        
        serializer = CreateBookingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return handle_response(data=serializer.data, message='Bookings created successfully', status_code=status.HTTP_201_CREATED)
        return handle_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get', 
    operation_description='Retrieve a specific booking',
    responses={200: BookingSerializer()},
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='patch', 
    operation_description='Update a specific booking',                 
    request_body=BookingSerializer,
    manual_parameters=[token_header]
)
@swagger_auto_schema(
    method='delete', 
    operation_description='Delete a specific booking',
    responses={204: 'Booking deleted successfully'},
    manual_parameters=[token_header]
)
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdmin])
def booking_detail(request, id):
    try:
        booking = Booking.objects.get(id=id)
    except Booking.DoesNotExist:
        return handle_response(message='Booking not found', status_code=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BookingSerializer(booking)
        return handle_response(data=serializer.data, message='Booking retrieved successfully', status_code=status.HTTP_200_OK)

    if request.method == 'PATCH':
        serializer = UpdateBookingSerializer(booking, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return handle_response(
                data=serializer.data, 
                message='Booking updated successfully', 
                status_code=status.HTTP_200_OK
            )
        return handle_response(data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        booking.delete()
        return handle_response(message='Booking deleted successfully', status_code=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='delete',
    operation_description='Delete multiple bookings',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'bookingIds': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.FORMAT_UUID),
                description='List of booking IDs to delete'
            )
        },
        required=['bookingIds']
    ),
    manual_parameters=[token_header],
    responses={204: 'Bookings deleted successfully'}
)
@api_view(['DELETE'])
@permission_classes([IsAdminOrTeamAdmin])
def delete_bookings(request):
    ids = request.data.get('bookingIds', [])
    if not ids:
        return handle_response(message='No booking IDs provided', status_code=status.HTTP_400_BAD_REQUEST)

    bookings = Booking.objects.filter(id__in=ids)
    if not bookings.exists():
        return handle_response(message='No bookings found for the provided IDs', status_code=status.HTTP_404_NOT_FOUND)

    bookings.delete()
    return handle_response(message='Bookings deleted successfully', status_code=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='put',
    operation_description="Update multiple bookings",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'bookingIds': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.FORMAT_UUID),
                description='List of booking IDs to update',
            ),
            'user_id': openapi.Schema(
                type=openapi.FORMAT_UUID,
                description='User to update for the bookings',
            ),
            'contact_id': openapi.Schema(
                type=openapi.FORMAT_UUID,
                description='Contact to update for the bookings',
            ),
            'team_id': openapi.Schema(
                type=openapi.FORMAT_UUID,
                description='Team to update for the bookings',
            ),
            'category_id': openapi.Schema(
                type=openapi.FORMAT_UUID,
                description='Category to update for the bookings',
            ),
            'title': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Title to update for the bookings',
            ),
            'status': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Status to update for the bookings',
            ),
            'start_at': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                description='Start time for the booking',
            ),
            'end_at': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                description='End time for the booking',
            ),
        }
    ),
    responses={200: 'Users updated successfully', 400: 'Bad Request', 404: 'Users not found'}
)
@api_view(['PUT'])
@permission_classes([IsAdminOrTeamAdmin])
@query_debugger
def update_bookings(request):
    try:
        booking_ids = request.data.get('bookingIds', [])
        user_id = request.data.get('user_id')
        start_at = request.data.get('start_at')
        end_at = request.data.get('end_at')
        num_booking_ids = len(booking_ids)
        update_data = {key: value for key, value in request.data.items() if key != 'bookingIds'}

       
        if not booking_ids or not update_data:
            return handle_response(message='Booking IDs and update data must be provided', status_code=status.HTTP_400_BAD_REQUEST)
                
        bookings = Booking.objects.filter(id__in=booking_ids)
        if not bookings.exists():
            return handle_response(message='No bookings found with provided IDs', status_code=status.HTTP_404_NOT_FOUND)

        if user_id and start_at and end_at:
            if num_booking_ids == 1:
                overlapping_bookings = Booking.objects.filter(
                    Q(start_at__lt=end_at) & Q(end_at__gt=start_at),
                    user_id=user_id
                ).exclude(id__in=booking_ids)
                if overlapping_bookings.exists():
                    return handle_response(
                        message='User has conflicting bookings during the specified time range',
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
            elif num_booking_ids > 1:
                    return handle_response(
                            message='Users cannot receive duplicate time reservations',
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
            
        bookings.update(**update_data)
        updated_bookings = Booking.objects.filter(id__in=booking_ids)
        serializer = UpdateBookingSerializer(updated_bookings, many=True)
        return handle_response(data=serializer.data, message='Bookings updated successfully', status_code=status.HTTP_200_OK)
    except Exception as e:
        return handle_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

#######################################################################################################
@swagger_auto_schema(
    method='get',
    operation_description='Retrieve bookings in a calendar format for a specific month and year.',
    manual_parameters=[
        openapi.Parameter(
            'month', 
            openapi.IN_QUERY, 
            description="Month of the year for which data is needed (1-12)", 
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'year', 
            openapi.IN_QUERY, 
            description="Year for which data is needed", 
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        token_header
    ], 
    responses={
        200: openapi.Response(
            description="Success - List of bookings by month and year",
        ),
        400: openapi.Response(
            description="Bad Request - Invalid month or year"
        )
    }
)
@api_view(['GET'])
def booking_calendar(request):
    month = request.GET.get('month')
    year = request.GET.get('year')

    if not month or not year:
        return handle_response(
            message="Month and year are required.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        month = int(month)
        year = int(year)
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
    except ValueError:
        return handle_response(
            message="Invalid month or year.",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    filters = Q()
    if request.user.role.roleName == "admin":
        filters &= Q(vendor__id=request.user.vendor.id)
    elif request.user.role.roleName == "team admin":
        team_user_ids = TeamUser.objects.filter(user_id=request.user.id).values_list('team_id', flat=True)
        filters &= Q(team_id__in=team_user_ids)

    bookings = Booking.objects.filter(filters).filter(start_at__gte=start_date, start_at__lt=end_date)
    calendar_data = {}

    for booking in bookings:
        booking_date = booking.start_at.date().strftime('%d-%m-%Y')

        if booking_date not in calendar_data:
            calendar_data[booking_date] = {
                'date': booking_date,
                'eventsAmount': 0,
                'events': []
            }

        calendar_data[booking_date]['eventsAmount'] += 1
        calendar_data[booking_date]['events'].append({
            'id': booking.id,
            'name': booking.title,  
            'timeStart': booking.start_at.strftime('%H:%M'),
            'timeEnd': booking.end_at.strftime('%H:%M'),
            'createdAt': booking.created_at.isoformat(),
            'user': {
                'id': booking.user_id.id if booking.user_id else "",
                'name': booking.user_id.username if booking.user_id else "",  
                'email': booking.user_id.email if booking.user_id else ""  
            },
            'contact': {
                'id': booking.contact_id.id if booking.contact_id else "",
                'name': booking.contact_id.name if booking.contact_id else "",
                'email': booking.contact_id.email if booking.contact_id else ""  
            },
            'category': {
                'id': booking.category_id.id if booking.category_id else "",
                'name': booking.category_id.title if booking.category_id else ""  
            }
        })

    return handle_response(
        data=list(calendar_data.values()),
        message="Calendar data retrieved successfully",
        status_code=status.HTTP_200_OK
    )

#######################################################################################################

class CustomPagination(PageNumberPagination):
    page_size = 6 
    page_size_query_param = 'limit' 
    max_page_size = 30 

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve bookings by date with optional filters for search, category, status, team, and staff.",
    manual_parameters=[
        openapi.Parameter(
            'date',
            openapi.IN_QUERY,
            description="Date for which to retrieve events (format: DD-MM-YYYY). This field is required.",
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'search',
            openapi.IN_QUERY,
            description="Search query to filter events by title or description.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'category_id',
            openapi.IN_QUERY,
            description="Filter by category ID.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description="Filter by event status.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'team_id',
            openapi.IN_QUERY,
            description="Filter by team ID.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'staff_id',
            openapi.IN_QUERY,
            description="Filter by staff/user ID.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'limit',
            openapi.IN_QUERY,
            description="Limit the number of events returned per page.",
            type=openapi.TYPE_INTEGER,
            required=False
        ),
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description="Page number to paginate through the events.",
            type=openapi.TYPE_INTEGER,
            required=False
        ),
        token_header
    ],
    responses={
        200: openapi.Response(
            description="Success - List of filtered bookings by date.",
        ),
        400: "Bad Request - Missing or invalid parameters",
        404: "Not Found - No events found on the given date"
    }
)
@api_view(['GET'])
def booking_calendar_by_date(request):
    date_str = request.GET.get('date', None)
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category_id')
    status_request = request.GET.get('status')
    team_id = request.GET.get('team_id')
    staff_id = request.GET.get('staff_id')

    paginator = CustomPagination()

    if not date_str:
        return handle_response(
            message="Date is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
    except ValueError:
        return handle_response(
            message="Invalid date format, expected DD-MM-YYYY",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    start_of_day = timezone.datetime.strptime(date_str, '%d-%m-%Y').date()
    end_of_day = start_of_day + timezone.timedelta(days=1)

    filters = Q(start_at__gte=start_of_day, start_at__lt=end_of_day)

    if search_query:
        filters &= Q(title__icontains=search_query) | Q(description__icontains=search_query)
    if category_id:
        filters &= Q(category_id=category_id)
    if status_request:
        filters &= Q(status=status_request)
    if team_id:
        filters &= Q(team_id=team_id)
    if staff_id:
        filters &= Q(user_id=staff_id)

    if request.user.role.roleName == "admin":
        filters &= Q(vendor__id=request.user.vendor.id)
    elif request.user.role.roleName == "team admin":
        team_user_ids = TeamUser.objects.filter(user_id=request.user.id).values_list('team_id', flat=True)
        filters &= Q(team_id__in=team_user_ids)

    bookings = Booking.objects.filter(filters)

    if not bookings.exists():
        return handle_response(
            message="No events found on this date",
            status_code=status.HTTP_404_NOT_FOUND
        )

    paginated_bookings = paginator.paginate_queryset(bookings, request)
    serializer = BookingSerializer(paginated_bookings, many=True)
    total_bookings = len(paginated_bookings)
    return handle_response(
        data={
            'total': total_bookings, 
            'events': serializer.data
        },
        message="Calendar data retrieved successfully",
        status_code=status.HTTP_200_OK
    )

#######################################################################################################
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve filtered bookings based on various criteria such as search query, category, status, team, staff, date range, and pagination.",
    manual_parameters=[
        openapi.Parameter(
            'search',
            openapi.IN_QUERY,
            description="Search query to filter bookings by title.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'category_id',
            openapi.IN_QUERY,
            description="Filter bookings by category ID.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            description="Filter bookings by status.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'team_id',
            openapi.IN_QUERY,
            description="Filter bookings by team ID.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'staff_id',
            openapi.IN_QUERY,
            description="Filter bookings by staff/user ID.",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'start_date',
            openapi.IN_QUERY,
            description="Filter bookings starting from this date (format: DD-MM-YYYY).",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'end_date',
            openapi.IN_QUERY,
            description="Filter bookings up to this date (format: DD-MM-YYYY).",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'date_limit',
            openapi.IN_QUERY,
            description="Limit the number of days returned.",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=10
        ),
        openapi.Parameter(
            'date_page',
            openapi.IN_QUERY,
            description="Page number for paginating through dates.",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=1
        ),
        openapi.Parameter(
            'event_limit',
            openapi.IN_QUERY,
            description="Limit the number of events returned per day.",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=60
        ),
        openapi.Parameter(
            'month', 
            openapi.IN_QUERY, 
            description="Month of the year for which data is needed (1-12)", 
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        openapi.Parameter(
            'year', 
            openapi.IN_QUERY, 
            description="Year for which data is needed", 
            type=openapi.TYPE_INTEGER,
            required=True
        ),
        token_header,
    ],
    responses={
        200: openapi.Response(
            description="Success - List of filtered bookings.",
        ),
        400: "Bad Request - Missing or invalid parameters",
    }
)
@api_view(['GET'])
def booking_filter(request):
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category_id')
    status_filter = request.GET.get('status')
    team_id = request.GET.get('team_id')
    staff_id = request.GET.get('staff_id')
    date_limit = int(request.GET.get('date_limit', 10))  
    date_page = int(request.GET.get('date_page', 1)) 
    event_limit = int(request.GET.get('event_limit', 60))  
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    month = request.GET.get('month')
    year = request.GET.get('year')

    filters = Q()

    if search_query:
        filters &= Q(title__icontains=search_query)

    if category_id:
        filters &= Q(category_id=category_id)

    if status_filter:
        filters &= Q(status=status_filter)

    if team_id:
        filters &= Q(team_id=team_id)

    if staff_id:
        filters &= Q(user_id=staff_id)

    if request.user.role.roleName == "admin":
        filters &= Q(vendor__id=request.user.vendor.id)
    elif request.user.role.roleName == "team admin":
        team_user_ids = TeamUser.objects.filter(user_id=request.user.id).values_list('team_id', flat=True)
        filters &= Q(team_id__in=team_user_ids)

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%d-%m-%Y')
            end_date = datetime.strptime(end_date_str, '%d-%m-%Y')
            filters &= Q(start_at__date__gte=start_date, start_at__date__lte=end_date)
        except ValueError:
            return handle_response(
                message="Invalid date. Date format must be DD-MM-YYYY.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    bookings = Booking.objects.filter(filters).order_by('start_at')

    if month and year:
        try:
            month = int(month)
            year = int(year)
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            bookings = bookings.filter(start_at__gte=start_date, start_at__lt=end_date)
        except ValueError:
            return handle_response(
                message="Invalid month or year.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    bookings_by_date = {}
    for booking in bookings:
        date_str = booking.start_at.strftime('%d-%m-%Y')
        if date_str not in bookings_by_date:
            bookings_by_date[date_str] = []
        bookings_by_date[date_str].append(booking)

    all_dates = sorted(bookings_by_date.keys())
    start_date_index = (date_page - 1) * date_limit
    end_date_index = date_page * date_limit
    paginated_dates = all_dates[start_date_index:end_date_index]

    data = []
    for date in paginated_dates:
        events = bookings_by_date[date]

        paginated_events = events[:event_limit]  

        serialized_events = BookingSerializer(paginated_events, many=True).data

        data.append({
            "date": date,
            "total_events": len(events), 
            "max_event": len(serialized_events),
            "events": serialized_events  
        })
    
    return handle_response(
        data={
            "total_days": len(bookings_by_date),  
            "date_page": date_page,
            "date_limit" : date_limit,
            "event_limit": event_limit,
            "data": data  
        },
        message="Calendar data retrieved successfully",
        status_code=status.HTTP_200_OK
    )