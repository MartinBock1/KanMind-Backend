from rest_framework import serializers

from kanmind_app.models import Boards, BoardUser, Task


class BoardsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Boards
        fields = ["id", "title", "member_count", "ticket_count",
                  "tasks_to_do_count", "tasks_high_prio_count", "owner_id"]


class BoardUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardUser
        fields = ['board', 'user', 'role', 'joined_date']


class TaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Boards
        fields = ["board", "title", "description", "status",
                  "priority", "assignee_id", "reviewer", "due_date", "comments_count"]
