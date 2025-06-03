from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BoardViewSet,
    BoardDetailView,
    EmailCheckView,
    TaskViewSet,
    TaskDetailView,
    TasksAssignedToMeView,
    TasksReviewingView,
    TaskCommentViewSet,
    CommentDeleteView,
)

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board-list-create')
router.register(r'tasks', TaskViewSet, basename='task-list')

task_comment = TaskCommentViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

urlpatterns = [
    path('', include(router.urls)),
    # path('boards/', BoardViewSet.as_view(), name='board-list-create'),
    path('boards/<int:board_id>/', BoardDetailView.as_view(), name='board-detail'),
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
    # path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('tasks/assigned_to_me/', TasksAssignedToMeView.as_view(), name='task-assignee'),
    path('tasks/reviewing/', TasksReviewingView.as_view(), name='task-reviewer'),
    # path('tasks/<int:task_id>/comments/', TaskCommentListView.as_view(), name='task-comments'),
    path('tasks/<int:task_id>/comments/', task_comment, name='task-comments'),
    path('tasks/<int:task_id>/comments/<int:comment_id>/',
         CommentDeleteView.as_view(), name='comment-delete'),
]
