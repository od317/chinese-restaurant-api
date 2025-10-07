from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    ]
    username = None  # Remove username field
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15,blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    full_name = models.CharField(('full name'), max_length=255,default='')
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def get_full_name(self):
        return self.full_name

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=[
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other')
    ])
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='YourCountry')
    is_primary = models.BooleanField(default=False)
    delivery_instructions = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.address_type} - {self.street_address}"