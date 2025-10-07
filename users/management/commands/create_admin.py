from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a superuser by directly writing to the database, skipping the UserManager.'

    def handle(self, *args, **options):
        # Prompt the user for data
        self.stdout.write("Please enter the following details to create a superuser:")
        
        email = input("Email address: ")
        first_name = input("First name: ")
        last_name = input("Last name: ")
        phone_number = input("Phone number: ")
        password = input("Password: ")

        # Check if a user with this email already exists
        if not User.objects.filter(email=email).exists():
            
            # Create the user instance directly
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                is_verified=True,  # Set verified status on creation
                is_staff=True,     # Required for admin access
                is_superuser=True, # Required for admin access
                is_active=True,    # Ensure the user is active
                role='admin'       # Set the role
            )
            
            # Set the password correctly
            user.set_password(password)
            user.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'A user with the email {email} already exists.')
            )