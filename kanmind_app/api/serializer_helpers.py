from rest_framework import serializers
from kanmind_app.models import User


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
