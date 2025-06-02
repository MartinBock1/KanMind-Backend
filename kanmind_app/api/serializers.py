from rest_framework import serializers
from django.contrib.auth.models import User
from kanmind_app.models import Board, Task


class UserSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source='username')

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']


class TaskSerializer(serializers.ModelSerializer):
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all()
    )
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='assignee', required=False
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='reviewer', required=False
    )

    due_date = serializers.DateField(
        input_formats=['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'],
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'reviewer', 'reviewer_id',
            'due_date'
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee_id', 'assignee',
            'reviewer_id', 'reviewer',
            'due_date'
        ]

    def validate(self, attrs):
        request = self.context['request']
        instance = self.instance
        board = instance.board

        # Nur Mitglieder dürfen bearbeiten
        if request.user not in board.members.all() and request.user != board.owner:
            raise serializers.ValidationError("Du bist kein Mitglied dieses Boards.")

        # Board darf nicht geändert werden
        if 'board' in attrs:
            raise serializers.ValidationError("Die Board-ID darf nicht geändert werden.")

        # Prüfen, ob assignee/reviewer Mitglieder sind
        user_ids = []
        if 'assignee_id' in attrs and attrs['assignee_id']:
            user_ids.append(attrs['assignee_id'])
        if 'reviewer_id' in attrs and attrs['reviewer_id']:
            user_ids.append(attrs['reviewer_id'])

        board_user_ids = list(board.members.values_list('id', flat=True)) + [board.owner_id]
        for uid in user_ids:
            if uid not in board_user_ids:
                raise serializers.ValidationError(
                    f"User mit ID {uid} ist kein Mitglied des Boards.")

        return attrs

    def update(self, instance, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        if assignee_id is not None:
            instance.assignee = User.objects.get(id=assignee_id)

        if reviewer_id is not None:
            instance.reviewer = User.objects.get(id=reviewer_id)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class BoardListSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField()
    ticket_count = serializers.IntegerField()
    tasks_to_do_count = serializers.IntegerField()
    tasks_high_prio_count = serializers.IntegerField()

    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count', 'tasks_to_do_count',
                  'tasks_high_prio_count', 'owner_id']


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
