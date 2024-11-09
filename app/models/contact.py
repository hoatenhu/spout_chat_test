import uuid
from django.db import models
from django.utils import timezone

from app.models.vendor import Vendor

class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    whatsappId = models.TextField(null=True)
    name = models.TextField()
    email = models.EmailField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Contact'