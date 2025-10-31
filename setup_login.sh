#!/bin/bash
# Quick Start Guide for Login Feature

echo "=========================================="
echo "TimeWeave - Login Feature Setup"
echo "=========================================="
echo ""

# Navigate to src directory
cd /home/ubuntu/code/AI-for-SE/src

echo "Step 1: Running migrations..."
python3 manage.py makemigrations
python3 manage.py migrate

echo ""
echo "Step 2: Creating a test superuser (optional)..."
echo "You can create a superuser to access Django admin:"
echo "  python3 manage.py createsuperuser"
echo ""

echo "Step 3: Starting the development server..."
echo "Run the following command to start the server:"
echo "  python3 manage.py runserver 0.0.0.0:7799"
echo ""

echo "=========================================="
echo "Quick Test URLs:"
echo "=========================================="
echo "Home Page:      http://localhost:7799/"
echo "Register:       http://localhost:7799/register/"
echo "Login:          http://localhost:7799/login/"
echo "Dashboard:      http://localhost:7799/dashboard/ (requires login)"
echo "Admin Panel:    http://localhost:7799/admin/ (requires superuser)"
echo ""

echo "=========================================="
echo "Test Workflow:"
echo "=========================================="
echo "1. Go to /register/ and create a new account"
echo "2. After registration, you'll be automatically logged in"
echo "3. You'll be redirected to the dashboard"
echo "4. Try creating a new meeting request"
echo "5. Test the logout functionality"
echo "6. Try accessing /dashboard/ while logged out (should redirect to login)"
echo ""

echo "Setup complete! Happy testing! 🎉"
