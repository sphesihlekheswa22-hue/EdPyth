#!/usr/bin/env python3
"""
Script to mark all existing users as email verified.
Run this once to allow existing users to login without email verification.
New users will still go through email verification.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def mark_existing_users_verified():
    """Mark all existing users as email verified."""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Get all users where email_verified is False
            users_to_verify = User.query.filter_by(email_verified=False).all()
            
            if not users_to_verify:
                print("No users found with unverified email addresses.")
                return
            
            print(f"Found {len(users_to_verify)} users with unverified email addresses.")
            
            # Mark all as verified
            for user in users_to_verify:
                user.email_verified = True
                user.email_verification_token = None
                user.email_verification_expires_at = None
                print(f"  - Marked {user.email} ({user.role}) as verified")
            
            # Commit changes
            db.session.commit()
            
            print(f"\nSuccessfully marked {len(users_to_verify)} users as email verified.")
            print("These users can now login without email verification.")
            print("New users will still go through email verification.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    mark_existing_users_verified()
