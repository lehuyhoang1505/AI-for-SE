# Forgot Password Feature - Quick Reference

## Overview
The forgot password feature allows users to reset their password via email if they forget it.

## How It Works

### 1. User Requests Password Reset
- User clicks "Quên mật khẩu?" link on login page
- Navigates to `/forgot-password/`
- Enters their email address
- System generates a unique reset token and sends email

### 2. User Receives Email
- Email contains a reset link with token: `/reset-password/{token}/`
- Token expires after 1 hour (configurable)
- Email template: `meetings/emails/password_reset.html`

### 3. User Resets Password
- User clicks link in email
- Enters new password twice (confirmation)
- Password must be at least 8 characters
- System validates token and updates password
- User redirected to login

## Files Added/Modified

### Models (`src/meetings/user_profile.py`)
Added fields to `UserProfile` model:
- `password_reset_token` - Unique token for password reset
- `password_reset_token_created_at` - Token creation timestamp

Added methods:
- `generate_password_reset_token()` - Creates new reset token
- `is_password_reset_token_valid()` - Checks if token is expired
- `clear_password_reset_token()` - Clears token after successful reset

### Views (`src/meetings/views.py`)
Added views:
- `forgot_password()` - Request password reset form
- `reset_password(request, token)` - Reset password with token

### URLs (`src/meetings/urls.py`)
Added URL patterns:
- `path('forgot-password/', views.forgot_password, name='forgot_password')`
- `path('reset-password/<str:token>/', views.reset_password, name='reset_password')`

### Templates
Created:
- `meetings/templates/meetings/forgot_password.html` - Request reset form
- `meetings/templates/meetings/reset_password.html` - New password form

Modified:
- `meetings/templates/meetings/login.html` - Added "Quên mật khẩu?" link

### Email Utilities (`src/meetings/email_utils.py`)
Already had `send_password_reset_email()` function - no changes needed

### Email Template
Already existed:
- `meetings/templates/meetings/emails/password_reset.html`

## Configuration

### Token Expiry
In `settings.py`, you can configure:
```python
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1  # Default: 1 hour
```

## Usage Flow

```
Login Page
    ↓ (click "Quên mật khẩu?")
Forgot Password Page (/forgot-password/)
    ↓ (enter email, submit)
Email Sent with Reset Link
    ↓ (click link in email)
Reset Password Page (/reset-password/{token}/)
    ↓ (enter new password, submit)
Password Updated → Redirect to Login
```

## Security Features

1. **Token Expiry**: Reset tokens expire after 1 hour
2. **Unique Tokens**: Each token is unique and can only be used once
3. **Email Privacy**: System doesn't reveal if email exists or not
4. **Password Requirements**: Minimum 8 characters
5. **Token Cleared**: After successful reset, token is cleared

## Testing

### Manual Testing
1. Go to login page: http://localhost:8000/login/
2. Click "Quên mật khẩu?"
3. Enter your email address
4. Check email for reset link
5. Click link and enter new password
6. Login with new password

### Test Accounts
Create a test user first:
```bash
cd src
python3 manage.py createsuperuser
```

### Check Email Logs
If RESEND_API_KEY is not configured, emails are logged to console instead.

## Database Migration

Migration created: `0005_userprofile_password_reset_token_and_more.py`

To apply migration (when database is available):
```bash
cd src
python3 manage.py migrate meetings
```

## Error Handling

- **Invalid Token**: "Link đặt lại mật khẩu không hợp lệ."
- **Expired Token**: "Link đặt lại mật khẩu đã hết hạn. Vui lòng yêu cầu link mới."
- **Password Mismatch**: "Mật khẩu không khớp."
- **Password Too Short**: "Mật khẩu phải có ít nhất 8 ký tự."

## Future Improvements

1. Add rate limiting to prevent abuse
2. Add CAPTCHA for forgot password form
3. Log password reset attempts
4. Add password strength meter
5. Support multiple active reset tokens per user
6. Add password history (prevent reusing old passwords)
