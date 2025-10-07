from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_verify = serializers.CharField(write_only=True)
    full_name = serializers.CharField(required=True, max_length=255)  # Explicitly define as required

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password_verify', 'phone_number']
        extra_kwargs = {
            'phone_number': {'required': False}  # Make phone_number optional in API
        }

    def validate(self, data):
        if data['password'] != data['password_verify']:
            raise serializers.ValidationError("Passwords don't match.")
        return data

    def create(self, validated_data):
        # Extract passwords first
        password = validated_data.pop('password')
        validated_data.pop('password_verify')  # Remove verification field
        
        # Generate verification code
        verification_code = str(random.randint(100000, 999999))
        
        # Create user instance
        user = User(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            phone_number=validated_data.get('phone_number'),  # Use get() since it's optional
            is_verified=False,
            is_active=False,
            verification_code=verification_code
        )
        
        # Use the extracted password variable, not validated_data['password']
        user.set_password(password)
        user.save()
        
        # Send verification email
        send_mail(
            'Verify Your Email - Restaurant App',
            f'Your verification code is: {verification_code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return user
    
class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=6)