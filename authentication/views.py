from rest_framework import status
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, EmailVerificationSerializer
from rest_framework.permissions import IsAdminUser
import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# In your views.py
from django.contrib.auth import authenticate, login
from django.contrib import messages

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(request, username=email, password=password)
    
    if user is not None:
        if user.is_verified:
            # Generate JWT tokens instead of using Django login
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful!',
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Please verify your email address before logging in.'
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({
            'message': 'Invalid email or password.'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register_user(request):
    if request.method == 'POST':
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User created successfully. Please check your email for verification code.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_email(request):
    if request.method == 'POST':
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            verification_code = serializer.validated_data['verification_code']
            
            try:
                user = User.objects.get(email=email, verification_code=verification_code)
                user.is_verified = True
                user.verification_code = None  # Clear the code after verification
                user.save()
                
                return Response({
                    'message': 'Email verified successfully! You can now login.'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': 'Invalid verification code or email.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def resend_verification_code(request):
    email = request.data.get('email')
    
    if not email:
        return Response(
            {'error': 'Email is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        
        # Check if user is already verified
        if user.is_verified:
            return Response(
                {'error': 'Email is already verified'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check cooldown period (2 minutes example)
        if (user.verification_sent_at and 
            timezone.now() < user.verification_sent_at + timedelta(minutes=2)):
            return Response(
                {'error': 'Please wait before requesting a new code'}, 
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Generate new verification code
        new_code = str(random.randint(100000, 999999))
        user.verification_code = new_code
        user.verification_sent_at = timezone.now()
        user.save()
        
        # Send new verification email
        send_mail(
            'New Verification Code - Restaurant App',
            f'Your new verification code is: {new_code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'New verification code sent successfully'
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'No account found with this email'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAdminUser])  # Restrict to admin users only
def get_all_users(request):
    users = User.objects.all()
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name':user.get_full_name(),
            'phone_number': user.phone_number,
            'role': user.role,
            'is_verified': user.is_verified,
            'date_joined': user.date_joined
        })
    return Response(user_data)