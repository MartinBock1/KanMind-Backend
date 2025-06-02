from rest_framework.views import APIView
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound

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


class BoardListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BoardCreateSerializer
        return BoardListSerializer

    def get_queryset(self):
        return Board.objects.filter(
            Q(owner=self.request.user) |
            Q(members=self.request.user)
        ).distinct().annotate(
            member_count=Count('members', distinct=True),
            ticket_count=Count('tasks', distinct=True),
            tasks_to_do_count=Count('tasks', filter=Q(tasks__status='to-do')),
            tasks_high_prio_count=Count('tasks', filter=Q(tasks__priority='high')),
        )

    def create(self, request, *args, **kwargs):
        # Eingabedaten validieren und speichern
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        board = serializer.save()

        # Annotierte Version des erstellten Boards laden
        annotated_board = (
            Board.objects.filter(id=board.id)
            .annotate(
                member_count=Count('members', distinct=True),
                ticket_count=Count('tasks', distinct=True),
                tasks_to_do_count=Count('tasks', filter=Q(tasks__status='to-do')),
                tasks_high_prio_count=Count('tasks', filter=Q(tasks__priority='high')),
            )
            .first()
        )

        # Mit dem List-Serializer serialisieren und zurückgeben
        output_serializer = BoardListSerializer(annotated_board)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOrMember]
    serializer_class = BoardDetailSerializer
    queryset = Board.objects.all()
    lookup_field = 'id'   # Das Board wird anhand der 'id' im URL-Pfad abgerufen
    lookup_url_kwarg = 'board_id'   # Der URL-Param. für die Board-ID wird als 'board_id' erwartet


class EmailCheckView(APIView):

    def get(self, request):
        email = request.query_params.get('email')

        # Zusätzliche Fehlerprüfung:
        # Überprüfe, ob die E-Mail-Adresse überhaupt im Query-Parameter vorhanden ist
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


class TaskListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    class Meta:
        model = Task
        fields = '__all__'
    
    def perform_create(self, serializer):
        serializer.save()


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsBoardMemberOrReadOnly]
    serializer_class = TaskDetailSerializer
    queryset = Task.objects.all()
    lookup_field = 'id'   # Das Board wird anhand der 'id' im URL-Pfad abgerufen
    lookup_url_kwarg = 'task_id'   # Der URL-Param. für die Board-ID wird als 'board_id' erwartet


class TasksReviewingView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)


class TasksAssignedToMeView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class TaskCommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_task(self):
        task_id = self.kwargs['task_id']
        task = get_object_or_404(Task, id=task_id)
        # Prüfen, ob der Benutzer Mitglied des Boards ist
        user = self.request.user
        if user != task.board.owner and user not in task.board.members.all():
            raise PermissionDenied("You must be a board member to access these comments.")
        return task

    def get_queryset(self):
        task = self.get_task()
        return Comment.objects.filter(task=task).order_by('created_at')

    def perform_create(self, serializer):
        task = self.get_task()
        serializer.save(task=task, author=self.request.user)


class CommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, task_id, comment_id):
        # Task und Kommentar laden oder 404 zurückgeben
        task = get_object_or_404(Task, id=task_id)
        comment = get_object_or_404(Comment, id=comment_id, task=task)

        # Prüfen, ob der anfragende User der Ersteller des Kommentars ist
        if comment.author != request.user:
            return Response({"detail": "Nur der Ersteller darf den Kommentar löschen."},
                            status=status.HTTP_403_FORBIDDEN)

        # Kommentar löschen
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
