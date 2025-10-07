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
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
import six


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


password_reset_token_generator = PasswordResetTokenGenerator()

@api_view(['POST'])
def password_reset_request(request):
    """
    Request password reset - sends email with reset link
    """
    email = request.data.get('email')
    
    if not email:
        return Response(
            {'error': 'Email is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        
        # Generate token and UID
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token_generator.make_token(user)
        
        # In production, you'll want to use your frontend URL here
        reset_url = f"http://localhost:3000/reset-password/{uid}/{token}/"
        
        # Send email
        send_mail(
            'Password Reset Request - Restaurant App',
            f'Click the link to reset your password: {reset_url}\n\n'
            f'This link will expire in 1 hour.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        # Always return success even if email doesn't exist (security best practice)
        return Response({
            'message': 'If an account with this email exists, a password reset link has been sent.'
        })
        
    except User.DoesNotExist:
        # Still return success for security (don't reveal which emails exist)
        return Response({
            'message': 'If an account with this email exists, a password reset link has been sent.'
        })

@api_view(['POST'])
def password_reset_confirm(request):
    """
    Confirm password reset with token and set new password
    """
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')  # Add password confirmation
    
    # Check all required fields including confirmation
    if not all([uid, token, new_password, confirm_password]):
        return Response(
            {'error': 'UID, token, new password and confirmation are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate that passwords match
    if new_password != confirm_password:
        return Response(
            {'error': 'Passwords do not match'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Optional: Add password strength validation here
    # You can add checks for minimum length, complexity, etc.
    if len(new_password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters long'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Decode UID
        user_id = urlsafe_base64_decode(uid)
        user_id = user_id.decode()  # Convert bytes to string if needed
        
        user = User.objects.get(pk=user_id)
        
        # Verify token
        if not password_reset_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired reset token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # FUTURE ENHANCEMENT: Send confirmation email that password was changed
        # send_mail(
        #     'Password Changed - Restaurant App',
        #     'Your password has been successfully changed.',
        #     settings.DEFAULT_FROM_EMAIL,
        #     [user.email],
        #     fail_silently=False,
        # )
        
        return Response({
            'message': 'Password reset successfully. You can now login with your new password.'
        })
        
    except (User.DoesNotExist, ValueError, OverflowError):
        return Response(
            {'error': 'Invalid reset link'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def password_change(request):
    """
    Change password for authenticated users
    """
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not all([current_password, new_password]):
        return Response(
            {'error': 'Current password and new password are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify current password
    if not request.user.check_password(current_password):
        return Response(
            {'error': 'Current password is incorrect'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    request.user.set_password(new_password)
    request.user.save()
    
    return Response({
        'message': 'Password changed successfully.'
    })

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