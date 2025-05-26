from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Boards(models.Model):
    title = models.CharField(max_length=100)
    member_count = models.IntegerField()
    ticket_count = models.IntegerField()
    tasks_to_do_count = models.IntegerField()
    tasks_high_prio_count = models.IntegerField()
    owner_id = models.IntegerField()

    class Meta:
        verbose_name = 'Board'
        verbose_name_plural = 'Boards'

    def __str__(self):
        return self.title


class BoardUser(models.Model):
    board = models.ForeignKey(Boards, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, blank=True, null=True)
    joined_date = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'BoardUser'
        verbose_name_plural = 'BoardUser'
    
    def __str__(self):
        return f"{self.user.username} ({self.board.title})"


class Task(models.Model):
    board = models.IntegerField()
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=600)
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=50)
    assignee_id = models.IntegerField()
    reviewer = models.IntegerField()
    due_date = models.DateField(null=True, blank=True)
    comments_count = models.IntegerField()

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return self.title
