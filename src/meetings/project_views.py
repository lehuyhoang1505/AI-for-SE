"""
Views for Project Management System
Handles project CRUD, task management, and progress tracking
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json

from .project_models import (
    Project, TodoTask, TaskComment, TaskHistory, 
    TaskTag, ProjectMembership, ProjectProgress
)
from .project_forms import (
    ProjectForm, TodoTaskForm, TaskCommentForm, 
    TaskFilterForm, QuickTaskForm, MembershipForm
)
from .project_utils import (
    calculate_project_statistics,
    calculate_completion_probability,
    get_task_velocity,
    get_member_workload,
    create_progress_snapshot,
    get_project_timeline_data,
    get_recommended_tasks,
    create_task_history_entry,
    get_overdue_tasks_report,
    filter_tasks,
    get_project_health_score
)


# =============================================================================
# PROJECT CRUD OPERATIONS
# =============================================================================

@login_required
def project_list(request):
    """List all projects user is involved in"""
    # Projects where user is leader or member
    user_projects = Project.objects.filter(
        Q(leader=request.user) | Q(members=request.user)
    ).distinct().select_related('leader').prefetch_related('members')
    
    # Add statistics to each project
    for project in user_projects:
        project.stats = calculate_project_statistics(project)
        project.health_score = get_project_health_score(project)
        project.probability = calculate_completion_probability(project)
    
    # Separate by status
    active_projects = [p for p in user_projects if p.status in ['planning', 'active']]
    other_projects = [p for p in user_projects if p.status not in ['planning', 'active']]
    
    return render(request, 'meetings/projects/project_list.html', {
        'active_projects': active_projects,
        'other_projects': other_projects,
    })


@login_required
def project_detail(request, project_id):
    """View project details with tasks and analytics"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user has access
    if request.user != project.leader and request.user not in project.members.all():
        return HttpResponseForbidden('Bạn không có quyền truy cập dự án này')
    
    # Get filter parameters
    filter_form = TaskFilterForm(request.GET, project=project)
    
    # Apply filters
    tasks = project.tasks.all().select_related('created_by').prefetch_related('assignees', 'tags')
    
    if filter_form.is_valid():
        filters = {
            'status': filter_form.cleaned_data.get('status'),
            'priority': filter_form.cleaned_data.get('priority'),
            'assignee': filter_form.cleaned_data.get('assignee'),
            'tag': filter_form.cleaned_data.get('tag'),
            'search': filter_form.cleaned_data.get('search'),
        }
        tasks = filter_tasks(project, filters)
    
    # Get project statistics
    stats = calculate_project_statistics(project)
    probability = calculate_completion_probability(project)
    velocity = get_task_velocity(project)
    workload = get_member_workload(project)
    health_score = get_project_health_score(project)
    
    # Get recommended tasks for current user
    recommended = get_recommended_tasks(request.user, project)
    
    # Quick task form
    quick_form = QuickTaskForm()
    
    return render(request, 'meetings/projects/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'stats': stats,
        'probability': probability,
        'velocity': velocity,
        'workload': workload,
        'health_score': health_score,
        'recommended': recommended,
        'filter_form': filter_form,
        'quick_form': quick_form,
    })


@login_required
def project_create(request):
    """Create a new project"""
    if request.method == 'POST':
        form = ProjectForm(request.POST, user=request.user)
        if form.is_valid():
            project = form.save()
            
            messages.success(request, f'Dự án "{project.name}" đã được tạo thành công!')
            return redirect('project_detail', project_id=project.id)
    else:
        # Set default dates
        initial = {
            'start_date': timezone.now().date(),
            'deadline': timezone.now().date() + timezone.timedelta(days=30),
            'status': 'planning',
            'priority': 'medium',
        }
        form = ProjectForm(initial=initial, user=request.user)
    
    return render(request, 'meetings/projects/project_form.html', {
        'form': form,
        'title': 'Tạo dự án mới',
        'submit_text': 'Tạo dự án',
    })


@login_required
def project_edit(request, project_id):
    """Edit existing project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Only leader can edit project
    if request.user != project.leader:
        return HttpResponseForbidden('Chỉ trưởng nhóm mới có thể chỉnh sửa dự án')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dự án đã được cập nhật!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project, user=request.user)
    
    return render(request, 'meetings/projects/project_form.html', {
        'form': form,
        'project': project,
        'title': f'Chỉnh sửa dự án: {project.name}',
        'submit_text': 'Cập nhật',
    })


@login_required
def project_delete(request, project_id):
    """Delete a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Only leader can delete project
    if request.user != project.leader:
        return HttpResponseForbidden('Chỉ trưởng nhóm mới có thể xóa dự án')
    
    if request.method == 'POST':
        name = project.name
        project.delete()
        messages.success(request, f'Dự án "{name}" đã được xóa')
        return redirect('project_list')
    
    return render(request, 'meetings/projects/project_confirm_delete.html', {
        'project': project
    })


# =============================================================================
# TASK CRUD OPERATIONS
# =============================================================================

@login_required
def task_create(request, project_id):
    """Create a new task"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is a member
    if request.user not in project.members.all():
        return HttpResponseForbidden('Bạn không có quyền tạo task trong dự án này')
    
    if request.method == 'POST':
        form = TodoTaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            form.save_m2m()  # Save many-to-many relationships
            
            # Create history entry
            create_task_history_entry(
                task=task,
                user=request.user,
                action='created',
                description=f'Task "{task.title}" được tạo'
            )
            
            messages.success(request, f'Task "{task.title}" đã được tạo!')
            return redirect('project_detail', project_id=project.id)
    else:
        initial = {
            'due_date': timezone.now().date() + timezone.timedelta(days=7),
            'status': 'todo',
            'priority': 'medium',
            'progress_percentage': 0,
        }
        form = TodoTaskForm(initial=initial, project=project)
    
    return render(request, 'meetings/projects/task_form.html', {
        'form': form,
        'project': project,
        'title': 'Tạo task mới',
        'submit_text': 'Tạo task',
    })


@login_required
def task_quick_create(request, project_id):
    """Quick create task via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is a member
    if request.user not in project.members.all():
        return JsonResponse({'error': 'Không có quyền'}, status=403)
    
    form = QuickTaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.created_by = request.user
        task.save()
        
        # Create history entry
        create_task_history_entry(
            task=task,
            user=request.user,
            action='created',
            description=f'Task "{task.title}" được tạo (quick add)'
        )
        
        return JsonResponse({
            'success': True,
            'task_id': str(task.id),
            'task_title': task.title,
        })
    else:
        return JsonResponse({'error': 'Dữ liệu không hợp lệ', 'errors': form.errors}, status=400)


@login_required
def task_detail(request, project_id, task_id):
    """View task details with comments and history"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(TodoTask, id=task_id, project=project)
    
    # Check access
    if request.user not in project.members.all():
        return HttpResponseForbidden('Bạn không có quyền xem task này')
    
    # Handle comment submission
    if request.method == 'POST':
        comment_form = TaskCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            
            # Create history entry
            create_task_history_entry(
                task=task,
                user=request.user,
                action='commented',
                description='Thêm bình luận'
            )
            
            messages.success(request, 'Bình luận đã được thêm')
            return redirect('task_detail', project_id=project.id, task_id=task.id)
    else:
        comment_form = TaskCommentForm()
    
    # Get comments and history
    comments = task.comments.select_related('user').order_by('created_at')
    history = task.history.select_related('user').order_by('-created_at')[:20]
    
    return render(request, 'meetings/projects/task_detail.html', {
        'project': project,
        'task': task,
        'comments': comments,
        'history': history,
        'comment_form': comment_form,
    })


@login_required
def task_edit(request, project_id, task_id):
    """Edit existing task"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(TodoTask, id=task_id, project=project)
    
    # Check access
    if request.user not in project.members.all():
        return HttpResponseForbidden('Bạn không có quyền chỉnh sửa task này')
    
    # Store old values for history
    old_status = task.status
    old_priority = task.priority
    
    if request.method == 'POST':
        form = TodoTaskForm(request.POST, instance=task, project=project)
        if form.is_valid():
            task = form.save()
            
            # Create history entries for significant changes
            if old_status != task.status:
                create_task_history_entry(
                    task=task,
                    user=request.user,
                    action='status_changed',
                    old_value=old_status,
                    new_value=task.status,
                    description=f'Trạng thái thay đổi từ "{old_status}" sang "{task.status}"'
                )
            
            if old_priority != task.priority:
                create_task_history_entry(
                    task=task,
                    user=request.user,
                    action='priority_changed',
                    old_value=old_priority,
                    new_value=task.priority,
                    description=f'Ưu tiên thay đổi từ "{old_priority}" sang "{task.priority}"'
                )
            
            messages.success(request, 'Task đã được cập nhật!')
            return redirect('task_detail', project_id=project.id, task_id=task.id)
    else:
        form = TodoTaskForm(instance=task, project=project)
    
    return render(request, 'meetings/projects/task_form.html', {
        'form': form,
        'project': project,
        'task': task,
        'title': f'Chỉnh sửa task: {task.title}',
        'submit_text': 'Cập nhật',
    })


@login_required
def task_delete(request, project_id, task_id):
    """Delete a task"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(TodoTask, id=task_id, project=project)
    
    # Only task creator or project leader can delete
    if request.user != task.created_by and request.user != project.leader:
        return HttpResponseForbidden('Bạn không có quyền xóa task này')
    
    if request.method == 'POST':
        title = task.title
        task.delete()
        
        # Update project completion
        project.update_completion_percentage()
        
        messages.success(request, f'Task "{title}" đã được xóa')
        return redirect('project_detail', project_id=project.id)
    
    return render(request, 'meetings/projects/task_confirm_delete.html', {
        'project': project,
        'task': task
    })


@login_required
@require_http_methods(["POST"])
def task_update_status(request, project_id, task_id):
    """Update task status via AJAX"""
    project = get_object_or_404(Project, id=project_id)
    task = get_object_or_404(TodoTask, id=task_id, project=project)
    
    # Check access
    if request.user not in project.members.all():
        return JsonResponse({'error': 'Không có quyền'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in dict(TodoTask.STATUS_CHOICES):
            return JsonResponse({'error': 'Trạng thái không hợp lệ'}, status=400)
        
        old_status = task.status
        task.status = new_status
        task.save()
        
        # Create history entry
        create_task_history_entry(
            task=task,
            user=request.user,
            action='status_changed',
            old_value=old_status,
            new_value=new_status,
            description=f'Trạng thái thay đổi từ "{old_status}" sang "{new_status}"'
        )
        
        return JsonResponse({'success': True, 'new_status': new_status})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# =============================================================================
# ANALYTICS & REPORTS
# =============================================================================

@login_required
def project_analytics(request, project_id):
    """View detailed analytics and reports for project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check access
    if request.user not in project.members.all():
        return HttpResponseForbidden('Bạn không có quyền xem dự án này')
    
    # Get comprehensive statistics
    stats = calculate_project_statistics(project)
    probability = calculate_completion_probability(project)
    velocity = get_task_velocity(project)
    workload = get_member_workload(project)
    health_score = get_project_health_score(project)
    overdue_report = get_overdue_tasks_report(project)
    timeline_data = get_project_timeline_data(project)
    
    return render(request, 'meetings/projects/project_analytics.html', {
        'project': project,
        'stats': stats,
        'probability': probability,
        'velocity': velocity,
        'workload': workload,
        'health_score': health_score,
        'overdue_report': overdue_report,
        'timeline_data': timeline_data,
    })


@login_required
def project_progress_snapshot(request, project_id):
    """Create a progress snapshot and redirect back"""
    project = get_object_or_404(Project, id=project_id)
    
    # Only leader can create snapshots
    if request.user != project.leader:
        return HttpResponseForbidden('Chỉ trưởng nhóm mới có quyền tạo snapshot')
    
    snapshot = create_progress_snapshot(project)
    messages.success(request, 'Đã tạo snapshot tiến độ')
    
    return redirect('project_analytics', project_id=project.id)


# =============================================================================
# MEMBER MANAGEMENT
# =============================================================================

@login_required
def project_members(request, project_id):
    """View and manage project members"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is leader
    if request.user != project.leader:
        return HttpResponseForbidden('Chỉ trưởng nhóm mới có quyền quản lý thành viên')
    
    memberships = ProjectMembership.objects.filter(project=project).select_related('user')
    
    if request.method == 'POST':
        form = MembershipForm(request.POST, project=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã thêm thành viên mới')
            return redirect('project_members', project_id=project.id)
    else:
        form = MembershipForm(project=project)
    
    return render(request, 'meetings/projects/project_members.html', {
        'project': project,
        'memberships': memberships,
        'form': form,
    })


@login_required
def member_remove(request, project_id, membership_id):
    """Remove a member from project"""
    project = get_object_or_404(Project, id=project_id)
    membership = get_object_or_404(ProjectMembership, id=membership_id, project=project)
    
    # Only leader can remove members
    if request.user != project.leader:
        return HttpResponseForbidden('Chỉ trưởng nhóm mới có quyền xóa thành viên')
    
    # Can't remove leader
    if membership.user == project.leader:
        messages.error(request, 'Không thể xóa trưởng nhóm khỏi dự án')
        return redirect('project_members', project_id=project.id)
    
    if request.method == 'POST':
        user_name = membership.user.username
        membership.delete()
        messages.success(request, f'Đã xóa {user_name} khỏi dự án')
        return redirect('project_members', project_id=project.id)
    
    return render(request, 'meetings/projects/member_confirm_remove.html', {
        'project': project,
        'membership': membership
    })


# =============================================================================
# DASHBOARD & MY TASKS
# =============================================================================

@login_required
def my_tasks(request):
    """View all tasks assigned to current user across all projects"""
    tasks = TodoTask.objects.filter(
        assignees=request.user
    ).select_related('project', 'created_by').prefetch_related('tags')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    # Separate by status
    todo_tasks = tasks.filter(status='todo')
    in_progress_tasks = tasks.filter(status='in_progress')
    review_tasks = tasks.filter(status='review')
    completed_tasks = tasks.filter(status='completed')
    
    # Get overdue tasks
    overdue_tasks = tasks.filter(
        status__in=['todo', 'in_progress', 'review'],
        due_date__lt=timezone.now().date()
    )
    
    return render(request, 'meetings/projects/my_tasks.html', {
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'review_tasks': review_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
    })
