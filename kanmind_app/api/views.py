from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.models import User
from django.db.models import Count, Q
from kanmind_app.models import Board, Task
from .permissions import IsOwnerOrMember
from .serializers import (
    BoardListSerializer,
    BoardDetailSerializer,
    BoardCreateSerializer,
    UserSerializer,
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

    def perform_create(self, serializer):
        serializer.save()


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
