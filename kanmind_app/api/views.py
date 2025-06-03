from rest_framework.views import APIView
from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from kanmind_app.models import Board, Task, Comment
from .permissions import IsOwnerOrMember, IsBoardMemberOrReadOnly
from .serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    UserSerializer,
    TaskSerializer,
    TaskDetailSerializer,
    CommentSerializer,
)
from .helpers import (
    get_serializer_class_for_method, 
    get_annotated_boards_for_user, 
    create_board_with_annotations,
    get_task_for_user,
    get_comments_for_task,
    create_comment,    
)


class BoardViewSet(viewsets.ModelViewSet):
    """
    A viewset for listing and creating boards.

    - GET (list): Returns a list of boards the current user owns or is a member of,
      with annotation data (e.g., member count, ticket count).
    - POST (create): Creates a new board and automatically includes the requesting user
      as both the owner and a member. Returns the newly created board with annotations.

    Only 'list' and 'create' actions are supported.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Selects the serializer class based on the action:
        - 'create' -> BoardCreateSerializer
        - 'list'   -> BoardListSerializer
        """
        return get_serializer_class_for_method(self.request.method)

    def get_queryset(self):
        """
        Returns the queryset of boards owned by or shared with the current user,
        annotated with:
        - Number of members
        - Number of tickets
        - Number of tasks with status 'to-do'
        - Number of tasks with high priority
        """
        return get_annotated_boards_for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new board.
        - Validates incoming data using BoardCreateSerializer.
        - Adds the current user as owner and member.
        - Returns the created board serialized via BoardListSerializer,
          including all annotations.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        annotated_board = create_board_with_annotations(serializer, request.user)
        output_serializer = BoardListSerializer(annotated_board)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a single board.

    - GET: Retrieve detailed information about a specific board.
    - PUT/PATCH: Update the title or members of the board.
    - DELETE: Delete the board (only allowed for the owner).

    Permissions:
        Only the board owner or a board member can access this view.
        Updates and deletions may be restricted further in the serializer or permission logic.

    Attributes:
        permission_classes (list): List of permission classes required to access the view.
        serializer_class (BoardDetailSerializer): Serializer used for data validation and output.
        queryset (QuerySet): QuerySet used to retrieve the board instance.
        lookup_field (str): Model field used for lookup (primary key here is 'id').
        lookup_url_kwarg (str): URL keyword argument used to pass the board ID.
    """
    permission_classes = [IsOwnerOrMember]
    serializer_class = BoardDetailSerializer
    queryset = Board.objects.all()
    lookup_field = 'id'
    lookup_url_kwarg = 'board_id'


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
    A viewset for listing and creating tasks.

    Actions:
        - list (GET): Returns a list of all tasks in the system.
          Each task includes an annotated `comments_count` field, showing
          the number of related comments. Access is limited to authenticated users.

        - create (POST): Allows creation of a new task. The request must be authenticated.
          You can extend `perform_create()` to add additional logic such as setting
          the task creator.

    Permissions:
        - Access is restricted to authenticated users only.

    Attributes:
        - permission_classes (list): Specifies that only authenticated users can access this view.
        - serializer_class (TaskSerializer): Used for both reading and writing task data.

    Notes:
        - The queryset is dynamically annotated with `comments_count` using Django’s Count aggregation.
        - The `comments_count` is not stored in the database but added at query time.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer
    queryset = Task.objects.none()  # Dummy queryset to avoid DRF registration error

    def get_queryset(self):
        """
        Returns all tasks annotated with the number of associated comments.
        """
        return Task.objects.annotate(
            comments_count=Count('comments')
        )

    def perform_create(self, serializer):
        """
        Called when a new task is created via POST.
        Extend this method to auto-assign the creator or perform other logic.
        """
        serializer.save()


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a single task.

    - GET: Retrieve detailed information about a specific task.
    - PUT/PATCH: Update task fields such as title, status, priority, assignee, etc.
    - DELETE: Delete the task (typically restricted to board members or owners).

    Permissions:
        - Only authenticated users can access this view.
        - Updates and deletions are restricted to board members or the board owner
          via the IsBoardMemberOrReadOnly permission class.

    Attributes:
        permission_classes (list): Permissions required to access or modify the task.
        serializer_class (TaskDetailSerializer): Serializer for validating and returning task details.
        queryset (QuerySet): The set of all Task objects (used for lookup).
        lookup_field (str): The model field used to retrieve the task (here, 'id').
        lookup_url_kwarg (str): The keyword argument from the URL that supplies the task ID.
    """
    permission_classes = [IsAuthenticated, IsBoardMemberOrReadOnly]
    serializer_class = TaskDetailSerializer
    queryset = Task.objects.all()
    lookup_field = 'id'
    lookup_url_kwarg = 'task_id'


class TasksReviewingView(ListAPIView):
    """
    API view to list all tasks where the current user is assigned as the reviewer.

    - GET: Returns a list of tasks the authenticated user is responsible for reviewing.

    Permissions:
        - Only authenticated users can access this view.

    Attributes:
        permission_classes (list): Ensures the user is authenticated.
        serializer_class (TaskSerializer): Serializer used to represent task data.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        Returns a queryset of tasks where the current user is set as the reviewer.

        Returns:
            QuerySet: Tasks filtered by reviewer equal to the current user.
        """
        return Task.objects.filter(reviewer=self.request.user)


class TasksAssignedToMeView(ListAPIView):
    """
    API view to list all tasks assigned to the currently authenticated user.

    - GET: Returns a list of tasks where the current user is set as the assignee.

    Permissions:
        - Only authenticated users can access this view.

    Attributes:
        permission_classes (list): Ensures the user is authenticated.
        serializer_class (TaskSerializer): Serializer used to return task data.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        Returns a queryset of tasks assigned to the current user.

        Returns:
            QuerySet: Tasks where assignee equals the current user.
        """
        return Task.objects.filter(assignee=self.request.user)


class TaskCommentViewSet(viewsets.ModelViewSet):
    """
    A viewset for listing and creating comments on a specific task.

    Access Control:
        Only users who are owners or members of the board associated with the task
        can view or add comments.

    Actions:
        - list (GET): Lists all comments for the specified task, ordered by creation time.
        - create (POST): Adds a new comment to the specified task, linked to the authenticated user.

    Notes:
        The task is identified via the `task_id` URL keyword argument.
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']
    queryset = Comment.objects.none()  # Dummy to satisfy DRF registration

    def get_task(self):
        """
        Retrieves the Task instance and checks if the user is authorized
        (owner or member of the board). Raises PermissionDenied if unauthorized.
        """
        return get_task_for_user(self.kwargs['task_id'], self.request.user)

    def get_queryset(self):
        """
        Returns all comments for the given task, ordered by creation date.
        """
        return get_comments_for_task(self.get_task())

    def perform_create(self, serializer):
        """
        Creates a new comment on the task and associates it with the requesting user.
        """
        task = self.get_task()
        user = self.request.user
        create_comment(serializer, task, user)


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
