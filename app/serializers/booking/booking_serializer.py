from django.forms import ValidationError
from rest_framework import serializers
from app.models.booking import Booking, CategoryBooking
from app.models.vendor import Vendor
from app.serializers.contact.contact_serializer import ContactSerializer
from app.serializers.team.team_serializer import TeamSerializer
from app.serializers.user.user_serializer import UserSerializer

class CategoryBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryBooking
        fields = ['id', 'title']

class CreateBookingSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all(), required=False)

    class Meta:
        model = Booking
        fields = ['id', "vendor", 'user_id', 'contact_id', 'team_id', 'category_id', 'title', 
                  'description', 'status', 'start_at', 'end_at', 'created_at', 
                  'updated_at']
        
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['vendor'] = request.user.vendor
        return super().create(validated_data)
    
class UpdateBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', "vendor", 'user_id', 'contact_id', 'team_id', 'category_id', 'title', 
                  'description', 'status', 'start_at', 'end_at']

class BookingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['id', 'user', 'contact', 'team', 'category', 'title', 
                  'description', 'status', 'start_at', 'end_at', 'created_at', 
                  'updated_at']
        
    def get_user(self, obj):
        user = obj.user_id  
        if user:
            return UserSerializer(user).data  
        return None
    
    def get_contact(self, obj):
        contact = obj.contact_id  
        if contact:
            return ContactSerializer(contact).data  
        return None
    
    def get_category(self, obj):
        category = obj.category_id  
        if category:
            return CategoryBookingSerializer(category).data  
        return None
    
    def get_team(self, obj):
        team = obj.team_id  
        if team:
            return TeamSerializer(team).data  
        return None
