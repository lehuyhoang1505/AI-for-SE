"""
Forms for Project Management System
"""
from django import forms
from django.contrib.auth.models import User
from .project_models import Project, TodoTask, TaskTag, TaskComment, ProjectMembership


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects"""
    
    # Add member selection field (multiple users)
    member_emails = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Nhập email thành viên, mỗi email một dòng'
        }),
        required=False,
        label='Email thành viên',
        help_text='Nhập email của các thành viên, mỗi email một dòng'
    )
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'goals', 'status', 'priority',
            'start_date', 'deadline'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If editing existing project, populate member_emails
        if self.instance and self.instance.pk and hasattr(self.instance, 'leader') and self.instance.leader:
            members = self.instance.members.exclude(id=self.instance.leader.id)
            self.fields['member_emails'].initial = '\n'.join(
                member.email for member in members if member.email
            )
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        start_date = self.cleaned_data.get('start_date')
        
        if deadline and start_date and deadline < start_date:
            raise forms.ValidationError('Hạn chót phải sau ngày bắt đầu')
        
        return deadline
    
    def clean_member_emails(self):
        """Validate and parse member emails"""
        emails_text = self.cleaned_data.get('member_emails', '')
        emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        
        # Validate each email
        valid_users = []
        invalid_emails = []
        
        for email in emails:
            try:
                user = User.objects.get(email=email)
                valid_users.append(user)
            except User.DoesNotExist:
                invalid_emails.append(email)
        
        if invalid_emails:
            raise forms.ValidationError(
                f'Không tìm thấy người dùng với email: {", ".join(invalid_emails)}'
            )
        
        return valid_users
    
    def save(self, commit=True):
        project = super().save(commit=False)
        
        # Set leader if creating new project
        # Check _state.adding instead of pk because UUID is assigned immediately
        if project._state.adding and self.user:
            project.leader = self.user
        
        if commit:
            project.save()
            
            # Add members
            member_users = self.cleaned_data.get('member_emails', [])
            
            # Always add leader as a member with 'leader' role
            ProjectMembership.objects.get_or_create(
                project=project,
                user=project.leader,
                defaults={'role': 'leader'}
            )
            
            # Add other members
            for user in member_users:
                if user != project.leader:
                    ProjectMembership.objects.get_or_create(
                        project=project,
                        user=user,
                        defaults={'role': 'member'}
                    )
            
            # Remove members that are no longer in the list
            if not project._state.adding:
                current_member_ids = [user.id for user in member_users] + [project.leader.id]
                ProjectMembership.objects.filter(project=project).exclude(
                    user_id__in=current_member_ids
                ).delete()
        
        return project


class TodoTaskForm(forms.ModelForm):
    """Form for creating and editing tasks"""
    
    assignee_ids = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Người thực hiện'
    )
    
    tag_names = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tags, phân cách bằng dấu phẩy (VD: bug, urgent, frontend)'
        }),
        required=False,
        label='Tags',
        help_text='Nhập các tags, phân cách bằng dấu phẩy'
    )
    
    class Meta:
        model = TodoTask
        fields = [
            'title', 'description', 'status', 'priority', 
            'due_date', 'estimated_hours', 'actual_hours',
            'progress_percentage'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'actual_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'progress_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Limit assignee choices to project members
        if self.project:
            self.fields['assignee_ids'].queryset = self.project.members.all()
        
        # If editing existing task, populate assignees and tags
        # Check _state.adding to ensure the task has been saved to the database
        if self.instance and self.instance.pk and not self.instance._state.adding:
            self.fields['assignee_ids'].initial = self.instance.assignees.all()
            self.fields['tag_names'].initial = ', '.join(
                tag.name for tag in self.instance.tags.all()
            )
    
    def clean_tag_names(self):
        """Parse and validate tag names"""
        tag_text = self.cleaned_data.get('tag_names', '')
        tag_names = [tag.strip().lower() for tag in tag_text.split(',') if tag.strip()]
        return tag_names
    
    def save(self, commit=True):
        task = super().save(commit=False)
        
        if commit:
            task.save()
            
            # Set assignees
            assignees = self.cleaned_data.get('assignee_ids', [])
            task.assignees.set(assignees)
            
            # Create/get tags and assign to task
            tag_names = self.cleaned_data.get('tag_names', [])
            tags = []
            for tag_name in tag_names:
                tag, created = TaskTag.objects.get_or_create(
                    name=tag_name,
                    defaults={'color': '#6c757d'}  # Default gray color
                )
                tags.append(tag)
            task.tags.set(tags)
            
            self.save_m2m()
        
        return task


class TaskCommentForm(forms.ModelForm):
    """Form for adding comments to tasks"""
    
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nhập bình luận...'
            }),
        }


class TaskFilterForm(forms.Form):
    """Form for filtering tasks in project view"""
    
    STATUS_CHOICES = [('', 'Tất cả trạng thái')] + list(TodoTask.STATUS_CHOICES)
    PRIORITY_CHOICES = [('', 'Tất cả ưu tiên')] + list(TodoTask.PRIORITY_CHOICES)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    assignee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label='Tất cả người thực hiện',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tag = forms.ModelChoiceField(
        queryset=TaskTag.objects.all(),
        required=False,
        empty_label='Tất cả tags',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tìm kiếm...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        if project:
            # Limit assignee choices to project members
            self.fields['assignee'].queryset = project.members.all()


class QuickTaskForm(forms.ModelForm):
    """Simplified form for quickly adding tasks"""
    
    class Meta:
        model = TodoTask
        fields = ['title', 'due_date', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên công việc...'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }


class MembershipForm(forms.ModelForm):
    """Form for managing project memberships and roles"""
    
    user_email = forms.EmailField(
        label='Email thành viên',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = ProjectMembership
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
    
    def clean_user_email(self):
        email = self.cleaned_data.get('user_email')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError(f'Không tìm thấy người dùng với email: {email}')
        
        # Check if user is already a member
        if self.project and ProjectMembership.objects.filter(
            project=self.project,
            user=user
        ).exists():
            raise forms.ValidationError('Người dùng này đã là thành viên của dự án')
        
        return user
    
    def save(self, commit=True):
        membership = super().save(commit=False)
        membership.user = self.cleaned_data['user_email']
        membership.project = self.project
        
        if commit:
            membership.save()
        
        return membership
