from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login, name='login'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('admin/users/', views.get_all_users, name='get-all-users'),
]