from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Board(models.Model):
    """
    Represents a project board where tasks are organized.

    Attributes:
        title (str): The title of the board.
        owner (User): The user who created and owns the board.
        members (ManyToMany[User]): Users who are members of the board.
    """
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_boards')
    members = models.ManyToManyField(User, related_name='boards')
    
    class Meta:
        verbose_name = 'Board'
        verbose_name_plural = 'Boards'
        ordering = ['id']

    def __str__(self):
        return self.title


class Task(models.Model):
    """
    Represents a task within a board.

    Attributes:
        board (Board): The board to which this task belongs.
        title (str): The title of the task.
        description (str): Detailed description of the task.
        status (str): The current status of the task (e.g., to-do, in-progress, etc.).
        priority (str): The priority level of the task (low, medium, high).
        assignee (User): The user assigned to the task.
        reviewer (User): The user responsible for reviewing the task.
        due_date (date): The deadline for the task.
    """
    STATUS_CHOICES = [
        ('to-do', 'To Do'),
        ('in-progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to-do')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assigned_tasks')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='reviewed_tasks')
    due_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['id']

    def __str__(self):
        return self.title


class Comment(models.Model):
    """
    Represents a comment made on a task.

    Attributes:
        task (Task): The task to which the comment belongs.
        author (User): The user who wrote the comment.
        content (str): The content of the comment.
        created_at (datetime): Timestamp when the comment was created.
    """
    task = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['created_at']
