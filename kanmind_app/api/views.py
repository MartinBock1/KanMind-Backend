from rest_framework import viewsets
from kanmind_app.models import Boards, Task
from .serializers import (
    BoardsSerializer,
    TaskSerializer,
)

class BoardsViewSet(viewsets.ModelViewSet):
    queryset = Boards.objects.all()
    serializer_class = BoardsSerializer
    

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
