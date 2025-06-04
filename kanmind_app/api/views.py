from rest_framework.views import APIView
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from kanmind_app.models import Board, Task, Comment
from .permissions import IsOwnerOrMember, IsBoardMemberOrReadOnly
from .serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    BoardCreateSerializer,
    UserSerializer,
    TaskSerializer,
    TaskDetailSerializer,
    CommentSerializer,
)
from .helpers import (
    get_annotated_boards_for_user,
    create_board_with_members_and_annotations,
    update_task_with_permission_check,
    get_task_for_user,
    get_tasks_for_reviewer,
    get_tasks_assigned_to_user,
    get_comments_for_task,
    create_comment,
)


class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Board objects.

    Supports the following actions:
    - list: Returns all boards the user owns or is a member of, with annotations.
    - retrieve: Returns detailed information about a specific board.
    - create: Creates a new board and automatically adds the creator as owner and member.
    - update/partial_update/destroy: Available only to board owners or members (permissions enforced).

    Uses different serializers per action to optimize data representation.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns the appropriate queryset depending on the action:
        - list: Boards related to the user (owned or as a member), annotated with metadata.
        - other actions: All boards.
        """
        if self.action == 'list':
            return get_annotated_boards_for_user(self.request.user)
        return Board.objects.all()

    def get_serializer_class(self):
        """
        Chooses the appropriate serializer class based on the current action:
        - list: Uses BoardListSerializer
        - retrieve: Uses BoardDetailSerializer
        - create: Uses BoardCreateSerializer
        - fallback/default: BoardDetailSerializer
        """
        if self.action == 'list':
            return BoardListSerializer
        elif self.action == 'retrieve':
            return BoardDetailSerializer
        elif self.action == 'create':
            return BoardCreateSerializer
        return BoardDetailSerializer

    def perform_create(self, serializer):
        """
        Internal method to save the board with the current user as owner.
        The actual creation logic including member assignment and annotation
        is handled in the custom create method.
        """
        self.board = serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new board.

        - Validates the incoming data.
        - Assigns the current user as owner and member.
        - Returns the created board with annotations using BoardListSerializer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = create_board_with_members_and_annotations(serializer, request.user)
        output_serializer = BoardListSerializer(board)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def get_permissions(self):
        """
        Applies object-level permission checks for retrieve, update, partial_update, and destroy.
        For other actions, only authentication is required.
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrMember()]
        return super().get_permissions()


class EmailCheckView(APIView):
    """
    API view to check if a user with a given email exists.

    This view accepts a GET request with an 'email' query parameter
    and returns the serialized user data if the user is found.

    - If no email parameter is provided, returns a 400 error.
    - If no user with the given email exists, returns a 404 error.
    - If a user is found, returns the user data as serialized JSON.

    Example request:
        GET /api/users/check-email/?email=test@example.com
    """

    def get(self, request):
        """
        Handles GET requests to check for a user by email.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            Response: JSON response containing either user data,
                      an error for missing email,
                      or an error if no matching user is found.
        """
        email = request.query_params.get('email')

        if not email:
            return Response({"error": "Email parameter is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"error": "User with this email not found."},
                            status=status.HTTP_404_NOT_FOUND)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Task objects.

    Supports the following actions:
    - list: Lists all tasks with an annotated comments count.
    - retrieve: Returns detailed information for a specific task.
    - create: Creates a new task (default serializer used).
    - update/partial_update: Updates a task with permission checks.
    - destroy: Deletes a task.
    
    Additional custom actions:
    - reviewing: Lists tasks where the current user is the reviewer.
    - assigned_to_me: Lists tasks assigned to the current user.

    Permissions:
    - Requires authentication for all actions.
    - Write access limited to board members or owners (IsBoardMemberOrReadOnly).
    """
    permission_classes = [IsAuthenticated, IsBoardMemberOrReadOnly]

    def get_queryset(self):
        """
        Returns a queryset of all tasks annotated with the count of related comments.
        """
        return Task.objects.annotate(comments_count=Count('comments'))

    def get_serializer_class(self):
        """
        Selects serializer class based on the action:
        - For retrieve, update, partial_update, and destroy: TaskDetailSerializer.
        - For list and create: TaskSerializer.
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return TaskDetailSerializer
        return TaskSerializer

    def perform_update(self, serializer):
        """
        Overrides update behavior to validate and update the task instance
        with permission checks before saving.
        """
        instance = self.get_object()
        update_task_with_permission_check(instance, serializer.validated_data, self.request.user)

    @action(detail=False, methods=['get'], url_path='reviewing')
    def reviewing(self, request):
        """
        Custom action to list all tasks for which the current user is the reviewer.
        Supports pagination.
        """
        tasks = get_tasks_for_reviewer(request.user)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='assigned_to_me')
    def assigned_to_me(self, request):
        """
        Custom action to list all tasks assigned to the current user.
        Supports pagination.
        """
        tasks = get_tasks_assigned_to_user(request.user)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class TaskCommentListView(generics.ListCreateAPIView):
    """
    API view to list or create comments on a specific task.

    Only users who are members or owners of the board associated with the task
    are allowed to access or create comments via this endpoint.

    Methods:
        get_task:
            Retrieves the Task instance by ID and verifies the requesting user's
            membership or ownership on the related board. Raises PermissionDenied
            if the user is unauthorized.

        get_queryset:
            Returns all comments related to the task, ordered by creation date.

        perform_create:
            Creates a new comment associated with the task and the authenticated user.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        return get_task_for_user(self.kwargs['task_id'], self.request.user)

    def get_queryset(self):
        return get_comments_for_task(self.get_task())

    def perform_create(self, serializer):
        task = self.get_task()
        user = self.request.user
        comment = create_comment(serializer, task, user)


class CommentDeleteView(APIView):
    """
    API view for deleting a specific comment on a task.

    - DELETE: Deletes the specified comment if the requesting user is the author.

    Permissions:
        - Only authenticated users can access this view.
        - Only the comment's author is allowed to delete it.

    URL Parameters:
        - task_id (int): ID of the task the comment belongs to.
        - comment_id (int): ID of the comment to be deleted.

    Responses:
        - 204 NO CONTENT: Comment was successfully deleted.
        - 403 FORBIDDEN: User is not the author of the comment.
        - 404 NOT FOUND: Task or comment does not exist or is mismatched.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, task_id, comment_id):
        """
        Deletes a comment if the requesting user is the comment's author.

        Args:
            request (Request): The incoming HTTP request.
            task_id (int): ID of the task to which the comment belongs.
            comment_id (int): ID of the comment to delete.

        Returns:
            Response: 204 on success, 403 if not author, or 404 if not found.
        """
        task = get_object_or_404(Task, id=task_id)
        comment = get_object_or_404(Comment, id=comment_id, task=task)

        if comment.author != request.user:
            return Response({"detail": "Only the creator may delete the comment."},
                            status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
