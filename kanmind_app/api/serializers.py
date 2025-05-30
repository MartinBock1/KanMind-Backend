from rest_framework import serializers
from django.contrib.auth.models import User
from kanmind_app.models import Board, Task


class UserSerializer(serializers.ModelSerializer):    
    fullname = serializers.CharField(source='username')

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority',
                  'assignee', 'reviewer', 'due_date', 'comments_count']


class BoardListSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField()
    ticket_count = serializers.IntegerField()
    tasks_to_do_count = serializers.IntegerField()
    tasks_high_prio_count = serializers.IntegerField()

    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count',
                  'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id']


class BoardDetailSerializer(serializers.ModelSerializer):
    members = serializers.ListField(child=serializers.IntegerField(),
                                    write_only=True, required=False)
    tasks = TaskSerializer(many=True)
    members_display = UserSerializer(source='members', many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'members_display', 'tasks']


class BoardCreateSerializer(serializers.ModelSerializer):
    members = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = Board
        fields = ['title', 'members']

    def create(self, validated_data):
        members_ids = validated_data.pop('members')
        request = self.context['request']
        board = Board.objects.create(title=validated_data['title'], owner=request.user)
        board.members.set(User.objects.filter(id__in=members_ids + [request.user.id]))
        return board

    def to_representation(self, instance):
        # Nutze den ListSerializer zur Ausgabe
        return BoardListSerializer(instance).data
