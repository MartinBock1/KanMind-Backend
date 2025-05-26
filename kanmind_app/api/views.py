from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated

from kanmind_app.models import (
    Boards,
    BoardUser,
    Task
)
from .serializers import (
    BoardsSerializer,
    BoardUserSerializer,
    TaskSerializer,
)
# from .permissions import IsOwnerOrAdmin, IsStaffOrReadOnly


class BoardsViewSet(viewsets.ModelViewSet):
    queryset = Boards.objects.all()
    serializer_class = BoardsSerializer
    permission_classes = [IsAuthenticated]


class BoardUserList(generics.ListCreateAPIView):
    queryset = BoardUser.objects.all()
    serializer_class = BoardUserSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
