from rest_framework import serializers
from app.models.vendor import Vendor

class VendorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'website', 'industry', 'size']
