"""
Utility functions for Project Management
Handles progress calculations, analytics, and predictions
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q, Avg
from .project_models import Project, TodoTask, TaskHistory, ProjectProgress


def calculate_project_statistics(project):
    """
    Calculate comprehensive statistics for a project
    Returns a dictionary with various metrics
    """
    tasks = project.tasks.all()
    
    stats = {
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status='completed').count(),
        'in_progress_tasks': tasks.filter(status='in_progress').count(),
        'todo_tasks': tasks.filter(status='todo').count(),
        'review_tasks': tasks.filter(status='review').count(),
        'overdue_tasks': tasks.filter(
            status__in=['todo', 'in_progress', 'review'],
            due_date__lt=timezone.now().date()
        ).count(),
        'soon_overdue_tasks': tasks.filter(
            status__in=['todo', 'in_progress', 'review'],
            due_date__gte=timezone.now().date(),
            due_date__lte=timezone.now().date() + timedelta(days=3)
        ).count(),
        'completion_rate': project.completion_percentage,
    }
    
    # Calculate priority distribution
    stats['priority_dist'] = {
        'urgent': tasks.filter(priority='urgent').count(),
        'high': tasks.filter(priority='high').count(),
        'medium': tasks.filter(priority='medium').count(),
        'low': tasks.filter(priority='low').count(),
    }
    
    # Calculate average task completion time
    completed_tasks = tasks.filter(status='completed', completed_at__isnull=False)
    if completed_tasks.exists():
        total_time = sum([
            (task.completed_at.date() - task.created_at.date()).days
            for task in completed_tasks
        ])
        stats['avg_completion_days'] = total_time / completed_tasks.count()
    else:
        stats['avg_completion_days'] = 0
    
    # Calculate time utilization (actual vs estimated)
    tasks_with_hours = tasks.filter(
        estimated_hours__isnull=False,
        actual_hours__isnull=False
    )
    if tasks_with_hours.exists():
        total_estimated = sum([float(task.estimated_hours) for task in tasks_with_hours])
        total_actual = sum([float(task.actual_hours) for task in tasks_with_hours])
        if total_estimated > 0:
            stats['time_accuracy'] = (total_actual / total_estimated) * 100
        else:
            stats['time_accuracy'] = 0
    else:
        stats['time_accuracy'] = 0
    
    return stats


def calculate_completion_probability(project):
    """
    Calculate probability of completing project on time
    Based on current velocity and remaining work
    """
    # Get current metrics
    total_tasks = project.total_tasks
    completed_tasks = project.completed_tasks
    remaining_tasks = total_tasks - completed_tasks
    
    if total_tasks == 0:
        return 100  # No tasks = 100% complete
    
    if remaining_tasks == 0:
        return 100  # All tasks done = 100% complete
    
    # Calculate days elapsed and remaining
    days_elapsed = (timezone.now().date() - project.start_date).days
    days_remaining = (project.deadline - timezone.now().date()).days
    
    if days_remaining <= 0:
        return 0  # Past deadline
    
    if days_elapsed <= 0:
        return 50  # Haven't started yet, neutral probability
    
    # Calculate velocity (tasks per day)
    velocity = completed_tasks / days_elapsed if days_elapsed > 0 else 0
    
    # Calculate required velocity to finish on time
    required_velocity = remaining_tasks / days_remaining if days_remaining > 0 else float('inf')
    
    # Calculate probability based on velocity ratio
    if required_velocity == 0:
        probability = 100
    elif velocity == 0:
        probability = 10  # No progress made, low probability
    else:
        velocity_ratio = velocity / required_velocity
        # Use sigmoid-like function to map ratio to probability
        if velocity_ratio >= 1.5:
            probability = 95
        elif velocity_ratio >= 1.2:
            probability = 85
        elif velocity_ratio >= 1.0:
            probability = 70
        elif velocity_ratio >= 0.8:
            probability = 50
        elif velocity_ratio >= 0.6:
            probability = 30
        else:
            probability = 15
    
    # Adjust based on overdue tasks
    overdue_tasks = project.overdue_tasks
    if overdue_tasks > 0:
        overdue_penalty = min(30, overdue_tasks * 5)  # Max 30% penalty
        probability = max(5, probability - overdue_penalty)
    
    return int(probability)


def get_task_velocity(project, days=7):
    """
    Calculate task completion velocity (tasks completed per day)
    over the last N days
    """
    since_date = timezone.now() - timedelta(days=days)
    
    completed_in_period = project.tasks.filter(
        status='completed',
        completed_at__gte=since_date
    ).count()
    
    velocity = completed_in_period / days if days > 0 else 0
    return round(velocity, 2)


def get_member_workload(project):
    """
    Calculate workload for each member in the project
    Returns list of dicts with member info and task counts
    """
    workload = []
    
    for member in project.members.all():
        assigned_tasks = TodoTask.objects.filter(
            project=project,
            assignees=member
        )
        
        member_data = {
            'user': member,
            'total': assigned_tasks.count(),
            'todo': assigned_tasks.filter(status='todo').count(),
            'in_progress': assigned_tasks.filter(status='in_progress').count(),
            'review': assigned_tasks.filter(status='review').count(),
            'completed': assigned_tasks.filter(status='completed').count(),
            'overdue': assigned_tasks.filter(
                status__in=['todo', 'in_progress', 'review'],
                due_date__lt=timezone.now().date()
            ).count(),
        }
        
        workload.append(member_data)
    
    # Sort by total tasks (descending)
    workload.sort(key=lambda x: x['total'], reverse=True)
    
    return workload


def create_progress_snapshot(project):
    """
    Create a snapshot of current project progress
    Used for historical tracking and analytics
    """
    # Calculate tasks completed in last week
    last_week = timezone.now() - timedelta(days=7)
    tasks_completed_last_week = project.tasks.filter(
        status='completed',
        completed_at__gte=last_week
    ).count()
    
    snapshot = ProjectProgress.objects.create(
        project=project,
        total_tasks=project.total_tasks,
        completed_tasks=project.completed_tasks,
        overdue_tasks=project.overdue_tasks,
        completion_percentage=project.completion_percentage,
        tasks_completed_last_week=tasks_completed_last_week
    )
    
    return snapshot


def get_project_timeline_data(project):
    """
    Get timeline data for burndown chart
    Returns list of dates and completion percentages
    """
    snapshots = project.progress_snapshots.order_by('snapshot_date')
    
    timeline = []
    for snapshot in snapshots:
        timeline.append({
            'date': snapshot.snapshot_date.date(),
            'completion': snapshot.completion_percentage,
            'total_tasks': snapshot.total_tasks,
            'completed_tasks': snapshot.completed_tasks,
        })
    
    # Add current state if not already in snapshots
    if not timeline or timeline[-1]['date'] != timezone.now().date():
        timeline.append({
            'date': timezone.now().date(),
            'completion': project.completion_percentage,
            'total_tasks': project.total_tasks,
            'completed_tasks': project.completed_tasks,
        })
    
    return timeline


def get_recommended_tasks(user, project):
    """
    Get recommended tasks for a user based on:
    - Priority
    - Deadline proximity
    - Current workload
    - Task dependencies (if implemented)
    """
    # Get tasks assigned to user that are not completed
    available_tasks = TodoTask.objects.filter(
        project=project,
        assignees=user,
        status__in=['todo', 'in_progress']
    )
    
    # Score each task
    scored_tasks = []
    for task in available_tasks:
        score = 0
        
        # Priority weight
        priority_scores = {'urgent': 40, 'high': 30, 'medium': 20, 'low': 10}
        score += priority_scores.get(task.priority, 0)
        
        # Deadline proximity weight
        days_until_due = task.days_remaining
        if days_until_due < 0:
            score += 50  # Overdue gets highest weight
        elif days_until_due <= 1:
            score += 45
        elif days_until_due <= 3:
            score += 35
        elif days_until_due <= 7:
            score += 25
        else:
            score += 10
        
        # Status weight (in_progress over todo)
        if task.status == 'in_progress':
            score += 15
        
        scored_tasks.append({
            'task': task,
            'score': score
        })
    
    # Sort by score (descending)
    scored_tasks.sort(key=lambda x: x['score'], reverse=True)
    
    return [item['task'] for item in scored_tasks[:5]]


def create_task_history_entry(task, user, action, old_value='', new_value='', description=''):
    """
    Create a history entry for task changes
    """
    from .project_models import TaskHistory
    
    history = TaskHistory.objects.create(
        task=task,
        user=user,
        action=action,
        old_value=old_value,
        new_value=new_value,
        description=description
    )
    
    return history


def get_overdue_tasks_report(project):
    """
    Generate a report of overdue tasks with details
    """
    overdue_tasks = project.tasks.filter(
        status__in=['todo', 'in_progress', 'review'],
        due_date__lt=timezone.now().date()
    ).select_related('created_by').prefetch_related('assignees')
    
    report = []
    for task in overdue_tasks:
        days_overdue = (timezone.now().date() - task.due_date).days
        report.append({
            'task': task,
            'days_overdue': days_overdue,
            'assignees': list(task.assignees.all()),
        })
    
    # Sort by days overdue (descending)
    report.sort(key=lambda x: x['days_overdue'], reverse=True)
    
    return report


def filter_tasks(project, filters):
    """
    Filter tasks based on provided criteria
    
    filters: dict with keys like 'status', 'priority', 'assignee', 'tag', 'search'
    """
    tasks = project.tasks.all()
    
    if filters.get('status'):
        tasks = tasks.filter(status=filters['status'])
    
    if filters.get('priority'):
        tasks = tasks.filter(priority=filters['priority'])
    
    if filters.get('assignee'):
        tasks = tasks.filter(assignees=filters['assignee'])
    
    if filters.get('tag'):
        tasks = tasks.filter(tags=filters['tag'])
    
    if filters.get('search'):
        search_term = filters['search']
        tasks = tasks.filter(
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term)
        )
    
    return tasks


def get_project_health_score(project):
    """
    Calculate overall project health score (0-100)
    Based on multiple factors:
    - Completion rate
    - Overdue tasks
    - Velocity
    - Time remaining
    """
    score = 0
    
    # Completion rate (30 points)
    score += int(project.completion_percentage * 0.3)
    
    # Overdue tasks penalty (up to -30 points)
    overdue_ratio = project.overdue_tasks / project.total_tasks if project.total_tasks > 0 else 0
    score -= int(overdue_ratio * 30)
    
    # Days remaining factor (20 points)
    days_remaining = project.days_remaining
    total_days = (project.deadline - project.start_date).days
    if total_days > 0:
        time_progress = ((total_days - days_remaining) / total_days) * 100
        # Compare time progress with completion percentage
        if time_progress <= project.completion_percentage:
            score += 20  # On track or ahead
        else:
            score += max(0, 20 - int((time_progress - project.completion_percentage) / 5))
    
    # Velocity factor (20 points)
    velocity = get_task_velocity(project)
    if velocity > 0:
        score += min(20, int(velocity * 10))
    
    # Ensure score is between 0 and 100
    score = max(0, min(100, score))
    
    return score
