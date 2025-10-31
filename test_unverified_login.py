"""
Quick test to verify email verification login flow
Run this to test the unverified email login behavior
"""
import os
import sys
import django

sys.path.insert(0, '/home/ubuntu/code/AI-for-SE/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'time_mamager.settings')
django.setup()

from django.contrib.auth.models import User
from meetings.user_profile import UserProfile

def test_unverified_user():
    """Test that unverified users can't login"""
    print("=" * 60)
    print("Testing Unverified User Login Block")
    print("=" * 60)
    
    # Create test user with unverified email
    test_username = "test_unverified"
    test_email = "unverified@example.com"
    
    try:
        # Clean up if exists
        User.objects.filter(username=test_username).delete()
        
        # Create new user
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password="testpass123"
        )
        print(f"✅ Created user: {test_username}")
        
        # Check profile
        profile = user.profile
        print(f"✓ Email: {user.email}")
        print(f"✓ Email verified: {profile.email_verified}")
        print(f"✓ Has verification token: {profile.email_verification_token is not None}")
        
        # Generate token
        token = profile.generate_verification_token()
        print(f"\n✅ Generated verification token")
        print(f"🔗 Verification URL: http://localhost:8000/verify-email/{token}/")
        
        print(f"\n📝 To test:")
        print(f"1. Start server: python3 manage.py runserver")
        print(f"2. Try to login with:")
        print(f"   Username: {test_username}")
        print(f"   Password: testpass123")
        print(f"3. You should see:")
        print(f"   - Error message about unverified email")
        print(f"   - Button to resend verification email")
        print(f"4. Click the button or visit: http://localhost:8000/resend-verification/?email={test_email}")
        
        print("\n" + "=" * 60)
        print("Test User Created Successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unverified_user()
