from django.urls import path
from .views import (
    BoardListCreateView,
    BoardDetailView,
    EmailCheckView,
    TaskListView
)

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:board_id>/', BoardDetailView.as_view(), name='board-detail'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
    path('tasks/', TaskListView.as_view(), name='task-list'),
]
