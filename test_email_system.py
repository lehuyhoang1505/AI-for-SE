#!/usr/bin/env python3
"""
Test script for email verification functionality
Tests the email system without actually sending emails
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/ubuntu/code/AI-for-SE/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'time_mamager.settings')
django.setup()

from django.contrib.auth.models import User
from meetings.user_profile import UserProfile
from meetings.email_utils import send_verification_email, send_meeting_invitation_email
from meetings.models import MeetingRequest, Participant
from django.utils import timezone
from datetime import timedelta

def test_email_verification():
    """Test email verification system"""
    print("=" * 60)
    print("Testing Email Verification System")
    print("=" * 60)
    
    # Check if test user exists
    test_username = "test_email_user"
    try:
        user = User.objects.get(username=test_username)
        print(f"✅ Found existing test user: {test_username}")
    except User.DoesNotExist:
        print(f"ℹ️  Creating test user: {test_username}")
        user = User.objects.create_user(
            username=test_username,
            email="test@example.com",
            password="testpass123"
        )
        print(f"✅ Created test user: {test_username}")
    
    # Check profile
    profile = user.profile
    print(f"\n📧 Email: {user.email}")
    print(f"✓ Email Verified: {profile.email_verified}")
    print(f"✓ Has Token: {profile.email_verification_token is not None}")
    
    # Generate verification token
    print("\n🔐 Generating verification token...")
    token = profile.generate_verification_token()
    print(f"✅ Token generated: {token[:20]}...")
    print(f"✓ Token created at: {profile.token_created_at}")
    
    # Check token validity
    is_valid = profile.is_verification_token_valid()
    print(f"✓ Token is valid: {is_valid}")
    
    # Test verification URL
    verification_url = f"http://localhost:8000/verify-email/{token}/"
    print(f"\n🔗 Verification URL:")
    print(f"   {verification_url}")
    
    # Simulate sending email
    print(f"\n📨 Simulating email send...")
    result = send_verification_email(user, verification_url)
    print(f"✓ Send result: {'Success' if result else 'Failed (expected without API key)'}")
    
    # Test verify email
    print(f"\n✅ Testing email verification...")
    profile.verify_email()
    profile.refresh_from_db()
    print(f"✓ Email verified: {profile.email_verified}")
    print(f"✓ Token cleared: {profile.email_verification_token is None}")
    
    print("\n" + "=" * 60)
    print("Email Verification Test Complete!")
    print("=" * 60)
    
    return user

def test_meeting_invitations():
    """Test meeting invitation emails"""
    print("\n" + "=" * 60)
    print("Testing Meeting Invitation Emails")
    print("=" * 60)
    
    # Get or create test meeting
    try:
        meeting = MeetingRequest.objects.filter(title="Test Meeting Email").first()
        if not meeting:
            print("ℹ️  Creating test meeting...")
            meeting = MeetingRequest.objects.create(
                title="Test Meeting Email",
                description="Testing email invitations",
                duration_minutes=60,
                date_range_start=timezone.now().date(),
                date_range_end=timezone.now().date() + timedelta(days=7),
                created_by_email="organizer@example.com",
                creator_id="test_creator"
            )
            print(f"✅ Created test meeting: {meeting.title}")
        else:
            print(f"✅ Found existing test meeting: {meeting.title}")
    except Exception as e:
        print(f"❌ Error creating meeting: {e}")
        return
    
    # Create test participant
    try:
        participant = Participant.objects.filter(
            meeting_request=meeting,
            email="participant@example.com"
        ).first()
        
        if not participant:
            print("ℹ️  Creating test participant...")
            participant = Participant.objects.create(
                meeting_request=meeting,
                name="Test Participant",
                email="participant@example.com"
            )
            print(f"✅ Created test participant: {participant.name}")
        else:
            print(f"✅ Found existing test participant: {participant.name}")
    except Exception as e:
        print(f"❌ Error creating participant: {e}")
        return
    
    # Test invitation email
    respond_url = f"http://localhost:8000/r/{meeting.id}/?t={meeting.token}&p={participant.id}"
    print(f"\n📨 Testing invitation email...")
    print(f"✓ Recipient: {participant.email}")
    print(f"✓ Meeting: {meeting.title}")
    print(f"🔗 Respond URL:")
    print(f"   {respond_url}")
    
    result = send_meeting_invitation_email(participant, meeting, respond_url)
    print(f"✓ Send result: {'Success' if result else 'Failed (expected without API key)'}")
    
    print("\n" + "=" * 60)
    print("Meeting Invitation Test Complete!")
    print("=" * 60)

def show_configuration():
    """Show current email configuration"""
    print("\n" + "=" * 60)
    print("Current Email Configuration")
    print("=" * 60)
    
    from django.conf import settings
    
    has_api_key = bool(settings.RESEND_API_KEY)
    print(f"✓ RESEND_API_KEY: {'Set ✅' if has_api_key else 'Not set (emails to console)'}")
    print(f"✓ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"✓ SITE_URL: {settings.SITE_URL}")
    print(f"✓ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"✓ TOKEN_EXPIRY: {settings.EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS} hours")
    
    if not has_api_key:
        print("\nℹ️  To enable real email sending:")
        print("   1. Get API key from https://resend.com/")
        print("   2. Set environment variable:")
        print("      export RESEND_API_KEY='re_xxxxxxxxxxxxx'")
        print("   3. Set DEFAULT_FROM_EMAIL to verified domain")
    
    print("=" * 60)

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("EMAIL FUNCTIONALITY TEST SUITE")
    print("=" * 60)
    
    try:
        # Show configuration
        show_configuration()
        
        # Test email verification
        user = test_email_verification()
        
        # Test meeting invitations
        test_meeting_invitations()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS COMPLETED!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Set RESEND_API_KEY to test with real emails")
        print("2. Register a new user in the web interface")
        print("3. Check console for verification email")
        print("4. Create meeting and send invitations")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
