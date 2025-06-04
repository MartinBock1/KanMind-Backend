from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    BoardViewSet,
    EmailCheckView,
    TaskViewSet,    
    TaskCommentListView,
    CommentDeleteView,
)

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('email-check/', EmailCheckView.as_view(), name='email-check'),
    path('tasks/<int:task_id>/comments/', TaskCommentListView.as_view(), name='task-comments'),
    path('tasks/<int:task_id>/comments/<int:comment_id>/',
         CommentDeleteView.as_view(), name='comment-delete'),
]

urlpatterns += router.urls
