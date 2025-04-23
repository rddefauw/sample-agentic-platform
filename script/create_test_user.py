# create_test_user.py
import boto3
import os
import argparse
import sys
import random
import string
import json

def generate_random_string(length=8):
    """Generate a random string of letters and digits"""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_random_email():
    """Generate a random email address for testing"""
    username = f"test-{generate_random_string(8)}"
    domain = "example.com"
    return f"{username}@{domain}"

def create_test_user(
    user_pool_id=None,
    email=None, 
    password=None, 
    auto_confirm=True, 
    set_permanent_password=True
):
    """Create a test user in the specified Cognito user pool"""
    # Use provided values or get from environment
    user_pool_id = user_pool_id or os.environ.get("COGNITO_USER_POOL_ID")
    
    # Generate random values if not provided
    email = email or generate_random_email()
    temporary_password = generate_random_string(12) + "Aa1!"  # Ensure it meets complexity requirements
    permanent_password = password or generate_random_string(12) + "Bb2@"  #B311: Just a test customer password to debug locally.
    
    # In this user pool, username must be an email
    username = email
    
    # Check if we have the required user pool ID
    if not user_pool_id:
        print("Error: Missing COGNITO_USER_POOL_ID")
        print("Please provide it as an argument or environment variable.")
        sys.exit(1)
    
    try:
        # Create Cognito client
        client = boto3.client('cognito-idp')
        
        # Create the user
        print(f"\nCreating user with email: {email}")
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            TemporaryPassword=temporary_password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true' if auto_confirm else 'false'
                }
            ],
            MessageAction='SUPPRESS'  # Don't send welcome email
        )
        print(f"User created successfully")
        
        # Auto-confirm the user if requested
        if auto_confirm:
            print("Auto-confirming user...")
            client.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {
                        'Name': 'email_verified',
                        'Value': 'true'
                    }
                ]
            )
            print("User confirmed")
        
        # Set permanent password if requested
        if set_permanent_password:
            print("Setting permanent password...")
            client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=email,
                Password=permanent_password,
                Permanent=True
            )
            print("Permanent password set")
        
        # Save user info to file for future reference
        user_info = {
            "user_pool_id": user_pool_id,
            "username": email,  # Username is the email
            "email": email,
            "password": permanent_password if set_permanent_password else temporary_password,
            "is_permanent_password": set_permanent_password
        }
        
        print("\nUser Summary:")
        print(f"  Email/Username: {email}")
        print(f"  Password: {permanent_password if set_permanent_password else temporary_password}")
        print(f"  Status: {'Confirmed' if auto_confirm else 'Unconfirmed'}")
        print(f"  Password Type: {'Permanent' if set_permanent_password else 'Temporary'}")
        
        return user_info
        
    except Exception as e:
        print(f"Error creating user: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Add command line arguments
    parser = argparse.ArgumentParser(description='Create a test user in Cognito')
    parser.add_argument('--user-pool-id', help='Cognito user pool ID')
    parser.add_argument('--email', help='Email address (random if not provided)')
    parser.add_argument('--password', help='Password (random if not provided)')
    parser.add_argument('--no-auto-confirm', action='store_true', help='Do not auto-confirm the user')
    parser.add_argument('--no-set-permanent-password', action='store_true', 
                        help='Do not set a permanent password (leave as temporary)')
    
    args = parser.parse_args()
    
    # Create user
    user_info = create_test_user(
        user_pool_id=args.user_pool_id,
        email=args.email,
        password=args.password,
        auto_confirm=not args.no_auto_confirm,
        set_permanent_password=not args.no_set_permanent_password
    )
    
    print("\nTest user created successfully!")
    print(f"You can now use these credentials with get_auth_token.py")
    print(f"Example command:")
    print(f"python script/get_auth_token.py --username '{user_info['email']}' --password '{user_info['password']}' --client-id <Get from TF output>")