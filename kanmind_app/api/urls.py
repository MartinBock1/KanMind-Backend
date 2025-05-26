from django.urls import path, include
from rest_framework import routers

from .views import BoardsViewSet, TaskViewSet

router = routers.SimpleRouter()
router.register(r'boards', BoardsViewSet)
router.register(r'task', TaskViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
