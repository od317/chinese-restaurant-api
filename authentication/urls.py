from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login, name='login'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('resend-code/', views.resend_verification_code, name='resend-code'),
    path('password-reset/', views.password_reset_request, name='password-reset'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    path('password-change/', views.password_change, name='password-change'),
    path('admin/users/', views.get_all_users, name='get-all-users'),
]