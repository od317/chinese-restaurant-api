from rest_framework import status
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, EmailVerificationSerializer
from rest_framework.permissions import IsAdminUser

User = get_user_model()


# In your views.py
from django.contrib.auth import authenticate, login
from django.contrib import messages

@api_view(['POST'])
def login(request):
    email = request.data.get('email')  # Use request.data for DRF
    password = request.data.get('password')
    
    user = authenticate(request, username=email, password=password)
    
    if user is not None:
        if user.is_verified:
            login(request, user)
            return Response({
                'message': 'Login successful!'
            }, status=status.HTTP_200_OK)  # Use 200 for successful login
        else:
            return Response({  # Added 'return'
                'message': 'Please verify your email address before logging in.'
            }, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({  # Added 'return'
            'message': 'Invalid email or password.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Render the login form again if not POST or if login failed

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