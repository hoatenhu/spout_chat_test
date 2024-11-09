from django.urls import path

from app.views.health import health_check
from app.views.role import role_detail, role_list
from app.views.team import add_users_to_teams, team_details, list_teams, remove_users_from_teams, delete_teams
from app.views.user import create_user, delete_users, invite_users, my_profile, update_users, generate_presigned_url, user_detail, user_list
from app.views.vendor import delete_vendors, update_vendors, vendor_detail, vendor_list
from app.views.booking import delete_bookings, update_bookings, booking_detail, booking_list, booking_calendar, booking_calendar_by_date, booking_filter
from app.views.booking_category import category_list, category_detail
from app.views.webhook import webhook
from .views.auth import change_password, forgot_password, login, logout, register, reset_password
from rest_framework_simplejwt.views import (TokenRefreshView)
from app.views.contact import list_contacts, contact_details
from app.views.room import room
from app.views.conversation import get_conversations_by_vendor, assign_user_and_team_to_conversation, change_assignment, add_users_to_conversation, remove_users_from_conversation, set_multiple_conversation_statuses

urlpatterns = [
    # Health Check
    path('health', health_check, name='health_check'),

    # Auth
    path('login', login, name='login'),
    path('register', register, name='register'),
    path('refresh-token', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password', forgot_password, name='forgot_password'),
    path('reset-password', reset_password, name='reset_password'),
    path('change-password', change_password, name='change_password'),
    path('logout', logout, name='logout'),

    # User
    path('users', user_list, name='user_list'),
    path('users/update', update_users, name='update_users'),
    path('users/create', create_user, name='create_user'),
    path('users/<uuid:pk>', user_detail, name='user_detail'),
    path('users/bulk', delete_users, name='delete_users'),
    path('users/invite', invite_users, name='invite_users'),

    # My Profile
    path('users/me', my_profile, name='my_profile'),
    path('generate-presigned-url', generate_presigned_url, name='generate-presigned-url'),

    # Role
    path('roles', role_list, name='role_list'),
    path('roles/<uuid:pk>', role_detail, name='role_detail'),

    # Vendor
    path('vendors', vendor_list, name='vendor_list'),
    path('vendors/<uuid:pk>', vendor_detail, name='vendor_detail'),
    path('vendors/bulk', delete_vendors, name='delete_vendors'),
    path('vendors/update', update_vendors, name='update_vendors'),
    
    # Team
    path('teams', list_teams, name='list-teams'), 
    path('teams/<uuid:id>', team_details, name='delete-team'), 
    path('teams/bulk', delete_teams, name='delete-teams'),
    path('teams/add-users', add_users_to_teams, name='add-users-to-team'),
    path('teams/remove-users', remove_users_from_teams, name='remove-users-from-team'),

    # Booking
    path('bookings', booking_list, name='booking_list'),
    path('bookings/<uuid:id>', booking_detail, name='booking_detail'),
    path('bookings/bulk', delete_bookings, name='delete_bookings'),
    path('bookings/calendar', booking_calendar, name='booking_calendar'), #lấy event theo từng ngày của tháng
    path('bookings/calendar-by-date', booking_calendar_by_date, name='bookings_by_date'), #lấy event theo ngày
    path('bookings/filter', booking_filter, name='bookings_by_date'),
    path('bookings/update', update_bookings, name='update_bookings'),

    # Category Booking
    path('category-bookings', category_list, name='category_list'),
    path('category-booking/<uuid:pk>', category_detail, name='category_detail'),

     # Contact
    path('contacts', list_contacts, name='contacts_list'),
    path('contacts/<uuid:id>', contact_details, name='category_detail'),

    # Chat
    path('chat/<str:room_name>/', room, name='room'),
    
    # Conversation
    path('conversations/by-vendor', get_conversations_by_vendor, name='conversations_by_vendor'),
    path('conversations/assign', assign_user_and_team_to_conversation, name='assign_user_and_team_to_conversation'),
    path('conversations/change-assignment', change_assignment, name='change_assignment'),
    path('conversations/add-users', add_users_to_conversation, name='add_users_to_conversation'),
    path('conversations/remove-users', remove_users_from_conversation, name='remove_users_from_conversation'),
    path('conversations/set-status', set_multiple_conversation_statuses, name='set_multiple_conversation_statuses'),
    
    # Webhook Whatsapp
    path("webhook", webhook, name="webhook"),
]
