from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random
from django.utils import timezone   

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_verify = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password_verify', 'phone_number']
        extra_kwargs = {
            'phone_number': {'required': False}
        }

    def validate_email(self, value):
        """
        Custom validation for email field
        """
        try:
            user = User.objects.get(email=value)
            
            if user.is_verified:
                raise serializers.ValidationError("This email is already registered and verified.")
            else:
                raise serializers.ValidationError("This email is registered but not verified. You can resend verification code.")
                
        except User.DoesNotExist:
            # Email doesn't exist, which is good for registration
            pass
            
        return value

    def validate(self, data):
        if data['password'] != data['password_verify']:
            raise serializers.ValidationError("Passwords don't match.")
        return data

    def create(self, validated_data):
        # Check if unverified user already exists with this email
        email = validated_data['email']
        try:
            # If user exists but is not verified, we can update their info
            existing_user = User.objects.get(email=email, is_verified=False)
            
            # Update the existing unverified user
            existing_user.full_name = validated_data['full_name']
            existing_user.phone_number = validated_data.get('phone_number')
            existing_user.set_password(validated_data['password'])
            
            # Generate new verification code
            new_code = str(random.randint(100000, 999999))
            existing_user.verification_code = new_code
            existing_user.verification_sent_at = timezone.now()
            existing_user.save()
            
            user = existing_user
            
        except User.DoesNotExist:
            # Create new user
            password = validated_data.pop('password')
            validated_data.pop('password_verify')

            verification_code = str(random.randint(100000, 999999))
            
            user = User(
                email=validated_data['email'],
                phone_number=validated_data.get('phone_number'),
                full_name=validated_data['full_name'],
                is_verified=False,
                verification_code=verification_code,
                verification_sent_at=timezone.now()
            )
            user.set_password(password)
            user.save()

        # Send verification email
        send_mail(
            'Verify Your Email - Restaurant App',
            f'Your verification code is: {user.verification_code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return user
    
class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=6)