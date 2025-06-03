from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from kanmind_app.models import Board, Task, Comment


def check_user_membership(user, board):
    """
    Checks if the user is a member or owner of the board.
    Raises ValidationError if not.
    """
    if user not in board.members.all() and user != board.owner:
        raise serializers.ValidationError("Du bist kein Mitglied dieses Boards.")


def validate_user_ids_on_board(user_ids, board):
    """
    Validates that all user_ids belong to members or owner of the board.
    Raises ValidationError if any user is not a member.
    """
    board_user_ids = list(board.members.values_list('id', flat=True)) + [board.owner_id]
    for uid in user_ids:
        if uid not in board_user_ids:
            raise serializers.ValidationError(f"User mit ID {uid} ist kein Mitglied des Boards.")


def extract_user_ids(attrs):
    """
    Extracts assignee_id and reviewer_id from attrs if present and not None.
    Returns a list of these IDs.
    """
    user_ids = []
    if 'assignee_id' in attrs and attrs['assignee_id']:
        user_ids.append(attrs['assignee_id'])
    if 'reviewer_id' in attrs and attrs['reviewer_id']:
        user_ids.append(attrs['reviewer_id'])
    return user_ids


def update_task_assignee_and_reviewer(instance, assignee_id, reviewer_id):
    """
    Updates the assignee and reviewer fields on the Task instance.
    """
    if assignee_id is not None:
        instance.assignee = User.objects.get(id=assignee_id)
    if reviewer_id is not None:
        instance.reviewer = User.objects.get(id=reviewer_id)


def validate_task_detail(instance, attrs, user):
    """
    Validates the task update data.

    Checks:
    - The user performing the update is a member or owner of the task's board.
    - The board ID is not being changed in the update data.
    - The assignee_id and reviewer_id (if provided) belong to members of the board.

    Args:
        instance: The Task instance being updated.
        attrs: The dictionary of attributes to validate.
        user: The user performing the update request.

    Raises:
        serializers.ValidationError: If validation fails for any check.

    Returns:
        The validated attrs dictionary.
    """
    board = instance.board

    if user not in board.members.all() and user != board.owner:
        raise serializers.ValidationError("You are not a member of this board.")

    if 'board' in attrs:
        raise serializers.ValidationError("The board ID must not be changed.")

    user_ids = []
    if 'assignee_id' in attrs and attrs['assignee_id']:
        user_ids.append(attrs['assignee_id'])
    if 'reviewer_id' in attrs and attrs['reviewer_id']:
        user_ids.append(attrs['reviewer_id'])

    board_user_ids = list(board.members.values_list('id', flat=True)) + [board.owner_id]
    for uid in user_ids:
        if uid not in board_user_ids:
            raise serializers.ValidationError(
                f"User with ID {uid} is not a member of the board."
            )

    return attrs


def update_task_detail(instance, validated_data):
    """
    Updates the Task instance with validated data, including related user fields.

    Extracts 'assignee_id' and 'reviewer_id' from the validated data and updates
    the corresponding User foreign key relationships on the Task instance.
    Then updates all other provided fields on the instance.

    Args:
        instance: The Task instance to update.
        validated_data: A dictionary of validated data from the serializer.

    Returns:
        The updated Task instance.
    """
    assignee_id = validated_data.pop('assignee_id', None)
    reviewer_id = validated_data.pop('reviewer_id', None)

    if assignee_id is not None:
        instance.assignee = User.objects.get(id=assignee_id)
    if reviewer_id is not None:
        instance.reviewer = User.objects.get(id=reviewer_id)

    for attr, value in validated_data.items():
        setattr(instance, attr, value)

    instance.save()
    return instance


def get_serializer_class_for_method(method):
    """
    Returns the appropriate serializer class based on the HTTP method.

    This function imports the serializer classes inside the function
    to avoid circular import issues.

    Args:
        method (str): The HTTP method (e.g., 'GET', 'POST').

    Returns:
        serializers.ModelSerializer:
            - BoardCreateSerializer if method is 'POST'
            - BoardListSerializer otherwise
    """
    from .serializers import BoardCreateSerializer, BoardListSerializer
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
