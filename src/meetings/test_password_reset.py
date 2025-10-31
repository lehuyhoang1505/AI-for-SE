"""
Test Password Reset Functionality
Run with: python3 manage.py test meetings.test_password_reset
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from meetings.user_profile import UserProfile


class PasswordResetTestCase(TestCase):
    """Test cases for password reset functionality"""
    
    def setUp(self):
        """Set up test client and create test user"""
        self.client = Client()
        self.test_email = 'test@example.com'
        self.test_username = 'testuser'
        self.old_password = 'oldpassword123'
        self.new_password = 'newpassword456'
        
        # Create test user
        self.user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.old_password
        )
        
        # Ensure profile exists
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
    
    def test_forgot_password_page_loads(self):
        """Test that forgot password page loads correctly"""
        response = self.client.get(reverse('forgot_password'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quên mật khẩu')
    
    def test_forgot_password_generates_token(self):
        """Test that requesting password reset generates a token"""
        response = self.client.post(reverse('forgot_password'), {
            'email': self.test_email
        })
        
        # Should redirect to login after successful submission
        self.assertEqual(response.status_code, 302)
        
        # Refresh profile from database
        self.profile.refresh_from_db()
        
        # Token should be generated
        self.assertIsNotNone(self.profile.password_reset_token)
        self.assertIsNotNone(self.profile.password_reset_token_created_at)
    
    def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email"""
        response = self.client.post(reverse('forgot_password'), {
            'email': 'nonexistent@example.com'
        })
        
        # Should still redirect (don't reveal if email exists)
        self.assertEqual(response.status_code, 302)
    
    def test_reset_password_with_valid_token(self):
        """Test resetting password with valid token"""
        # Generate reset token
        token = self.profile.generate_password_reset_token()
        
        # Access reset page
        response = self.client.get(reverse('reset_password', args=[token]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Đặt lại mật khẩu')
        
        # Submit new password
        response = self.client.post(reverse('reset_password', args=[token]), {
            'password1': self.new_password,
            'password2': self.new_password
        })
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Refresh user from database
        self.user.refresh_from_db()
        
        # Old password should not work
        self.assertFalse(self.user.check_password(self.old_password))
        
        # New password should work
        self.assertTrue(self.user.check_password(self.new_password))
        
        # Token should be cleared
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.password_reset_token)
    
    def test_reset_password_invalid_token(self):
        """Test reset password with invalid token"""
        response = self.client.get(reverse('reset_password', args=['invalid-token']))
        
        # Should redirect to forgot password page
        self.assertEqual(response.status_code, 302)
    
    def test_reset_password_mismatched_passwords(self):
        """Test reset password with mismatched passwords"""
        token = self.profile.generate_password_reset_token()
        
        response = self.client.post(reverse('reset_password', args=[token]), {
            'password1': 'password123',
            'password2': 'different456'
        })
        
        # Should show error and stay on same page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'không khớp')
    
    def test_reset_password_too_short(self):
        """Test reset password with password too short"""
        token = self.profile.generate_password_reset_token()
        
        response = self.client.post(reverse('reset_password', args=[token]), {
            'password1': 'short',
            'password2': 'short'
        })
        
        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ít nhất 8 ký tự')
    
    def test_token_validation(self):
        """Test token validation logic"""
        token = self.profile.generate_password_reset_token()
        
        # Token should be valid immediately after generation
        self.assertTrue(self.profile.is_password_reset_token_valid())
        
        # Clear token
        self.profile.clear_password_reset_token()
        
        # Token should no longer be valid
        self.assertFalse(self.profile.is_password_reset_token_valid())
    
    def test_authenticated_user_redirected_from_forgot_password(self):
        """Test that authenticated users are redirected from forgot password page"""
        # Login user
        self.client.login(username=self.test_username, password=self.old_password)
        
        # Try to access forgot password page
        response = self.client.get(reverse('forgot_password'))
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
