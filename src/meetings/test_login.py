"""
Test Login Feature
Run this after setting up the login feature to verify everything works
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class AuthenticationTestCase(TestCase):
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_register_page_loads(self):
        """Test that registration page loads successfully"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Đăng ký tài khoản')
    
    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Đăng nhập')
    
    def test_user_registration(self):
        """Test user registration process"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # User should be created
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_user_login(self):
        """Test user login process"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        
        # User should be authenticated
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('dashboard'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_accessible_after_login(self):
        """Test that dashboard is accessible after login"""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Access dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_request_requires_login(self):
        """Test that creating request requires authentication"""
        response = self.client.get(reverse('create_request_step1'))
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_logout(self):
        """Test logout functionality"""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Logout
        response = self.client.get(reverse('logout'))
        
        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        
        # Dashboard should no longer be accessible
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
    
    def test_duplicate_email_registration(self):
        """Test that duplicate email registration is prevented"""
        response = self.client.post(reverse('register'), {
            'username': 'anotheruser',
            'email': 'test@example.com',  # Same email as test_user
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        
        # Should not create the user
        self.assertFalse(User.objects.filter(username='anotheruser').exists())


class NavigationTestCase(TestCase):
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_anonymous_user_navigation(self):
        """Test navigation for anonymous users"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Đăng nhập')
        self.assertContains(response, 'Đăng ký')
    
    def test_authenticated_user_navigation(self):
        """Test navigation for authenticated users"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'Đăng xuất')
        self.assertContains(response, 'Dashboard')


if __name__ == '__main__':
    print("Run these tests with: python manage.py test meetings.test_login")
