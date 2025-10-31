"""
URL Configuration for Project Management
"""
from django.urls import path
from . import project_views

urlpatterns = [
    # Project CRUD
    path('', project_views.project_list, name='project_list'),
    path('create/', project_views.project_create, name='project_create'),
    path('<uuid:project_id>/', project_views.project_detail, name='project_detail'),
    path('<uuid:project_id>/edit/', project_views.project_edit, name='project_edit'),
    path('<uuid:project_id>/delete/', project_views.project_delete, name='project_delete'),
    
    # Task CRUD
    path('<uuid:project_id>/task/create/', project_views.task_create, name='task_create'),
    path('<uuid:project_id>/task/quick-create/', project_views.task_quick_create, name='task_quick_create'),
    path('<uuid:project_id>/task/<uuid:task_id>/', project_views.task_detail, name='task_detail'),
    path('<uuid:project_id>/task/<uuid:task_id>/edit/', project_views.task_edit, name='task_edit'),
    path('<uuid:project_id>/task/<uuid:task_id>/delete/', project_views.task_delete, name='task_delete'),
    path('<uuid:project_id>/task/<uuid:task_id>/update-status/', project_views.task_update_status, name='task_update_status'),
    
    # Analytics & Reports
    path('<uuid:project_id>/analytics/', project_views.project_analytics, name='project_analytics'),
    path('<uuid:project_id>/snapshot/', project_views.project_progress_snapshot, name='project_progress_snapshot'),
    
    # Member Management
    path('<uuid:project_id>/members/', project_views.project_members, name='project_members'),
    path('<uuid:project_id>/members/<uuid:membership_id>/remove/', project_views.member_remove, name='member_remove'),
    
    # My Tasks (across all projects)
    path('my-tasks/', project_views.my_tasks, name='my_tasks'),
]
