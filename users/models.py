from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as DefaultUserManager
from django.conf import settings
import pytz



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
    username = None  

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['name']  

    
    objects = UserManager()

    def __str__(self):
        return self.email  

class GPTMessageLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    prompt = models.TextField()  
    gpt_response = models.TextField() 
    timestamp = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        # Convert timestamp to Europe/Kiev timezone
        kiev_tz = pytz.timezone('Europe/Kiev')
        timestamp_in_kiev = self.timestamp.astimezone(kiev_tz)
        return f"Log from {self.user} at {timestamp_in_kiev.strftime('%Y-%m-%d %H:%M:%S')}"