"""
Email Utility Functions using Resend API
Handles sending emails for verification, invitations, and notifications
"""
import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_email_via_resend(to_email, subject, html_content, from_email=None):
    """
    Send email using Resend API
    
    Args:
        to_email: Recipient email address (str or list)
        subject: Email subject
        html_content: HTML content of the email
        from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL if not provided)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import resend
        
        # Set API key
        api_key = settings.RESEND_API_KEY
        if not api_key:
            logger.warning("RESEND_API_KEY not configured. Email not sent.")
            # For development, print to console
            logger.info(f"Email would be sent to: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content: {html_content}")
            return False
        
        resend.api_key = api_key
        
        # Prepare sender
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        # Send email
        params = {
            "from": from_email,
            "to": [to_email] if isinstance(to_email, str) else to_email,
            "subject": subject,
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Email sent successfully to {to_email}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_verification_email(user, verification_url):
    """
    Send email verification link to new user
    
    Args:
        user: User instance
        verification_url: Full URL for email verification
    
    Returns:
        bool: True if successful, False otherwise
    """
    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': 'TimeWeave',
    }
    
    # Render HTML template
    html_content = render_to_string('meetings/emails/verify_email.html', context)
    
    subject = 'Xác thực email của bạn - TimeWeave'
    
    return send_email_via_resend(
        to_email=user.email,
        subject=subject,
        html_content=html_content
    )


def send_meeting_invitation_email(participant, meeting_request, respond_url):
    """
    Send meeting invitation to participant
    
    Args:
        participant: Participant instance
        meeting_request: MeetingRequest instance
        respond_url: Full URL for participant to respond
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not participant.email:
        return False
    
    context = {
        'participant': participant,
        'meeting_request': meeting_request,
        'respond_url': respond_url,
        'site_name': 'TimeWeave',
    }
    
    # Render HTML template
    html_content = render_to_string('meetings/emails/meeting_invitation.html', context)
    
    subject = f'Mời tham gia cuộc họp: {meeting_request.title}'
    
    return send_email_via_resend(
        to_email=participant.email,
        subject=subject,
        html_content=html_content
    )


def send_meeting_locked_notification(participant, meeting_request, locked_slot):
    """
    Notify participant that meeting time has been finalized
    
    Args:
        participant: Participant instance
        meeting_request: MeetingRequest instance
        locked_slot: SuggestedSlot instance that was locked
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not participant.email:
        return False
    
    context = {
        'participant': participant,
        'meeting_request': meeting_request,
        'locked_slot': locked_slot,
        'site_name': 'TimeWeave',
    }
    
    # Render HTML template
    html_content = render_to_string('meetings/emails/meeting_locked.html', context)
    
    subject = f'Cuộc họp đã được chốt: {meeting_request.title}'
    
    return send_email_via_resend(
        to_email=participant.email,
        subject=subject,
        html_content=html_content
    )


def send_password_reset_email(user, reset_url):
    """
    Send password reset link to user
    
    Args:
        user: User instance
        reset_url: Full URL for password reset
    
    Returns:
        bool: True if successful, False otherwise
    """
    context = {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'TimeWeave',
    }
    
    # Render HTML template
    html_content = render_to_string('meetings/emails/password_reset.html', context)
    
    subject = 'Đặt lại mật khẩu - TimeWeave'
    
    return send_email_via_resend(
        to_email=user.email,
        subject=subject,
        html_content=html_content
    )
