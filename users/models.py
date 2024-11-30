from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DefaultUserManager
from django.conf import settings
import pytz
import datetime
import uuid
from rest_framework.permissions import IsAuthenticated

class UserManager(DefaultUserManager):
    def create_superuser(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

# Custom User Model
class User(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    username = None  # Remove the default username field

    # Fields for Bearer token management
    token = models.CharField(max_length=64, blank=True, null=True)
    token_expiration = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'  # Use email instead of username for authentication
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.email

    def is_token_valid(self):
        """Check if the user's token is still valid."""
        return self.token and self.token_expiration > datetime.datetime.now(pytz.utc)

class GPTMessageLog(models.Model):
    permission_classes = [IsAuthenticated]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prompt = models.TextField()
    gpt_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional additional fields
    response_time = models.FloatField(blank=True, null=True)  # Time taken for response (in seconds)
    category = models.CharField(max_length=50, blank=True, null=True)  # Category or context of the request

    def __str__(self):
        # Convert timestamp to Europe/Kiev timezone
        kiev_tz = pytz.timezone('Europe/Kiev')
        timestamp_in_kiev = self.timestamp.astimezone(kiev_tz)
        return f"Log from {self.user.email} at {timestamp_in_kiev.strftime('%Y-%m-%d %H:%M:%S')}"
