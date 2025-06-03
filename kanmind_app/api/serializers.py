from rest_framework import serializers
from django.contrib.auth.models import User

from kanmind_app.models import Board, Task, Comment
from .helpers import validate_task_detail, update_task_detail


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.

    Adds a custom field 'fullname' that maps to the user's 'username'.

    Fields:
        id (int): The unique ID of the user.
        email (str): The email address of the user.
        fullname (str): The username of the user, exposed as 'fullname'.
    """
    fullname = serializers.CharField(source='username')

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for the Task model. Handles both serialization and deserialization
    of Task instances for API interactions.

    Fields:
        - board (int): Foreign key to the related Board. Writable.
        - title (str): The title of the task.
        - description (str): A detailed description of the task.
        - status (str): The current status of the task (e.g., "to-do", "in-progress").
        - priority (str): The priority level of the task (e.g., "low", "high").
        - due_date (date): The optional deadline for the task.

        - assignee (UserSerializer): Nested read-only representation of the assigned user.
        - assignee_id (int): Write-only field used to set the assignee by their ID.
        - reviewer (UserSerializer): Nested read-only representation of the reviewer.
        - reviewer_id (int): Write-only field used to set the reviewer by their ID.

        - comments_count (int): Read-only field indicating the number of comments associated
          with this task. This value must be annotated in the view using Count('comments').

    Notes:
        - The 'assignee_id' and 'reviewer_id' fields are mapped to their respective User model
          relations via the `source` keyword and are used for input only.
        - The `comments_count` must be provided via annotation in the queryset, as it's not
          a model field.
    """
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all()
    )
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='assignee', required=False
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='reviewer', required=False
    )
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'reviewer', 'reviewer_id',
            'due_date', 'comments_count',
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed view and update of Task instances.

    Fields:
        - assignee_id: Integer ID for assigning a user to the task (write-only).
        - reviewer_id: Integer ID for assigning a reviewer to the task (write-only).
        - assignee: Nested user representation of the assignee (read-only).
        - reviewer: Nested user representation of the reviewer (read-only).

    Meta:
        Defines the model as Task and lists all included fields.

    Methods:
        - validate(attrs):
            Validates incoming data using external helper function,
            ensuring user permissions and field constraints.

        - update(instance, validated_data):
            Updates a Task instance using external helper function,
            handling related user fields and other attributes.
    """
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee_id', 'assignee',
            'reviewer_id', 'reviewer',
            'due_date'
        ]

    def validate(self, attrs):
        return validate_task_detail(self.instance, attrs, self.context['request'].user)

    def update(self, instance, validated_data):
        return update_task_detail(instance, validated_data)


class BoardListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Board instances with additional aggregated fields.

    Fields:
        - member_count: Number of members in the board.
        - ticket_count: Total number of tickets associated with the board.
        - tasks_to_do_count: Number of tasks with status "to do".
        - tasks_high_prio_count: Number of tasks marked as high priority.
        - owner_id: ID of the owner of the board.

    Meta:
        Defines the model as Board and includes all relevant fields for summary display.
    """
    member_count = serializers.IntegerField()
    ticket_count = serializers.IntegerField()
    tasks_to_do_count = serializers.IntegerField()
    tasks_high_prio_count = serializers.IntegerField()

    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count', 'tasks_to_do_count',
                  'tasks_high_prio_count', 'owner_id']


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed view of a Board instance.

    Fields:
        - members: List of user IDs to set as members (write-only, optional).
        - tasks: Nested list of tasks related to the board (read-only).
        - members_display: Nested representation of the board members as user objects (read-only).

    Meta:
        Specifies the Board model and includes fields for detailed board data including membership
        and tasks.
    """
    members = serializers.ListField(child=serializers.IntegerField(),
                                    write_only=True, required=False)
    tasks = TaskSerializer(many=True)
    members_display = UserSerializer(source='members', many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'members_display', 'tasks']


class BoardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new Board instance.

    Fields:
        - title: The title of the board.
        - members: A list of user IDs to be added as members of the board.

    Meta:
        Specifies the Board model and includes the title and members fields.

    Methods:
        - create(validated_data):
            Creates a new Board with the given title and sets the requesting user as the owner.
            Adds the provided member user IDs, along with the owner, to the board's members.

        - to_representation(instance):
            Returns a serialized representation of the newly created board using
            BoardListSerializer.
    """
    members = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = Board
        fields = ['title', 'members']

    def create(self, validated_data):
        members_ids = validated_data.pop('members')
        request = self.context['request']
        board = Board.objects.create(title=validated_data['title'], owner=request.user)
        board.members.set(User.objects.filter(id__in=members_ids + [request.user.id]))
        return board

    def to_representation(self, instance):
        return BoardListSerializer(instance).data


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model that converts Comment instances
    to JSON and validates input data for creating/updating comments.

    Attributes:
        author (SerializerMethodField): Returns the full name of the author
            if available, otherwise the username. Read-only.
        created_at (DateTimeField): The timestamp when the comment was created,
            formatted as ISO-like string. Read-only.

    Meta:
        model (Comment): The Comment model being serialized.
        fields (list): List of model fields included in serialization.
        read_only_fields (list): Fields that cannot be modified by input.
    """
    author = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['id', 'created_at', 'author']

    def get_author(self, obj):
        if obj.author:
            full_name = obj.author.get_full_name()
            return full_name if full_name else obj.author.username
        return None
