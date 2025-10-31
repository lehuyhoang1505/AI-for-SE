"""
Views for Meeting Time Scheduler
Handles Leader and Member workflows
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json
import uuid

from .models import MeetingRequest, Participant, BusySlot, SuggestedSlot
from .user_profile import UserProfile
from .forms import (
    MeetingRequestForm, ParticipantForm, BulkParticipantForm,
    BusySlotForm, ParticipantResponseForm, UserRegistrationForm
)
from .utils import (
    generate_suggested_slots, get_top_suggestions, get_heatmap_data,
    parse_busy_slots_from_json
)
from .email_utils import send_verification_email, send_meeting_invitation_email, send_meeting_locked_notification


def get_or_create_creator_id(request):
    """Get or create a unique creator ID from session"""
    creator_id = request.session.get('creator_id')
    if not creator_id:
        creator_id = str(uuid.uuid4())
        request.session['creator_id'] = creator_id
    return creator_id


# =============================================================================
# AUTHENTICATION VIEWS
# =============================================================================

def user_login(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if email is verified
                profile = getattr(user, 'profile', None)
                if profile and not profile.email_verified:
                    messages.error(
                        request, 
                        'Email chưa được xác thực. Vui lòng kiểm tra email và xác thực tài khoản trước khi đăng nhập.'
                    )
                    # Add link to resend verification
                    resend_link = f'<a href="/resend-verification/?email={user.email}" class="btn btn-sm btn-primary">Gửi lại email xác thực</a>'
                    messages.info(
                        request,
                        resend_link,
                        extra_tags='safe'
                    )
                else:
                    login(request, user)
                    messages.success(request, f'Chào mừng {username}!')
                    # Redirect to next parameter or dashboard
                    next_url = request.GET.get('next', 'dashboard')
                    return redirect(next_url)
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
    else:
        form = AuthenticationForm()
    
    return render(request, 'meetings/login.html', {'form': form})


def user_register(request):
    """Registration page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # User can exist but can't login until verified
            user.save()
            
            # Create user profile (should be auto-created by signal, but ensure it exists)
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Generate verification token
            token = profile.generate_verification_token()
            
            # Build verification URL
            verification_url = request.build_absolute_uri(
                f'/verify-email/{token}/'
            )
            
            # Send verification email
            send_verification_email(user, verification_url)
            
            messages.success(
                request, 
                f'Đăng ký thành công! Một email xác thực đã được gửi đến {user.email}. '
                'Vui lòng kiểm tra email và xác thực tài khoản để đăng nhập.'
            )
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'meetings/register.html', {'form': form})


def user_logout(request):
    """Logout"""
    logout(request)
    messages.success(request, 'Đã đăng xuất thành công')
    return redirect('home')


# =============================================================================
# HOME & DASHBOARD
# =============================================================================

def home(request):
    """Landing page"""
    return render(request, 'meetings/home.html')


@login_required
def dashboard(request):
    """Leader dashboard showing all their meeting requests"""
    # Filter requests by the logged-in user
    recent_requests = MeetingRequest.objects.filter(
        created_by_email=request.user.email
    ).order_by('-created_at')[:20]
    
    # Add response counts and share URL to each request for template
    for req in recent_requests:
        req.responded_count = req.participants.filter(has_responded=True).count()
        req.total_count = req.participants.count()
        req.share_link = request.build_absolute_uri(req.get_share_url())
        # Convert response_rate to integer for CSS width (avoid decimal separator issues)
        req.response_rate_int = int(req.response_rate)
    
    return render(request, 'meetings/dashboard.html', {
        'requests': recent_requests
    })


# =============================================================================
# LEADER WORKFLOW - CREATE REQUEST (3-STEP WIZARD)
# =============================================================================

@login_required
def create_request_step1(request):
    """Step 1: Meeting configuration"""
    if request.method == 'POST':
        form = MeetingRequestForm(request.POST)
        if form.is_valid():
            meeting_request = form.save(commit=False)
            # Set creator email from logged-in user
            meeting_request.created_by_email = request.user.email
            meeting_request.creator_id = str(request.user.id)
            meeting_request.save()
            # Store ID in session for next steps
            request.session['meeting_request_id'] = str(meeting_request.id)
            return redirect('create_request_step2')
    else:
        # Set default values
        initial = {
            'date_range_start': timezone.now().date(),
            'date_range_end': timezone.now().date() + timedelta(days=7),
            'duration_minutes': 60,
            'timezone': 'Asia/Ho_Chi_Minh',
            'work_hours_start': '09:00',
            'work_hours_end': '18:00',
            'step_size_minutes': 30,
            'work_days_only': True,
            'created_by_email': request.user.email,
        }
        form = MeetingRequestForm(initial=initial)
    
    return render(request, 'meetings/create_step1.html', {'form': form})


@login_required
def create_request_step2(request):
    """Step 2: Add participants (optional)"""
    meeting_request_id = request.session.get('meeting_request_id')
    if not meeting_request_id:
        return redirect('create_request_step1')
    
    meeting_request = get_object_or_404(MeetingRequest, id=meeting_request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_participant':
            form = ParticipantForm(request.POST)
            if form.is_valid():
                participant = form.save(commit=False)
                participant.meeting_request = meeting_request
                participant.save()
                messages.success(request, f'Đã thêm {participant.name or participant.email}')
                return redirect('create_request_step2')
        
        elif action == 'add_bulk':
            bulk_form = BulkParticipantForm(request.POST)
            if bulk_form.is_valid():
                data = bulk_form.cleaned_data['participants_data']
                count = 0
                for line in data.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) == 2:
                        name, email = parts
                    elif len(parts) == 1:
                        name = ''
                        email = parts[0]
                    else:
                        continue
                    
                    # Convert empty email to None for NULL in database
                    email = email or None
                    
                    if email:
                        Participant.objects.get_or_create(
                            meeting_request=meeting_request,
                            email=email,
                            defaults={'name': name}
                        )
                    else:
                        # No email - create new participant with NULL email
                        Participant.objects.create(
                            meeting_request=meeting_request,
                            name=name or 'Anonymous',
                            email=None
                        )
                    count += 1
                
                messages.success(request, f'Đã thêm {count} người tham gia')
                return redirect('create_request_step2')
        
        elif action == 'next':
            return redirect('create_request_step3')
        
        elif action == 'skip':
            return redirect('create_request_step3')
    
    participants = meeting_request.participants.all()
    form = ParticipantForm()
    bulk_form = BulkParticipantForm()
    
    return render(request, 'meetings/create_step2.html', {
        'meeting_request': meeting_request,
        'participants': participants,
        'form': form,
        'bulk_form': bulk_form,
    })


@login_required
def create_request_step3(request):
    """Step 3: Review and finalize"""
    meeting_request_id = request.session.get('meeting_request_id')
    if not meeting_request_id:
        return redirect('create_request_step1')
    
    meeting_request = get_object_or_404(MeetingRequest, id=meeting_request_id)
    
    # Generate initial empty heatmap structure
    heatmap_data = get_heatmap_data(meeting_request)
    
    if request.method == 'POST':
        # Finalize and show share link
        meeting_request.status = 'active'
        meeting_request.save()
        
        # Clear session
        del request.session['meeting_request_id']
        
        return redirect('request_created', request_id=meeting_request.id)
    
    return render(request, 'meetings/create_step3.html', {
        'meeting_request': meeting_request,
        'heatmap_data': heatmap_data,
    })


@login_required
def request_created(request, request_id):
    """Success page after creating request"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Verify ownership
    if meeting_request.created_by_email != request.user.email:
        return HttpResponseForbidden('You do not have permission to view this request')
    
    share_url = request.build_absolute_uri(meeting_request.get_share_url())
    
    return render(request, 'meetings/request_created.html', {
        'meeting_request': meeting_request,
        'share_url': share_url,
    })


# =============================================================================
# LEADER WORKFLOW - VIEW & MANAGE REQUEST
# =============================================================================

@login_required
def view_request(request, request_id):
    """Leader view of a meeting request with full details and suggestions"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Verify ownership
    if meeting_request.created_by_email != request.user.email:
        return HttpResponseForbidden('You do not have permission to view this request')
    
    # Get participants and response status
    participants = meeting_request.participants.all()
    responded = participants.filter(has_responded=True)
    not_responded = participants.filter(has_responded=False)
    
    # Generate/update suggestions (but not if already locked to preserve the locked slot)
    if meeting_request.status != 'locked':
        generate_suggested_slots(meeting_request, force_recalculate=True)
    
    # Get top suggestions
    # If locked, get the locked slot directly, otherwise get top suggestions
    if meeting_request.status == 'locked':
        top_suggestions = SuggestedSlot.objects.filter(
            meeting_request=meeting_request,
            is_locked=True
        )
    else:
        top_suggestions = get_top_suggestions(meeting_request, limit=10)
    
    # Get heatmap data
    heatmap_data = get_heatmap_data(meeting_request)
    
    return render(request, 'meetings/view_request.html', {
        'meeting_request': meeting_request,
        'participants': participants,
        'responded': responded,
        'not_responded': not_responded,
        'top_suggestions': top_suggestions,
        'heatmap_data': heatmap_data,
    })


@login_required
def lock_slot(request, request_id, slot_id):
    """Lock a suggested slot as the final meeting time"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Verify ownership
    if meeting_request.created_by_email != request.user.email:
        return HttpResponseForbidden('You do not have permission to lock this slot')
    
    slot = get_object_or_404(SuggestedSlot, id=slot_id, meeting_request=meeting_request)
    
    # Delete all other slots (keep only the locked slot)
    SuggestedSlot.objects.filter(meeting_request=meeting_request).exclude(id=slot_id).delete()
    
    # Lock this slot
    slot.is_locked = True
    slot.save()
    
    # Update meeting request status
    meeting_request.status = 'locked'
    meeting_request.save()
    
    # Send notification emails to all participants
    participants_with_email = meeting_request.participants.exclude(email__isnull=True).exclude(email='')
    sent_count = 0
    for participant in participants_with_email:
        if send_meeting_locked_notification(participant, meeting_request, slot):
            sent_count += 1
    
    messages.success(request, f'Đã chốt khung giờ họp! Đã gửi thông báo đến {sent_count} người tham gia.')
    return redirect('view_request', request_id=request_id)


@login_required
def edit_request(request, request_id):
    """Edit meeting request settings"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Verify ownership
    if meeting_request.created_by_email != request.user.email:
        return HttpResponseForbidden('You do not have permission to edit this request')
    
    if request.method == 'POST':
        form = MeetingRequestForm(request.POST, instance=meeting_request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật cài đặt thành công!')
            return redirect('view_request', request_id=request_id)
    else:
        form = MeetingRequestForm(instance=meeting_request)
    
    return render(request, 'meetings/edit_request.html', {
        'meeting_request': meeting_request,
        'form': form,
    })


@login_required
def delete_request(request, request_id):
    """Delete a meeting request"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Verify ownership
    if meeting_request.created_by_email != request.user.email:
        return HttpResponseForbidden('You do not have permission to delete this request')
    
    if request.method == 'POST':
        title = meeting_request.title
        meeting_request.delete()
        messages.success(request, f'Đã xóa yêu cầu "{title}" thành công!')
        return redirect('dashboard')
    
    # If GET request, show confirmation page
    return render(request, 'meetings/confirm_delete.html', {
        'meeting_request': meeting_request
    })


# =============================================================================
# MEMBER WORKFLOW - RESPOND TO REQUEST
# =============================================================================

def respond_to_request(request, request_id):
    """Member view - fill in their availability"""
    # Get token from query params
    token = request.GET.get('t')
    
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Verify token
    if meeting_request.token != token:
        return HttpResponseForbidden('Invalid token')
    
    # Check if still active
    if not meeting_request.is_active:
        return render(request, 'meetings/request_closed.html', {
            'meeting_request': meeting_request
        })
    
    # Get or create participant from URL parameter first, then from session
    participant_id = request.GET.get('p') or request.session.get(f'participant_{request_id}')
    if participant_id:
        participant = Participant.objects.filter(id=participant_id).first()
    else:
        participant = None
    
    if request.method == 'POST':
        form = ParticipantResponseForm(request.POST)
        if form.is_valid():
            # Get or create participant
            if not participant:
                email = form.cleaned_data['email'] or None  # Convert empty string to None
                name = form.cleaned_data['name']
                timezone_val = form.cleaned_data['timezone']
                
                # If email is provided, use get_or_create with email as lookup key
                if email:
                    participant, created = Participant.objects.get_or_create(
                        meeting_request=meeting_request,
                        email=email,
                        defaults={
                            'name': name,
                            'timezone': timezone_val
                        }
                    )
                    if not created:
                        # Update existing participant info
                        participant.name = name
                        participant.timezone = timezone_val
                        participant.save()
                else:
                    # No email provided - create new participant with NULL email
                    # NULL emails don't violate unique constraint (multiple NULLs are allowed)
                    participant = Participant.objects.create(
                        meeting_request=meeting_request,
                        name=name or 'Ẩn danh',
                        email=None,
                        timezone=timezone_val
                    )
                
                # Use unique session key including participant ID to avoid conflicts
                session_key = f'participant_{request_id}_{participant.id}'
                request.session[session_key] = str(participant.id)
                # Also store the latest participant ID for this request
                request.session[f'participant_{request_id}'] = str(participant.id)
            else:
                # Update participant info
                participant.name = form.cleaned_data['name']
                participant.email = form.cleaned_data['email'] or None
                participant.timezone = form.cleaned_data['timezone']
                participant.save()
            
            # Redirect to calendar selection with token and participant ID
            return redirect(f'/r/{request_id}/select/?t={token}&p={participant.id}')
    else:
        initial = {}
        if participant:
            initial = {
                'name': participant.name,
                'email': participant.email,
                'timezone': participant.timezone,
            }
        form = ParticipantResponseForm(initial=initial)
    
    return render(request, 'meetings/respond_step1.html', {
        'meeting_request': meeting_request,
        'form': form,
        'token': token,
    })


def select_busy_times(request, request_id):
    """Member selects their busy time slots"""
    import json
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Get participant ID from URL parameter first (more reliable), then from session
    participant_id = request.GET.get('p') or request.session.get(f'participant_{request_id}')
    if not participant_id:
        # Redirect back to respond page with token
        token = request.GET.get('t', meeting_request.token)
        return redirect(f'/r/{request_id}/?t={token}')
    
    participant = get_object_or_404(Participant, id=participant_id)
    
    # Store in session for future use
    request.session[f'participant_{request_id}'] = str(participant.id)
    
    # Get existing busy slots for THIS participant only
    busy_slots = participant.busy_slots.all()
    
    # Get heatmap data in participant's timezone
    heatmap_data = get_heatmap_data(meeting_request, participant.timezone)
    
    # Serialize heatmap for JavaScript
    heatmap_data['heatmap_json'] = json.dumps(heatmap_data['heatmap'])
    
    return render(request, 'meetings/select_busy_times.html', {
        'meeting_request': meeting_request,
        'participant': participant,
        'busy_slots': busy_slots,
        'heatmap_data': heatmap_data,
        'token': request.GET.get('t', meeting_request.token),
    })


@csrf_exempt
@require_http_methods(["POST"])
def save_busy_slots(request, request_id):
    """API endpoint to save participant's busy slots"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Get participant from session
    participant_id = request.session.get(f'participant_{request_id}')
    if not participant_id:
        return JsonResponse({'error': 'No participant found'}, status=400)
    
    participant = get_object_or_404(Participant, id=participant_id)
    
    try:
        data = json.loads(request.body)
        busy_slots_data = data.get('busy_slots', [])
        
        # Clear existing busy slots
        participant.busy_slots.all().delete()
        
        # Parse and create new busy slots
        slots = parse_busy_slots_from_json(busy_slots_data, participant.timezone)
        
        for start_utc, end_utc in slots:
            BusySlot.objects.create(
                participant=participant,
                start_time=start_utc,
                end_time=end_utc
            )
        
        # Mark participant as responded
        participant.has_responded = True
        participant.responded_at = timezone.now()
        participant.save()
        
        # Regenerate suggestions
        generate_suggested_slots(meeting_request, force_recalculate=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Đã lưu thành công'
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


def response_complete(request, request_id):
    """Thank you page after member submits response"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    participant_id = request.session.get(f'participant_{request_id}')
    participant = None
    
    if participant_id:
        participant = Participant.objects.filter(id=participant_id).first()
    
    # Get top suggestions
    top_suggestions = get_top_suggestions(meeting_request, limit=5)
    
    # Calculate response stats for template
    responded_count = meeting_request.participants.filter(has_responded=True).count()
    total_count = meeting_request.participants.count()
    
    return render(request, 'meetings/response_complete.html', {
        'meeting_request': meeting_request,
        'participant': participant,
        'top_suggestions': top_suggestions,
        'responded_count': responded_count,
        'total_count': total_count,
    })


# =============================================================================
# API ENDPOINTS
# =============================================================================

def api_get_heatmap(request, request_id):
    """API endpoint to get heatmap data"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    timezone_param = request.GET.get('timezone', meeting_request.timezone)
    
    heatmap_data = get_heatmap_data(meeting_request, timezone_param)
    
    return JsonResponse(heatmap_data)


def api_get_suggestions(request, request_id):
    """API endpoint to get top suggestions"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    limit = int(request.GET.get('limit', 10))
    min_pct = int(request.GET.get('min_pct', 50))
    
    suggestions = get_top_suggestions(meeting_request, limit=limit, min_availability_pct=min_pct)
    
    data = []
    for suggestion in suggestions:
        data.append({
            'id': str(suggestion.id),
            'start_time': suggestion.start_time.isoformat(),
            'end_time': suggestion.end_time.isoformat(),
            'available_count': suggestion.available_count,
            'total_participants': suggestion.total_participants,
            'percentage': suggestion.availability_percentage,
            'heatmap_level': suggestion.heatmap_level,
        })
    
    return JsonResponse({'suggestions': data})


# =============================================================================
# EMAIL VERIFICATION
# =============================================================================

def verify_email(request, token):
    """Verify user email with token"""
    try:
        profile = UserProfile.objects.get(email_verification_token=token)
        
        # Check if token is still valid
        if not profile.is_verification_token_valid():
            messages.error(request, 'Link xác thực đã hết hạn. Vui lòng yêu cầu gửi lại email xác thực.')
            return redirect('resend_verification')
        
        # Verify email
        profile.verify_email()
        messages.success(request, 'Email đã được xác thực thành công! Bạn có thể đăng nhập ngay bây giờ.')
        return redirect('login')
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Link xác thực không hợp lệ.')
        return redirect('login')


def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Vui lòng nhập địa chỉ email.')
            return render(request, 'meetings/resend_verification.html')
        
        try:
            user = User.objects.get(email=email)
            profile = user.profile
            
            # Check if already verified
            if profile.email_verified:
                messages.info(request, 'Email này đã được xác thực. Bạn có thể đăng nhập.')
                return redirect('login')
            
            # Generate new token
            token = profile.generate_verification_token()
            
            # Build verification URL
            verification_url = request.build_absolute_uri(
                f'/verify-email/{token}/'
            )
            
            # Send verification email
            send_verification_email(user, verification_url)
            
            messages.success(
                request,
                f'Email xác thực đã được gửi lại đến {email}. Vui lòng kiểm tra hộp thư của bạn.'
            )
            return redirect('login')
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            messages.info(
                request,
                'Nếu email này tồn tại trong hệ thống, một email xác thực sẽ được gửi đến.'
            )
            return redirect('login')
    
    # GET request - show form
    email = request.GET.get('email', '')
    return render(request, 'meetings/resend_verification.html', {'email': email})


def send_meeting_invitations(request, request_id):
    """Send meeting invitations to all participants via email"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Verify ownership
    if meeting_request.created_by_email != request.user.email:
        return HttpResponseForbidden('You do not have permission to send invitations')
    
    # Get all participants with email addresses
    participants_with_email = meeting_request.participants.exclude(email__isnull=True).exclude(email='')
    
    sent_count = 0
    failed_count = 0
    
    for participant in participants_with_email:
        # Build respond URL with token and participant ID
        respond_url = request.build_absolute_uri(
            f'/r/{meeting_request.id}/?t={meeting_request.token}&p={participant.id}'
        )
        
        # Send invitation email
        if send_meeting_invitation_email(participant, meeting_request, respond_url):
            sent_count += 1
        else:
            failed_count += 1
    
    if sent_count > 0:
        messages.success(request, f'Đã gửi lời mời đến {sent_count} người tham gia.')
    
    if failed_count > 0:
        messages.warning(request, f'Không thể gửi email đến {failed_count} người.')
    
    return redirect('view_request', request_id=request_id)

