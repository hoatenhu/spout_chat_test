from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

from app.models.role import Role
from app.models.vendor import Vendor

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, editable=False)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    whatsappId = models.TextField(null=True)
    subjectId = models.TextField(null=True)
    email = models.EmailField(max_length=100, unique=True)
    avatar = models.TextField(null=True)
    firstName = models.TextField()
    lastName = models.TextField()
    phoneNumber = models.TextField(max_length=20,null=True)
    dateOfBirth = models.TextField(null=True)
    gender = models.TextField(null=True)
    countryCode = models.TextField(null=True)
    username = models.CharField(max_length=100, null=True, unique=True)
    position = models.TextField(null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    last_login = None 

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'User'
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['vendor']),
        ]
