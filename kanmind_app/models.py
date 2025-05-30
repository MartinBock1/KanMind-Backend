from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Board(models.Model):
    """
    Repräsentiert ein Projekt-Board, auf dem Aufgaben (Tasks) organisiert werden.

    Attribute:
        title (str): Der Titel des Boards.
        owner (User): Der Benutzer, der das Board erstellt hat und als Eigentümer gilt.
        members (ManyToMany[User]): Die Benutzer, die Mitglieder dieses Boards sind.
    """
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_boards')
    members = models.ManyToManyField(User, related_name='boards')

    def __str__(self):
        return self.title


class Task(models.Model):
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
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='assigned_tasks')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    blank=True, related_name='reviewed_tasks')
    due_date = models.DateField(null=True, blank=True)
    comments_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title
