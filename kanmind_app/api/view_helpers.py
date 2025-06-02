from rest_framework.exceptions import PermissionDenied

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from kanmind_app.models import Board, Task, Comment
from .serializers import BoardCreateSerializer, BoardListSerializer


def get_serializer_class_for_method(method):
    """
    Returns the appropriate serializer class based on the HTTP method.

    Args:
        method (str): The HTTP method of the incoming request (e.g., 'GET', 'POST').

    Returns:
        serializers.ModelSerializer: 
            - BoardCreateSerializer if method is 'POST'
            - BoardListSerializer for all other methods (default: 'GET')
    """
    if method == 'POST':
        return BoardCreateSerializer
    return BoardListSerializer
    
    
def get_annotated_boards_for_user(user):
    """
    Returns queryset of Boards the user owns or is member of,
    annotated with member_count, ticket_count, tasks_to_do_count, tasks_high_prio_count.
    """
    return Board.objects.filter(
        Q(owner=user) | Q(members=user)
    ).distinct().annotate(
        member_count=Count('members', distinct=True),
        ticket_count=Count('tasks', distinct=True),
        tasks_to_do_count=Count('tasks', filter=Q(tasks__status='to-do')),
        tasks_high_prio_count=Count('tasks', filter=Q(tasks__priority='high')),
    )


def create_board_with_annotations(serializer, user):
    """
    Creates a Board using the serializer and sets the owner and members.
    Returns the annotated Board instance.
    """
    board = serializer.save()
    board.members.set(User.objects.filter(
        id__in=[*serializer.validated_data.get('members', []), user.id]))
    annotated_board = get_annotated_boards_for_user(user).filter(id=board.id).first()
    return annotated_board


def get_task_for_user(task_id, user):
    """
    Fetches a task by ID and checks if the user is a member of the associated board.

    Args:
        task_id (int): ID of the task.
        user (User): The current authenticated user.

    Returns:
        Task: The task instance if access is permitted.

    Raises:
        PermissionDenied: If the user is not a member of the board.
    """
    task = get_object_or_404(Task, id=task_id)
    if user != task.board.owner and user not in task.board.members.all():
        raise PermissionDenied("You must be a board member to access these comments.")
    return task


def get_comments_for_task(task):
    """
    Returns a queryset of comments ordered by creation date for a given task.

    Args:
        task (Task): The task to get comments for.

    Returns:
        QuerySet: Ordered comments for the task.
    """
    return Comment.objects.filter(task=task).order_by('created_at')


def create_comment(serializer, task, user):
    """
    Saves a new comment with the given task and author.

    Args:
        serializer (Serializer): The comment serializer with validated data.
        task (Task): The task to attach the comment to.
        user (User): The user creating the comment.

    Returns:
        Comment: The saved comment instance.
    """
    comment = serializer.save(task=task, author=user)
    comment.refresh_from_db()
    return comment
