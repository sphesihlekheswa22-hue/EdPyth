#!/usr/bin/env python3
"""Test email configuration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test email configuration
print("Testing email configuration...")
print(f"MAIL_SERVER: {os.environ.get('MAIL_SERVER')}")
print(f"MAIL_PORT: {os.environ.get('MAIL_PORT')}")
print(f"MAIL_USE_TLS: {os.environ.get('MAIL_USE_TLS')}")
print(f"MAIL_USERNAME: {os.environ.get('MAIL_USERNAME')}")
print(f"MAIL_PASSWORD: {'*' * len(os.environ.get('MAIL_PASSWORD', '')) if os.environ.get('MAIL_PASSWORD') else 'Not set'}")

# Test sending email
from app import create_app
app = create_app()

with app.app_context():
    from app.services.email_service import send_otp_email
    
    # Generate a test OTP
    test_otp = "123456"
    test_email = "sphesihlekheswa22@gmail.com"
    
    print(f"\nAttempting to send test OTP email to {test_email}...")
    result = send_otp_email(test_email, test_otp, 'registration')
    
    if result:
        print("✓ Email sent successfully!")
    else:
        print("✗ Failed to send email. Check your email configuration.")
