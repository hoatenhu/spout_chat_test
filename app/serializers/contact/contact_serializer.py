from rest_framework import serializers
from app.models.booking import Booking, CategoryBooking
from app.models.contact import Contact
from app.serializers.team.team_serializer import TeamSerializer
from app.serializers.user.user_serializer import UserSerializer
from app.serializers.vendor.vendor_serializer import VendorSerializer

class ContactSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    
    class Meta:
        model = Contact
        fields = ['id', 'vendor', 'whatsappId', 'name', 'email']
