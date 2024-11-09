import uuid
from django.db import models
from django.utils import timezone

from app.models.contact import Contact
from app.models.user import User
from app.models.team import Team
from app.models.vendor import Vendor

    
class CategoryBooking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'category_booking'

class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_bookings')
    contact_id = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, related_name='contact_bookings')
    team_id = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    category_id = models.ForeignKey(CategoryBooking, on_delete=models.SET_NULL, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    status = models.TextField()
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Booking'