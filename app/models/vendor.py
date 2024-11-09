import uuid
from django.db import models
from django.utils import timezone

class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    website = models.TextField(null=True)
    industry = models.TextField()
    size = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'Vendor'
    def __str__(self):
        return self.name