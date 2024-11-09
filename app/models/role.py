import uuid
from django.db import models
from django.utils import timezone

class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roleName = models.TextField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'Role'

    def __str__(self):
        return self.roleName