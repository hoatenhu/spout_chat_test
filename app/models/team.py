import uuid
from django.db import models
from django.utils import timezone

from app.models.user import User
from app.models.vendor import Vendor

class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'Team'
    def __str__(self):
        return self.name

class TeamUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'team_user'
        unique_together = ('user', 'team') 